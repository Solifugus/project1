"""
Basic tests for DocElement implementation.

This validates T:0001 acceptance criteria.
"""

from doc_element import DocElement, Kind, File, Status


def test_create_valid_doc_element():
    """Test creating DocElement with all required fields."""
    element = DocElement(
        id="R:Purpose",
        kind=Kind.REQUIREMENT,
        title="System Purpose",
        file=File.SOFTWARE_DESIGN,
        heading_level=3,
        anchor="r-purpose",
        body_markdown="Project1 provides a disciplined workflow...",
        refs=["C:WorkspaceManager", "D:DocElement"],
        backlinks=["T:0001"]
    )

    assert element.id == "R:Purpose"
    assert element.kind == Kind.REQUIREMENT
    assert element.title == "System Purpose"
    assert element.file == File.SOFTWARE_DESIGN
    assert element.heading_level == 3
    assert element.anchor == "r-purpose"
    assert element.body_markdown == "Project1 provides a disciplined workflow..."
    assert element.refs == ["C:WorkspaceManager", "D:DocElement"]
    assert element.backlinks == ["T:0001"]
    assert element.status is None  # Not a task


def test_task_element_with_status():
    """Test creating Task element with default status."""
    task = DocElement(
        id="T:0001",
        kind=Kind.TASK,
        title="Define DocElement data structure",
        file=File.DEVELOPMENT_PLAN,
        heading_level=3,
        anchor="t-0001",
        body_markdown="Implement the core DocElement struct/class...",
    )

    assert task.kind == Kind.TASK
    assert task.status == Status.PENDING  # Default for new tasks
    assert task.is_task() is True


def test_non_task_with_status_fails():
    """Test that non-Task elements cannot have status."""
    try:
        DocElement(
            id="R:Purpose",
            kind=Kind.REQUIREMENT,
            title="System Purpose",
            file=File.SOFTWARE_DESIGN,
            heading_level=3,
            anchor="r-purpose",
            body_markdown="Some content...",
            status=Status.PENDING  # Invalid for non-Task
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Status field only valid for Task kind" in str(e)


def test_empty_id_fails():
    """Test that empty ID raises validation error."""
    try:
        DocElement(
            id="",  # Invalid empty ID
            kind=Kind.REQUIREMENT,
            title="System Purpose",
            file=File.SOFTWARE_DESIGN,
            heading_level=3,
            anchor="r-purpose",
            body_markdown="Some content..."
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "DocElement id cannot be empty" in str(e)


def test_serialization_roundtrip():
    """Test JSON serialization and deserialization."""
    original = DocElement(
        id="C:WorkspaceManager",
        kind=Kind.COMPONENT,
        title="Workspace Manager",
        file=File.SOFTWARE_DESIGN,
        heading_level=3,
        anchor="c-workspacemanager",
        body_markdown="Purpose: Load, validate, and index...",
        refs=["R:WorkspaceLayout"],
        backlinks=["T:0008", "T:0012"]
    )

    # Serialize to JSON and back
    json_str = original.to_json()
    restored = DocElement.from_json(json_str)

    assert restored.id == original.id
    assert restored.kind == original.kind
    assert restored.title == original.title
    assert restored.file == original.file
    assert restored.heading_level == original.heading_level
    assert restored.anchor == original.anchor
    assert restored.body_markdown == original.body_markdown
    assert restored.refs == original.refs
    assert restored.backlinks == original.backlinks
    assert restored.status == original.status


def test_task_serialization_with_status():
    """Test Task element serialization preserves status."""
    task = DocElement(
        id="T:0001",
        kind=Kind.TASK,
        title="Define DocElement",
        file=File.DEVELOPMENT_PLAN,
        heading_level=3,
        anchor="t-0001",
        body_markdown="Implementation details...",
        status=Status.IN_PROGRESS
    )

    json_str = task.to_json()
    restored = DocElement.from_json(json_str)

    assert restored.status == Status.IN_PROGRESS
    assert restored.is_task() is True


def test_reference_management():
    """Test adding references and backlinks."""
    element = DocElement(
        id="C:Parser",
        kind=Kind.COMPONENT,
        title="Markdown Parser",
        file=File.SOFTWARE_DESIGN,
        heading_level=3,
        anchor="c-parser",
        body_markdown="Parses markdown files..."
    )

    # Add references
    element.add_reference("D:DocElement")
    element.add_reference("C:Indexer")
    element.add_reference("D:DocElement")  # Duplicate should be ignored

    assert element.refs == ["D:DocElement", "C:Indexer"]

    # Add backlinks
    element.add_backlink("T:0004")
    element.add_backlink("T:0007")
    element.add_backlink("T:0004")  # Duplicate should be ignored

    assert element.backlinks == ["T:0004", "T:0007"]


def test_enum_validation():
    """Test enum fields accept only valid values."""
    # Valid enums should work
    element = DocElement(
        id="UI:MainWindow",
        kind=Kind.UI,
        title="Main Application Window",
        file=File.SOFTWARE_DESIGN,
        heading_level=3,
        anchor="ui-mainwindow",
        body_markdown="Main window layout..."
    )

    assert element.kind == Kind.UI
    assert element.file == File.SOFTWARE_DESIGN


if __name__ == "__main__":
    # Run basic tests manually
    print("Running DocElement tests...")
    test_create_valid_doc_element()
    print("✓ Valid DocElement creation")

    test_task_element_with_status()
    print("✓ Task element with status")

    test_non_task_with_status_fails()
    print("✓ Non-task status validation")

    test_empty_id_fails()
    print("✓ Empty ID validation")

    test_serialization_roundtrip()
    print("✓ JSON serialization roundtrip")

    test_task_serialization_with_status()
    print("✓ Task status serialization")

    test_reference_management()
    print("✓ Reference management")

    test_enum_validation()
    print("✓ Enum validation")

    print("\nAll tests passed! T:0001 implementation is complete.")