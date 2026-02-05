"""
Tests for indexer data structures functionality.

This validates T:0010 acceptance criteria.
"""

from indexer import DocumentIndex, SearchMatch, IndexStatistics, IndexError, create_index
from doc_element import DocElement, Kind, File, Status


def create_test_element(element_id: str, title: str, kind: Kind, file: File,
                       refs: list = None, status: Status = None) -> DocElement:
    """Helper to create test DocElement."""
    return DocElement(
        id=element_id,
        kind=kind,
        title=title,
        file=file,
        heading_level=2,
        anchor=title.lower().replace(' ', '-'),
        body_markdown=f"Body content for {title}",
        refs=refs or [],
        backlinks=[],
        status=status
    )


def test_index_initialization():
    """Test DocumentIndex initialization."""
    index = DocumentIndex()

    assert index.get_element_count() == 0
    assert index.get_reference_count() == 0
    assert len(index.get_all_elements()) == 0

    stats = index.get_statistics()
    assert stats.total_elements == 0
    assert stats.total_references == 0


def test_add_remove_elements():
    """Test adding and removing elements from index."""
    index = DocumentIndex()

    # Create test element
    element = create_test_element(
        "R:Purpose", "System Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN
    )

    # Add element
    index.add_element(element)
    assert index.get_element_count() == 1
    assert index.has_element("R:Purpose")

    # Retrieve element
    retrieved = index.get_element("R:Purpose")
    assert retrieved is not None
    assert retrieved.id == "R:Purpose"
    assert retrieved.title == "System Purpose"

    # Remove element
    removed = index.remove_element("R:Purpose")
    assert removed is True
    assert index.get_element_count() == 0
    assert not index.has_element("R:Purpose")

    # Try to remove non-existent element
    removed = index.remove_element("NonExistent")
    assert removed is False


def test_o1_id_lookup():
    """Test O(1) ID lookup performance requirement."""
    index = DocumentIndex()

    # Add many elements
    elements = [
        create_test_element(f"R:{i:04d}", f"Requirement {i}", Kind.REQUIREMENT, File.SOFTWARE_DESIGN)
        for i in range(1000)
    ]

    for element in elements:
        index.add_element(element)

    assert index.get_element_count() == 1000

    # Test lookups (should be O(1))
    import time
    start_time = time.time()

    # Perform many lookups
    for i in range(0, 1000, 100):
        element_id = f"R:{i:04d}"
        retrieved = index.get_element(element_id)
        assert retrieved is not None
        assert retrieved.id == element_id

    lookup_time = time.time() - start_time

    # Lookups should be very fast (under 0.1 seconds for 10 lookups)
    assert lookup_time < 0.1, f"Lookups took {lookup_time:.3f}s, may not be O(1)"


def test_file_based_lookup():
    """Test file-based element lookups."""
    index = DocumentIndex()

    # Add elements from different files
    elements = [
        create_test_element("R:Purpose", "Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Component", Kind.COMPONENT, File.SOFTWARE_DESIGN),
        create_test_element("T:0001", "Task 1", Kind.TASK, File.DEVELOPMENT_PLAN),
        create_test_element("T:0002", "Task 2", Kind.TASK, File.DEVELOPMENT_PLAN),
        create_test_element("TP:0001", "Test 1", Kind.TEST, File.TEST_PLAN),
    ]

    for element in elements:
        index.add_element(element)

    # Test file-based retrieval
    design_elements = index.get_elements_by_file(File.SOFTWARE_DESIGN)
    assert len(design_elements) == 2
    design_ids = {e.id for e in design_elements}
    assert design_ids == {"R:Purpose", "C:Component"}

    plan_elements = index.get_elements_by_file(File.DEVELOPMENT_PLAN)
    assert len(plan_elements) == 2
    plan_ids = {e.id for e in plan_elements}
    assert plan_ids == {"T:0001", "T:0002"}

    test_elements = index.get_elements_by_file(File.TEST_PLAN)
    assert len(test_elements) == 1
    assert test_elements[0].id == "TP:0001"


