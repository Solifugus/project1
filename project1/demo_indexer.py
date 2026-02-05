"""
Demo showing indexer data structures with real Project1 data.
"""

from indexer import create_index, SearchMatch
from markdown_parser import parse_markdown_file
from workspace_discovery import discover_workspace
from workspace_paths import get_artifact_path, ArtifactType
import time
from pathlib import Path


def format_search_results(results: list) -> str:
    """Format search results for display."""
    if not results:
        return "No results found"

    output = []
    for i, result in enumerate(results, 1):
        score_bar = "█" * int(result.match_score * 10) + "░" * (10 - int(result.match_score * 10))
        match_icon = {
            'id_exact': '🎯',
            'id_partial': '🔍',
            'title_exact': '📝',
            'title_partial': '📄'
        }.get(result.match_type, '❓')

        output.append(
            f"  {i}. {match_icon} {result.element_id} "
            f"({result.match_score:.2f}) [{score_bar}]\n"
            f"     Title: {result.element_title}\n"
            f"     Match: {result.match_type} - \"{result.matched_text[:50]}{'...' if len(result.matched_text) > 50 else ''}\""
        )

    return "\n".join(output)


def main():
    """Demonstrate indexer functionality with real Project1 data."""
    print("Indexer Data Structures Demo - Project1 Document Index")
    print("=" * 56)

    # Create the index
    index = create_index()
    print("Created empty document index")

    # Discover workspace and load documents
    print("\nLOADING DOCUMENTS")
    print("-" * 17)

    try:
        workspace_info = discover_workspace()
        projects = [p for p in workspace_info.projects if p.status.value == 'complete']

        if not projects:
            print("No complete projects found in workspace")
            return

        print(f"Found {len(projects)} complete projects to index")

        total_elements = 0
        load_times = {}

        for project in projects:
            project_name = project.name
            print(f"\n📁 Indexing project: {project_name}")

            # Load files for this project
            artifacts = [
                ("software-design.md", ArtifactType.SOFTWARE_DESIGN),
                ("development-plan.md", ArtifactType.DEVELOPMENT_PLAN),
                ("test-plan.md", ArtifactType.TEST_PLAN),
            ]

            project_elements = 0
            for file_desc, artifact_type in artifacts:
                file_path = get_artifact_path(project_name, artifact_type)

                if file_path.exists():
                    print(f"   📄 Parsing {file_desc}...")
                    start_time = time.time()

                    try:
                        elements = parse_markdown_file(str(file_path))
                        parse_time = time.time() - start_time

                        print(f"      Found {len(elements)} elements ({parse_time:.3f}s)")

                        # Add elements to index
                        add_start = time.time()
                        for element in elements:
                            index.add_element(element)
                        add_time = time.time() - add_start

                        project_elements += len(elements)
                        load_times[f"{project_name}/{file_desc}"] = {
                            'parse_time': parse_time,
                            'index_time': add_time,
                            'elements': len(elements)
                        }

                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                else:
                    print(f"      ⚠️  File not found: {file_path}")

            total_elements += project_elements
            print(f"   ✅ Project total: {project_elements} elements")

        print(f"\n🏁 Indexing complete: {total_elements} total elements indexed")

    except Exception as e:
        print(f"Error loading documents: {e}")
        return

    # Index Statistics
    print("\nINDEX STATISTICS")
    print("-" * 16)

    stats = index.get_statistics()
    print(f"  Total elements: {stats.total_elements}")
    print(f"  Total references: {stats.total_references}")
    print(f"  Orphaned references: {stats.orphaned_references}")
    print(f"  Elements without refs: {stats.elements_without_refs}")
    print(f"  Search index size: {stats.search_index_size}")

    print(f"\n  Elements by kind:")
    for kind, count in sorted(stats.elements_by_kind.items()):
        percentage = (count / stats.total_elements) * 100
        print(f"    {kind:<12}: {count:>3} ({percentage:>5.1f}%)")

    print(f"\n  Elements by file:")
    for file_name, count in sorted(stats.elements_by_file.items()):
        percentage = (count / stats.total_elements) * 100
        print(f"    {file_name:<20}: {count:>3} ({percentage:>5.1f}%)")

    # Performance Analysis
    print(f"\n  Loading performance:")
    total_parse_time = sum(data['parse_time'] for data in load_times.values())
    total_index_time = sum(data['index_time'] for data in load_times.values())

    print(f"    Total parse time: {total_parse_time:.3f}s")
    print(f"    Total index time: {total_index_time:.3f}s")
    print(f"    Elements per second: {stats.total_elements / (total_parse_time + total_index_time):.1f}")

    # Reference Graph Analysis
    print(f"\nREFERENCE GRAPH ANALYSIS")
    print("-" * 24)

    # Find most referenced elements
    all_elements = index.get_all_elements()
    backlink_counts = [(element.id, len(index.get_backlinks(element.id))) for element in all_elements]
    most_referenced = sorted(backlink_counts, key=lambda x: x[1], reverse=True)

    print("  Most referenced elements:")
    for element_id, backlink_count in most_referenced[:10]:
        if backlink_count > 0:
            element = index.get_element(element_id)
            print(f"    {element_id:<25}: {backlink_count:>2} references")
            print(f"      Title: {element.title[:50]}{'...' if len(element.title) > 50 else ''}")

    # Find elements with most outgoing references
    ref_counts = [(element.id, len(element.refs)) for element in all_elements]
    most_referring = sorted(ref_counts, key=lambda x: x[1], reverse=True)

    print(f"\n  Elements with most outgoing references:")
    for element_id, ref_count in most_referring[:5]:
        if ref_count > 0:
            element = index.get_element(element_id)
            refs = index.get_references(element_id)
            print(f"    {element_id:<25}: {ref_count:>2} refs → {', '.join(refs[:3])}{'...' if len(refs) > 3 else ''}")

    # Validate references
    validation_issues = index.validate_references()
    broken_refs = validation_issues['broken_references']

    if broken_refs:
        print(f"\n  ⚠️  Validation issues:")
        print(f"    Broken references: {len(broken_refs)}")
        for broken_ref in broken_refs[:5]:
            print(f"      {broken_ref}")
        if len(broken_refs) > 5:
            print(f"      ... and {len(broken_refs) - 5} more")
    else:
        print(f"\n  ✅ Reference validation: All references are valid")

    # Check for circular references
    cycles = index.find_circular_references()
    if cycles:
        print(f"\n  🔄 Circular references found: {len(cycles)}")
        for i, cycle in enumerate(cycles[:3]):
            cycle_str = " → ".join(cycle)
            print(f"    {i+1}. {cycle_str}")
    else:
        print(f"\n  ✅ No circular references found")

    # Search Functionality Demo
    print(f"\nSEARCH FUNCTIONALITY DEMO")
    print("-" * 25)

    search_queries = [
        "Purpose",           # Should match R:Purpose and titles
        "C:Workspace",      # Partial ID match
        "Component",        # Title word match
        "T:0001",          # Exact task ID
        "Workspace Manager" # Multi-word title
    ]

    for query in search_queries:
        print(f"\n🔍 Search: \"{query}\"")
        start_time = time.time()
        results = index.search(query, limit=5)
        search_time = time.time() - start_time

        print(f"   Found {len(results)} results in {search_time:.4f}s")
        if results:
            formatted_results = format_search_results(results)
            print(formatted_results)

    # Lookup Performance Test
    print(f"\nLOOKUP PERFORMANCE TEST")
    print("-" * 23)

    # Test O(1) ID lookups
    test_elements = list(index._elements.keys())[:100]  # Get first 100 element IDs

    start_time = time.time()
    lookup_count = 0

    for _ in range(10):  # 10 rounds of lookups
        for element_id in test_elements:
            element = index.get_element(element_id)
            lookup_count += 1
            assert element is not None

    lookup_time = time.time() - start_time
    lookups_per_second = lookup_count / lookup_time

    print(f"  Performed {lookup_count} lookups in {lookup_time:.4f}s")
    print(f"  Rate: {lookups_per_second:.0f} lookups/second")
    print(f"  Average: {(lookup_time / lookup_count) * 1000:.4f}ms per lookup")

    if lookups_per_second > 10000:
        print("  ✅ O(1) lookup performance confirmed")
    else:
        print("  ⚠️  Lookup performance may not be optimal")

    # Advanced Features Demo
    print(f"\nADVANCED FEATURES")
    print("-" * 17)

    # Kind-based filtering
    from doc_element import Kind
    requirements = index.get_elements_by_kind(Kind.REQUIREMENT)
    tasks = index.get_elements_by_kind(Kind.TASK)
    components = index.get_elements_by_kind(Kind.COMPONENT)

    print(f"  Kind-based filtering:")
    print(f"    Requirements: {len(requirements)}")
    print(f"    Tasks: {len(tasks)}")
    print(f"    Components: {len(components)}")

    # File-based filtering
    from doc_element import File
    design_elements = index.get_elements_by_file(File.SOFTWARE_DESIGN)
    plan_elements = index.get_elements_by_file(File.DEVELOPMENT_PLAN)

    print(f"\n  File-based filtering:")
    print(f"    Software Design: {len(design_elements)}")
    print(f"    Development Plan: {len(plan_elements)}")

    # Export reference graph
    graph_data = index.export_reference_graph()
    graph_size = len(str(graph_data))

    print(f"\n  Reference graph export:")
    print(f"    Serialized size: {graph_size:,} bytes")
    print(f"    Elements: {len(graph_data['elements'])}")
    print(f"    Reference mappings: {len(graph_data['references'])}")
    print(f"    Backlink mappings: {len(graph_data['backlinks'])}")

    print()
    print("✅ Fast O(1) ID lookups")
    print("✅ Efficient reference graph traversal")
    print("✅ Search index with partial matching")
    print("✅ File and kind-based filtering")
    print("✅ Reference validation and cycle detection")
    print("✅ Comprehensive statistics and analysis")
    print("✅ High-performance search functionality")
    print("✅ Reference graph export capability")
    print("✅ Multi-project document indexing")

    if stats.total_elements > 0:
        print(f"✅ Successfully indexed {stats.total_elements} elements from real Project1 data")


if __name__ == "__main__":
    main()