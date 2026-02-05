"""
Tests for reference detection functionality.

This validates T:0006 acceptance criteria.
"""

from reference_detection import (
    ReferenceDetector, Reference, ReferenceDetectionError,
    detect_references, extract_reference_ids
)


def test_inline_reference_detection():
    """Test detection of inline ID references."""
    body_text = """This component implements C:WorkspaceManager functionality
    and uses D:ProjectInfo for data storage. It also calls M:loadWorkspace
    to initialize the workspace structure.

    See also R:CoreWorkflow for the complete workflow."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should find 4 unique references
    assert len(references) == 4

    # Check specific references
    ref_ids = [ref.target_id for ref in references]
    assert "C:WorkspaceManager" in ref_ids
    assert "D:ProjectInfo" in ref_ids
    assert "M:loadWorkspace" in ref_ids
    assert "R:CoreWorkflow" in ref_ids

    # Check reference types
    for ref in references:
        assert ref.reference_type == "inline"

    # Check context extraction
    workspace_ref = next(ref for ref in references if ref.target_id == "C:WorkspaceManager")
    assert "implements C:WorkspaceManager functionality" in workspace_ref.context

    # Check line and position tracking
    assert workspace_ref.line_number == 0
    assert workspace_ref.position_in_line > 0


def test_explicit_reference_detection():
    """Test detection of explicit References: sections."""
    body_text = """This component provides core functionality.

## References:

- C:WorkspaceManager - Manages workspace loading
- D:ProjectInfo - Contains project metadata
- M:validateStructure - Validates workspace structure
- I:FileSystemWatcher - Monitors file changes

Additional implementation notes here."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should find 4 explicit references
    explicit_refs = [ref for ref in references if ref.reference_type == "explicit"]
    assert len(explicit_refs) == 4

    # Check reference IDs
    ref_ids = [ref.target_id for ref in explicit_refs]
    assert "C:WorkspaceManager" in ref_ids
    assert "D:ProjectInfo" in ref_ids
    assert "M:validateStructure" in ref_ids
    assert "I:FileSystemWatcher" in ref_ids

    # Check contexts include descriptions
    workspace_ref = next(ref for ref in explicit_refs if ref.target_id == "C:WorkspaceManager")
    assert "Manages workspace loading" in workspace_ref.context


def test_mixed_reference_types():
    """Test detection when both inline and explicit references exist."""
    body_text = """This implements C:WorkspaceManager and uses D:ProjectInfo.

## References:

- R:CoreRequirement - Main system requirement
- UI:MainWindow - Primary interface

The implementation also calls M:loadProject internally."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should find 5 total references
    assert len(references) == 5

    # Check reference types
    inline_refs = [ref for ref in references if ref.reference_type == "inline"]
    explicit_refs = [ref for ref in references if ref.reference_type == "explicit"]

    assert len(inline_refs) == 3  # C:WorkspaceManager, D:ProjectInfo, M:loadProject
    assert len(explicit_refs) == 2  # R:CoreRequirement, UI:MainWindow


def test_deduplication():
    """Test that duplicate references are deduplicated."""
    body_text = """This uses C:WorkspaceManager for loading.

## References:

- C:WorkspaceManager - Workspace management component

The C:WorkspaceManager handles all workspace operations."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should only have one C:WorkspaceManager reference (explicit takes priority)
    workspace_refs = [ref for ref in references if ref.target_id == "C:WorkspaceManager"]
    assert len(workspace_refs) == 1
    assert workspace_refs[0].reference_type == "explicit"  # Explicit references win