def test_reference_graph():
    """Test reference graph construction and traversal."""
    index = DocumentIndex()

    # Create elements with references
    elements = [
        create_test_element("R:Purpose", "Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Component", Kind.COMPONENT, File.SOFTWARE_DESIGN,
                          refs=["R:Purpose", "D:Data"]),
        create_test_element("D:Data", "Data Structure", Kind.DATA, File.SOFTWARE_DESIGN,
                          refs=["R:Purpose"]),
        create_test_element("M:Method", "Method", Kind.METHOD, File.SOFTWARE_DESIGN,
                          refs=["C:Component", "D:Data"]),
    ]

    for element in elements:
        index.add_element(element)

    # Test forward references
    component_refs = index.get_references("C:Component")
    assert set(component_refs) == {"R:Purpose", "D:Data"}

    method_refs = index.get_references("M:Method")
    assert set(method_refs) == {"C:Component", "D:Data"}

    purpose_refs = index.get_references("R:Purpose")
    assert len(purpose_refs) == 0  # No outgoing references

    # Test backlinks
    purpose_backlinks = index.get_backlinks("R:Purpose")
    assert set(purpose_backlinks) == {"C:Component", "D:Data"}

    data_backlinks = index.get_backlinks("D:Data")
    assert set(data_backlinks) == {"C:Component", "M:Method"}

    component_backlinks = index.get_backlinks("C:Component")
    assert set(component_backlinks) == {"M:Method"}

    # Test complete reference graph
    graph = index.get_reference_graph()
    assert len(graph) == 3  # Only elements with outgoing references
    assert set(graph["C:Component"]) == {"R:Purpose", "D:Data"}
    assert set(graph["M:Method"]) == {"C:Component", "D:Data"}


def test_search_exact_id_match():
    """Test exact ID search functionality."""
    index = DocumentIndex()

    elements = [
        create_test_element("R:Purpose", "System Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("R:Performance", "Performance Requirements", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Main Component", Kind.COMPONENT, File.SOFTWARE_DESIGN),
    ]

    for element in elements:
        index.add_element(element)

    # Test exact ID match
    results = index.search("R:Purpose")
    assert len(results) >= 1

    exact_match = results[0]  # Should be first (highest score)
    assert exact_match.element_id == "R:Purpose"
    assert exact_match.match_type == "id_exact"
    assert exact_match.match_score == 1.0


def test_search_partial_id_match():
    """Test partial ID search functionality."""
    index = DocumentIndex()

    elements = [
        create_test_element("R:Purpose", "System Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("R:Performance", "Performance Requirements", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Main Component", Kind.COMPONENT, File.SOFTWARE_DESIGN),
    ]

    for element in elements:
        index.add_element(element)

    # Test partial ID match
    results = index.search("R:P")
    assert len(results) >= 2

    # Should find both R:Purpose and R:Performance
    found_ids = {result.element_id for result in results}
    assert "R:Purpose" in found_ids
    assert "R:Performance" in found_ids

    # Check partial match types
    for result in results:
        if result.element_id in ["R:Purpose", "R:Performance"]:
            assert result.match_type == "id_partial"
            assert 0.0 < result.match_score < 1.0


def test_search_title_match():
    """Test title search functionality."""
    index = DocumentIndex()

    elements = [
        create_test_element("R:Purpose", "System Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("R:Performance", "System Performance Requirements", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Main System Component", Kind.COMPONENT, File.SOFTWARE_DESIGN),
    ]

    for element in elements:
        index.add_element(element)

    # Test exact title search
    results = index.search("System Purpose")
    assert len(results) >= 1

    exact_title_match = next((r for r in results if r.match_type == "title_exact"), None)
    assert exact_title_match is not None
    assert exact_title_match.element_id == "R:Purpose"

    # Test partial title search
    results = index.search("System")
    assert len(results) >= 3

    # Should find all elements with "System" in title
    found_ids = {result.element_id for result in results}
    assert "R:Purpose" in found_ids
    assert "R:Performance" in found_ids
    assert "C:Component" in found_ids