def test_case_insensitive_detection():
    """Test that references work regardless of case."""
    body_text = """This implements c:workspacemanager and uses r:corerequirement.

Also references t:001 and tp:001."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should find all references despite case differences
    assert len(references) == 4

    ref_ids = [ref.target_id for ref in references]
    assert "C:workspacemanager" in ref_ids  # Prefix normalized to uppercase
    assert "R:corerequirement" in ref_ids
    assert "T:001" in ref_ids
    assert "TP:001" in ref_ids


def test_reference_validation():
    """Test reference validation against known IDs."""
    known_ids = {
        "C:WorkspaceManager",
        "D:ProjectInfo",
        "M:loadWorkspace",
        "R:CoreRequirement"
    }

    body_text = """This implements C:WorkspaceManager and uses D:ProjectInfo.
    It also references M:loadWorkspace and C:UnknownComponent."""

    detector = ReferenceDetector(known_ids)
    references = detector.detect_references_in_text(body_text)

    validation_result = detector.validate_references(references)

    # Check validation results
    assert len(validation_result['valid']) == 3
    assert len(validation_result['invalid']) == 1

    assert "C:WorkspaceManager" in validation_result['valid']
    assert "D:ProjectInfo" in validation_result['valid']
    assert "M:loadWorkspace" in validation_result['valid']
    assert "C:UnknownComponent" in validation_result['invalid']


def test_broken_reference_detection():
    """Test finding broken references."""
    known_ids = {"C:ValidComponent", "D:ValidData"}

    body_text = """This uses C:ValidComponent and C:BrokenComponent.
    Also references D:ValidData and D:BrokenData."""

    detector = ReferenceDetector(known_ids)
    references = detector.detect_references_in_text(body_text)

    broken_refs = detector.find_broken_references(references)

    assert len(broken_refs) == 2
    broken_ids = [ref.target_id for ref in broken_refs]
    assert "C:BrokenComponent" in broken_ids
    assert "D:BrokenData" in broken_ids


def test_reference_statistics():
    """Test reference statistics generation."""
    body_text = """This implements C:Component1 and C:Component2.
    Uses D:Data1 and calls M:Method1.

## References:

- R:Requirement1 - Main requirement
- UI:Interface1 - User interface"""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    stats = detector.get_reference_statistics(references)

    assert stats['total_references'] == 6
    assert stats['unique_targets'] == 6
    assert stats['inline_references'] == 4
    assert stats['explicit_references'] == 2

    # Check prefix counts
    assert stats['by_prefix']['C:'] == 2
    assert stats['by_prefix']['D:'] == 1
    assert stats['by_prefix']['M:'] == 1
    assert stats['by_prefix']['R:'] == 1
    assert stats['by_prefix']['UI:'] == 1


def test_reference_grouping():
    """Test grouping references by target."""
    body_text = """This uses C:WorkspaceManager for loading.
    The C:WorkspaceManager also handles validation.

## References:

- C:WorkspaceManager - Core workspace component"""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    grouped = detector.group_references_by_target(references)

    # Should only have one unique target due to deduplication
    assert len(grouped) == 1
    assert "C:WorkspaceManager" in grouped
    assert len(grouped["C:WorkspaceManager"]) == 1


def test_reference_patterns():
    """Test analysis of reference patterns in context."""
    body_text = """This component implements C:WorkspaceManager interface.
    It uses D:ProjectInfo for data storage.
    The system extends R:BaseRequirement functionality.
    Users can call M:loadWorkspace method.
    See R:Documentation for more details.
    Based on C:OriginalDesign architecture."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    patterns = detector.find_reference_patterns(references)

    # Check that patterns are detected
    assert 'implements' in patterns
    assert 'uses' in patterns
    assert 'extends' in patterns
    assert 'calls' in patterns
    assert 'see' in patterns
    assert 'based_on' in patterns

    # Check examples are captured
    assert len(patterns['implements']) > 0
    assert any("implements C:WorkspaceManager" in example for example in patterns['implements'])


def test_multiple_references_sections():
    """Test handling multiple References: sections."""
    body_text = """First section with content.

## References:

- C:Component1 - First component

Additional content here.

### References:

- D:Data1 - First data structure
- M:Method1 - First method"""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    explicit_refs = [ref for ref in references if ref.reference_type == "explicit"]
    assert len(explicit_refs) == 3

    ref_ids = [ref.target_id for ref in explicit_refs]
    assert "C:Component1" in ref_ids
    assert "D:Data1" in ref_ids
    assert "M:Method1" in ref_ids


def test_empty_references_section():
    """Test handling of empty References: sections."""
    body_text = """Component description.

## References:

Additional content after empty section."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should find no references
    assert len(references) == 0


def test_invalid_id_formats():
    """Test that invalid ID formats are ignored."""
    body_text = """This mentions some invalid patterns:
    - X:InvalidPrefix (unknown prefix)
    - C: (missing suffix)
    - :MissingPrefix (missing prefix)
    - C:123Invalid (invalid suffix format for C:)
    - Regular text with colons: like this