def test_search_ranking():
    """Test search result ranking by relevance."""
    index = DocumentIndex()

    elements = [
        create_test_element("R:Purpose", "System Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("R:Performance", "Performance Requirements", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
    ]

    for element in elements:
        index.add_element(element)

    # Test exact ID search (should be highest ranked)
    results = index.search("R:Purpose")
    assert len(results) >= 1
    top_result = results[0]
    assert top_result.element_id == "R:Purpose"
    assert top_result.match_type == "id_exact"
    assert top_result.match_score == 1.0

    # Test partial search that could match both ID and title
    results = index.search("Purpose")
    assert len(results) >= 1

    # Should find R:Purpose element
    purpose_result = next((r for r in results if r.element_id == "R:Purpose"), None)
    assert purpose_result is not None
    assert purpose_result.match_score > 0.5  # Should be a reasonable match


def test_statistics_generation():
    """Test index statistics generation."""
    index = DocumentIndex()

    # Add diverse elements
    elements = [
        create_test_element("R:Purpose", "Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("R:Performance", "Performance", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Component", Kind.COMPONENT, File.SOFTWARE_DESIGN, refs=["R:Purpose"]),
        create_test_element("T:0001", "Task 1", Kind.TASK, File.DEVELOPMENT_PLAN, refs=["R:Purpose", "C:Component"]),
        create_test_element("TP:0001", "Test 1", Kind.TEST, File.TEST_PLAN, refs=["T:0001"]),
    ]

    for element in elements:
        index.add_element(element)

    # Add orphaned reference
    orphaned_element = create_test_element("M:Method", "Method", Kind.METHOD, File.SOFTWARE_DESIGN,
                                         refs=["NonExistent:Element"])
    index.add_element(orphaned_element)

    stats = index.get_statistics()

    assert stats.total_elements == 6

    # Check kind distribution
    assert stats.elements_by_kind["Requirement"] == 2
    assert stats.elements_by_kind["Component"] == 1
    assert stats.elements_by_kind["Task"] == 1
    assert stats.elements_by_kind["Test"] == 1
    assert stats.elements_by_kind["Method"] == 1

    # Check file distribution
    assert stats.elements_by_file["software-design"] == 4
    assert stats.elements_by_file["development-plan"] == 1
    assert stats.elements_by_file["test-plan"] == 1

    # Check reference counts
    assert stats.total_references == 5  # 1 + 2 + 1 + 1 orphaned
    assert stats.orphaned_references == 1  # NonExistent:Element
    assert stats.elements_without_refs == 2  # R:Purpose, R:Performance have no refs


def test_reference_validation():
    """Test reference validation functionality."""
    index = DocumentIndex()

    # Add elements with some broken references
    elements = [
        create_test_element("R:Purpose", "Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Component", Kind.COMPONENT, File.SOFTWARE_DESIGN,
                          refs=["R:Purpose", "NonExistent:Element"]),
        create_test_element("M:Method", "Method", Kind.METHOD, File.SOFTWARE_DESIGN,
                          refs=["C:Component", "Another:Missing"]),
    ]

    for element in elements:
        index.add_element(element)

    # Validate references
    issues = index.validate_references()

    # Check broken references
    broken_refs = issues['broken_references']
    assert len(broken_refs) == 2
    assert "C:Component -> NonExistent:Element" in broken_refs
    assert "M:Method -> Another:Missing" in broken_refs

    # Should not have missing backlinks (internal consistency check)
    missing_backlinks = issues['missing_backlinks']
    assert len(missing_backlinks) == 0  # Our implementation keeps these consistent


def test_kind_based_lookup():
    """Test lookup by element kind."""
    index = DocumentIndex()

    elements = [
        create_test_element("R:Purpose", "Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("R:Performance", "Performance", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component1", "Component 1", Kind.COMPONENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component2", "Component 2", Kind.COMPONENT, File.SOFTWARE_DESIGN),
        create_test_element("T:0001", "Task", Kind.TASK, File.DEVELOPMENT_PLAN),
    ]

    for element in elements:
        index.add_element(element)

    # Test kind-based retrieval
    requirements = index.get_elements_by_kind(Kind.REQUIREMENT)
    assert len(requirements) == 2
    req_ids = {e.id for e in requirements}
    assert req_ids == {"R:Purpose", "R:Performance"}

    components = index.get_elements_by_kind(Kind.COMPONENT)
    assert len(components) == 2
    comp_ids = {e.id for e in components}
    assert comp_ids == {"C:Component1", "C:Component2"}

    tasks = index.get_elements_by_kind(Kind.TASK)
    assert len(tasks) == 1
    assert tasks[0].id == "T:0001"


def test_circular_reference_detection():
    """Test detection of circular references."""
    index = DocumentIndex()

    # Create elements with circular references
    elements = [
        create_test_element("A:Element", "Element A", Kind.COMPONENT, File.SOFTWARE_DESIGN, refs=["B:Element"]),
        create_test_element("B:Element", "Element B", Kind.COMPONENT, File.SOFTWARE_DESIGN, refs=["C:Element"]),
        create_test_element("C:Element", "Element C", Kind.COMPONENT, File.SOFTWARE_DESIGN, refs=["A:Element"]),
        create_test_element("D:Element", "Element D", Kind.COMPONENT, File.SOFTWARE_DESIGN, refs=["E:Element"]),
        create_test_element("E:Element", "Element E", Kind.COMPONENT, File.SOFTWARE_DESIGN),  # No cycle
    ]

    for element in elements:
        index.add_element(element)

    # Find circular references
    cycles = index.find_circular_references()

    # Should find one cycle
    assert len(cycles) >= 1

    # Check that the cycle contains all three elements
    cycle = cycles[0]
    cycle_elements = set(cycle[:-1])  # Remove duplicate last element
    assert cycle_elements == {"A:Element", "B:Element", "C:Element"}


def test_index_updates():
    """Test updating existing elements in the index."""
    index = DocumentIndex()

    # Add initial element
    original = create_test_element("R:Purpose", "Original Purpose", Kind.REQUIREMENT,
                                 File.SOFTWARE_DESIGN, refs=["C:Original"])
    index.add_element(original)

    assert index.get_element_count() == 1
    retrieved = index.get_element("R:Purpose")
    assert retrieved.title == "Original Purpose"
    assert retrieved.refs == ["C:Original"]

    # Update element with new title and references
    updated = create_test_element("R:Purpose", "Updated Purpose", Kind.REQUIREMENT,
                                File.SOFTWARE_DESIGN, refs=["C:Updated", "D:Data"])
    index.add_element(updated)  # Should replace existing

    # Should still have only one element
    assert index.get_element_count() == 1

    # But with updated content
    retrieved = index.get_element("R:Purpose")
    assert retrieved.title == "Updated Purpose"
    assert set(retrieved.refs) == {"C:Updated", "D:Data"}

    # Test search index is updated
    results = index.search("Updated Purpose")
    assert len(results) >= 1
    assert results[0].element_id == "R:Purpose"


def test_clear_index():
    """Test clearing all index data."""
    index = DocumentIndex()

    # Add some elements
    elements = [
        create_test_element("R:Purpose", "Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Component", Kind.COMPONENT, File.SOFTWARE_DESIGN, refs=["R:Purpose"]),
    ]

    for element in elements:
        index.add_element(element)

    assert index.get_element_count() == 2
    assert index.get_reference_count() == 1

    # Clear index
    index.clear()

    assert index.get_element_count() == 0
    assert index.get_reference_count() == 0
    assert len(index.get_all_elements()) == 0

    # Search should return no results
    results = index.search("Purpose")
    assert len(results) == 0


def test_reference_graph_export():
    """Test exporting the complete reference graph."""
    index = DocumentIndex()

    elements = [
        create_test_element("R:Purpose", "Purpose", Kind.REQUIREMENT, File.SOFTWARE_DESIGN),
        create_test_element("C:Component", "Component", Kind.COMPONENT, File.SOFTWARE_DESIGN, refs=["R:Purpose"]),
    ]

    for element in elements:
        index.add_element(element)

    # Export graph
    graph_data = index.export_reference_graph()

    assert 'elements' in graph_data
    assert 'references' in graph_data
    assert 'backlinks' in graph_data
    assert 'statistics' in graph_data

    # Check elements
    elements_data = graph_data['elements']
    assert len(elements_data) == 2
    assert "R:Purpose" in elements_data
    assert "C:Component" in elements_data

    # Check references
    references_data = graph_data['references']
    assert "C:Component" in references_data
    assert references_data["C:Component"] == ["R:Purpose"]

    # Check backlinks
    backlinks_data = graph_data['backlinks']
    assert "R:Purpose" in backlinks_data
    assert backlinks_data["R:Purpose"] == ["C:Component"]


def test_convenience_function():
    """Test convenience function for creating index."""
    index = create_index()
    assert isinstance(index, DocumentIndex)
    assert index.get_element_count() == 0


def test_error_handling():
    """Test error handling in index operations."""
    index = DocumentIndex()

    # Test getting non-existent element
    result = index.get_element("NonExistent")
    assert result is None

    # Test searching with empty query
    results = index.search("")
    assert len(results) == 0

    results = index.search("   ")  # Whitespace only
    assert len(results) == 0


if __name__ == "__main__":
    # Run all tests manually
    print("Running indexer tests...")

    test_index_initialization()
    print("✓ Index initialization")

    test_add_remove_elements()
    print("✓ Add/remove elements")

    test_o1_id_lookup()
    print("✓ O(1) ID lookup performance")

    test_file_based_lookup()
    print("✓ File-based lookup")

    test_reference_graph()
    print("✓ Reference graph construction")

    test_search_exact_id_match()
    print("✓ Exact ID search")

    test_search_partial_id_match()
    print("✓ Partial ID search")

    test_search_title_match()
    print("✓ Title search")

    test_search_ranking()
    print("✓ Search result ranking")

    test_statistics_generation()
    print("✓ Statistics generation")

    test_reference_validation()
    print("✓ Reference validation")

    test_kind_based_lookup()
    print("✓ Kind-based lookup")

    test_circular_reference_detection()
    print("✓ Circular reference detection")

    test_index_updates()
    print("✓ Index updates")

    test_clear_index()
    print("✓ Clear index")

    test_reference_graph_export()
    print("✓ Reference graph export")

    test_convenience_function()
    print("✓ Convenience function")

    test_error_handling()
    print("✓ Error handling")

    print("\nAll tests passed! T:0010 indexer data structures complete.")