Valid references: C:ValidComponent and T:001."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should only find valid references
    assert len(references) == 2
    ref_ids = [ref.target_id for ref in references]
    assert "C:ValidComponent" in ref_ids
    assert "T:001" in ref_ids


def test_convenience_functions():
    """Test convenience functions for reference detection."""
    body_text = """This implements C:WorkspaceManager and uses D:ProjectInfo.

## References:

- M:loadWorkspace - Loads workspace data"""

    # Test detect_references function
    references = detect_references(body_text)
    assert len(references) == 3

    # Test extract_reference_ids function
    ref_ids = extract_reference_ids(body_text)
    assert len(ref_ids) == 3
    assert "C:WorkspaceManager" in ref_ids
    assert "D:ProjectInfo" in ref_ids
    assert "M:loadWorkspace" in ref_ids


def test_context_extraction():
    """Test that context is properly extracted around references."""
    body_text = """The component architecture implements C:WorkspaceManager as the core system."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    assert len(references) == 1
    ref = references[0]

    # Context should include surrounding text (up to 20 chars each side)
    assert "implements C:WorkspaceManager as" in ref.context
    assert len(ref.context) <= 60  # 20 + ID + 20 + some buffer


def test_line_and_position_tracking():
    """Test accurate line and position tracking."""
    body_text = """Line 0 content here.
Line 1 has C:Component reference.
Line 2 with D:Data reference here."""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    assert len(references) == 2

    # Check component reference
    component_ref = next(ref for ref in references if ref.target_id == "C:Component")
    assert component_ref.line_number == 1
    assert component_ref.position_in_line > 0

    # Check data reference
    data_ref = next(ref for ref in references if ref.target_id == "D:Data")
    assert data_ref.line_number == 2
    assert data_ref.position_in_line > 0


def test_error_handling():
    """Test error handling for invalid inputs."""
    detector = ReferenceDetector()

    try:
        # This should not raise an error, just return empty list
        references = detector.detect_references_in_text("")
        assert len(references) == 0
    except ReferenceDetectionError:
        assert False, "Should handle empty input gracefully"

    # Test with None input should raise error
    try:
        detector.detect_references_in_text(None)
        assert False, "Should raise error for None input"
    except (ReferenceDetectionError, TypeError):
        pass  # Expected


def test_references_with_special_characters():
    """Test references that include special markdown characters."""
    body_text = """This **implements** *C:WorkspaceManager* functionality.

Code block reference:
```python
# Uses D:ProjectInfo
data = load_project_info()
```

List with reference:
- Uses `M:loadWorkspace` method
- Calls [R:CoreRequirement](link) for validation"""

    detector = ReferenceDetector()
    references = detector.detect_references_in_text(body_text)

    # Should find all references despite markdown formatting
    assert len(references) == 4

    ref_ids = [ref.target_id for ref in references]
    assert "C:WorkspaceManager" in ref_ids
    assert "D:ProjectInfo" in ref_ids
    assert "M:loadWorkspace" in ref_ids
    assert "R:CoreRequirement" in ref_ids


if __name__ == "__main__":
    # Run all tests manually
    print("Running reference detection tests...")

    test_inline_reference_detection()
    print("✓ Inline reference detection")

    test_explicit_reference_detection()
    print("✓ Explicit reference detection")

    test_mixed_reference_types()
    print("✓ Mixed reference types")

    test_deduplication()
    print("✓ Reference deduplication")

    test_case_insensitive_detection()
    print("✓ Case insensitive detection")

    test_reference_validation()
    print("✓ Reference validation")

    test_broken_reference_detection()
    print("✓ Broken reference detection")

    test_reference_statistics()
    print("✓ Reference statistics")

    test_reference_grouping()
    print("✓ Reference grouping")

    test_reference_patterns()
    print("✓ Reference patterns")

    test_multiple_references_sections()
    print("✓ Multiple References sections")

    test_empty_references_section()
    print("✓ Empty References section")

    test_invalid_id_formats()
    print("✓ Invalid ID format handling")

    test_convenience_functions()
    print("✓ Convenience functions")

    test_context_extraction()
    print("✓ Context extraction")

    test_line_and_position_tracking()
    print("✓ Line and position tracking")

    test_error_handling()
    print("✓ Error handling")

    test_references_with_special_characters()
    print("✓ Special character handling")

    print("\nAll tests passed! T:0006 reference detection is complete.")