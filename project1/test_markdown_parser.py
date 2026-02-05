"""
Tests for full markdown parsing functionality.

This validates T:0007 acceptance criteria.
"""

from markdown_parser import (
    MarkdownParser, MarkdownParsingError, ParsedElement,
    parse_markdown_file, parse_markdown_content
)
from doc_element import DocElement, Kind, File, Status


def test_basic_parsing():
    """Test basic markdown parsing into DocElements."""
    markdown_text = """# R:Purpose - System Purpose

This system provides a disciplined workflow for building software.
It references C:WorkspaceManager for workspace operations.

## C:WorkspaceManager - Workspace Management Component

Purpose: Load, validate, and index the workspace.

Responsibilities:
- Discover projects in the workspace
- Validate structure using M:validateStructure

## References:

- I:ProjectDiscovery - Project discovery interface
- D:WorkspaceStructure - Workspace data structure

### M:loadWorkspace - Load Workspace Method

```python
def load_workspace(path: str) -> WorkspaceInfo:
    pass
```
"""

    parser = MarkdownParser("software-design.md")
    elements = parser.parse_markdown(markdown_text)

    # Should find 4 elements
    assert len(elements) == 4

    # Check R:Purpose element
    purpose = next(e for e in elements if e.id == "R:Purpose")
    assert purpose.kind == Kind.REQUIREMENT
    assert purpose.title == "System Purpose"
    assert purpose.file == File.SOFTWARE_DESIGN
    assert purpose.heading_level == 1
    assert purpose.anchor == "system-purpose"
    assert "C:WorkspaceManager" in purpose.refs
    assert len(purpose.refs) == 1

    # Check C:WorkspaceManager element
    workspace_mgr = next(e for e in elements if e.id == "C:WorkspaceManager")
    assert workspace_mgr.kind == Kind.COMPONENT
    assert workspace_mgr.title == "Workspace Management Component"
    assert workspace_mgr.heading_level == 2
    assert "M:validateStructure" in workspace_mgr.refs

    # Check explicit references element (should have no ID)
    ref_element = next(e for e in elements if "References" in e.title)
    assert ref_element.kind == Kind.OTHER
    assert ref_element.id.startswith("NoID_")
    assert "I:ProjectDiscovery" in ref_element.refs
    assert "D:WorkspaceStructure" in ref_element.refs

    # Check M:loadWorkspace element
    method = next(e for e in elements if e.id == "M:loadWorkspace")
    assert method.kind == Kind.METHOD
    assert method.title == "Load Workspace Method"
    assert method.heading_level == 3


def test_file_enum_detection():
    """Test that File enum is correctly detected from file paths."""
    test_cases = [
        ("software-design.md", File.SOFTWARE_DESIGN),
        ("development-plan.md", File.DEVELOPMENT_PLAN),
        ("test-plan.md", File.TEST_PLAN),
        ("conventions.md", File.CONVENTIONS),
        ("/path/to/software-design.md", File.SOFTWARE_DESIGN),
        ("unknown-file.md", None),
    ]

    for file_path, expected_file in test_cases:
        parser = MarkdownParser(file_path)
        if expected_file:
            assert parser.file_enum == expected_file
        else:
            assert parser.file_enum is None


def test_kind_detection():
    """Test that Kind is correctly determined from ID prefixes."""
    markdown_text = """# R:Requirement - A Requirement

Content.

## C:Component - A Component

Content.

### D:Data - Data Structure

Content.

#### I:Interface - Interface Spec

Content.

##### M:Method - Method Spec

Content.

## UI:Window - UI Element

Content.

## T:0001 - Task Item

Content.

## TP:0001 - Test Plan Item

Content.

## UnknownPrefix:Something - Unknown

Content.

## No ID Here

Content.
"""

    parser = MarkdownParser("test.md")
    elements = parser.parse_markdown(markdown_text)

    # Check each valid ID kind
    kind_mapping = {
        "R:Requirement": Kind.REQUIREMENT,
        "C:Component": Kind.COMPONENT,
        "D:Data": Kind.DATA,
        "I:Interface": Kind.INTERFACE,
        "M:Method": Kind.METHOD,
        "UI:Window": Kind.UI,
        "T:0001": Kind.TASK,
        "TP:0001": Kind.TEST,
    }

    for element_id, expected_kind in kind_mapping.items():
        element = next(e for e in elements if e.id == element_id)
        assert element.kind == expected_kind

    # Check elements without valid IDs (should get NoID_ placeholders)
    no_id_elements = [e for e in elements if e.id.startswith("NoID_")]
    assert len(no_id_elements) == 2  # "UnknownPrefix:Something" and "No ID Here"

    for element in no_id_elements:
        assert element.kind == Kind.OTHER


def test_task_status_detection():
    """Test task status extraction from content."""
    markdown_text = """# T:0001 - Completed Task

This task is completed and done.

## T:0002 - In Progress Task

Currently implementing this feature.

### T:0003 - Pending Task

This task needs to be started.

#### T:0004 - Another Pending Task

No status indicators in content.
"""

    parser = MarkdownParser("development-plan.md")
    elements = parser.parse_markdown(markdown_text)

    # Check status detection
    task_1 = next(e for e in elements if e.id == "T:0001")
    assert task_1.status == Status.COMPLETED

    task_2 = next(e for e in elements if e.id == "T:0002")
    assert task_2.status == Status.IN_PROGRESS

    task_3 = next(e for e in elements if e.id == "T:0003")
    assert task_3.status == Status.PENDING

    task_4 = next(e for e in elements if e.id == "T:0004")
    assert task_4.status == Status.PENDING


def test_anchor_generation():
    """Test URL anchor generation from titles."""
    markdown_text = """# R:Test - Simple Title

Content.

## C:Component - Complex Title with Symbols! & Numbers 123

Content.

### D:Data - Multiple    Spaces   and-Hyphens

Content.

#### M:Method - Unicode: émojis 🎉 and spëcial chars

Content.
"""

    parser = MarkdownParser("test.md")
    elements = parser.parse_markdown(markdown_text)

    # Check anchor generation
    anchors = {e.id: e.anchor for e in elements}

    assert anchors["R:Test"] == "simple-title"
    assert anchors["C:Component"] == "complex-title-with-symbols-numbers-123"
    assert anchors["D:Data"] == "multiple-spaces-and-hyphens"
    assert anchors["M:Method"] == "unicode-émojis-and-spëcial-chars"


def test_reference_integration():
    """Test integration with reference detection."""
    markdown_text = """# C:WorkspaceManager - Workspace Manager

This component implements I:ProjectDiscovery and uses D:ProjectInfo.
It also calls M:loadWorkspace for initialization.

## References:

- R:CoreRequirement - Main system requirement
- UI:MainWindow - Primary user interface
- C:Helper - Helper component

Additional content with C:AnotherComponent reference.
"""

    parser = MarkdownParser("software-design.md")
    elements = parser.parse_markdown(markdown_text)

    # Find workspace manager
    workspace_mgr = next(e for e in elements if e.id == "C:WorkspaceManager")

    # Should have inline references but not explicit ones (they're in another element)
    expected_inline = {"I:ProjectDiscovery", "D:ProjectInfo", "M:loadWorkspace"}
    inline_refs = set(workspace_mgr.refs)
    assert expected_inline.issubset(inline_refs)

    # Find references section element
    ref_element = next(e for e in elements if "References" in e.title)

    # Should have explicit references plus additional inline reference
    expected_explicit = {"R:CoreRequirement", "UI:MainWindow", "C:Helper", "C:AnotherComponent"}
    explicit_refs = set(ref_element.refs)
    assert expected_explicit.issubset(explicit_refs)


def test_empty_elements():
    """Test handling of elements with no content."""
    markdown_text = """# R:Purpose - Purpose

## C:EmptyComponent - Empty Component

### D:Data - Data with Content

Some actual content here.

#### M:EmptyMethod - Empty Method

##### UI:EmptyUI - Empty UI

"""

    parser = MarkdownParser("test.md")
    elements = parser.parse_markdown(markdown_text)

    # Check empty elements
    empty_component = next(e for e in elements if e.id == "C:EmptyComponent")
    assert empty_component.body_markdown == ""

    empty_method = next(e for e in elements if e.id == "M:EmptyMethod")
    assert empty_method.body_markdown == ""

    empty_ui = next(e for e in elements if e.id == "UI:EmptyUI")
    assert empty_ui.body_markdown == ""

    # Check non-empty element
    data_element = next(e for e in elements if e.id == "D:Data")
    assert "Some actual content here." in data_element.body_markdown


def test_malformed_markdown():
    """Test handling of malformed markdown."""
    malformed_cases = [
        "",  # Empty content
        "# No ID - Just a heading",  # Valid heading without ID
        "## ### Invalid heading level structure",  # Malformed heading
        "Regular text without headings",  # No headings
    ]

    parser = MarkdownParser("test.md")

    # Empty content should return empty list
    elements = parser.parse_markdown(malformed_cases[0])
    assert len(elements) == 0

    # Content without headings should return empty list
    elements = parser.parse_markdown(malformed_cases[3])
    assert len(elements) == 0

    # Heading without ID should still work
    elements = parser.parse_markdown(malformed_cases[1])
    assert len(elements) == 1
    assert elements[0].id.startswith("NoID_")
    assert elements[0].title == "No ID - Just a heading"


def test_validation():
    """Test element validation functionality."""
    markdown_text = """# R:Purpose - Purpose

Content.

## R:Purpose - Duplicate Purpose

Different content.

### C:Component -

Empty title case.

#### T:0001 - Valid Task

Task content.
"""

    parser = MarkdownParser("test.md")
    elements = parser.parse_markdown(markdown_text)

    warnings = parser.validate_parsed_elements(elements)

    # Should have warnings for duplicate ID
    duplicate_warnings = [w for w in warnings if "Duplicate ID" in w]
    assert len(duplicate_warnings) > 0
    assert "R:Purpose" in duplicate_warnings[0]


def test_parsing_statistics():
    """Test parsing statistics generation."""
    markdown_text = """# R:Purpose - Purpose

Content with C:Component reference.

## C:Component1 - Component 1

Content.

### C:Component2 - Component 2

Content with D:Data and M:Method references.

#### D:Data - Data Structure

No content.

##### M:Method - Method

Content.

## T:0001 - Task

Task content.
"""

    parser = MarkdownParser("test.md")
    elements = parser.parse_markdown(markdown_text)

    stats = parser.get_parsing_statistics(elements)

    assert stats['total_elements'] == 6
    assert stats['by_kind']['Requirement'] == 1
    assert stats['by_kind']['Component'] == 2
    assert stats['by_kind']['Data'] == 1
    assert stats['by_kind']['Method'] == 1
    assert stats['by_kind']['Task'] == 1

    assert stats['by_heading_level']['h1'] == 1
    assert stats['by_heading_level']['h2'] == 2
    assert stats['by_heading_level']['h3'] == 1
    assert stats['by_heading_level']['h4'] == 1
    assert stats['by_heading_level']['h5'] == 1

    assert stats['total_references'] > 0
    assert stats['unique_ids'] == 6


def test_convenience_functions():
    """Test convenience functions for parsing."""
    markdown_text = """# R:Purpose - Purpose

Content.

## C:Component - Component

Component content.
"""

    # Test parse_markdown_content
    elements = parse_markdown_content(markdown_text, "software-design.md")
    assert len(elements) == 2
    assert all(e.file == File.SOFTWARE_DESIGN for e in elements)

    # Test parse_markdown_content without file path
    elements = parse_markdown_content(markdown_text)
    assert len(elements) == 2
    # Should default to SOFTWARE_DESIGN
    assert all(e.file == File.SOFTWARE_DESIGN for e in elements)


def test_title_extraction():
    """Test clean title extraction from headings."""
    markdown_text = """# R:Purpose - System Purpose Title

Content.

## C:Component - Multi-Word Component Title

Content.

### Simple Title Without ID

Content.

#### D:Data - Title with: Colons and Symbols!

Content.
"""

    parser = MarkdownParser("test.md")
    elements = parser.parse_markdown(markdown_text)

    # Check title extraction
    titles = {e.id: e.title for e in elements if not e.id.startswith("NoID_")}

    assert titles["R:Purpose"] == "System Purpose Title"
    assert titles["C:Component"] == "Multi-Word Component Title"
    assert titles["D:Data"] == "Title with: Colons and Symbols!"

    # Check element without ID
    no_id_element = next(e for e in elements if e.id.startswith("NoID_"))
    assert no_id_element.title == "Simple Title Without ID"


def test_error_handling():
    """Test error handling for invalid inputs."""
    parser = MarkdownParser("test.md")

    # Test None input
    try:
        parser.parse_markdown(None)
        assert False, "Should raise MarkdownParsingError"
    except (MarkdownParsingError, TypeError):
        pass  # Expected

    # Test invalid file path
    try:
        parser.parse_file("/nonexistent/file.md")
        assert False, "Should raise MarkdownParsingError"
    except MarkdownParsingError as e:
        assert "Failed to read file" in str(e)


def test_complex_markdown_preservation():
    """Test that complex markdown formatting is preserved in body content."""
    markdown_text = """# R:Purpose - Purpose

This has **bold** and *italic* formatting.

- List item 1
- List item 2
  - Nested item

```python
def example():
    return "code"
```

[Link](https://example.com) and `inline code`.

> Blockquote content

| Table | Header |
|-------|--------|
| Cell  | Data   |

## C:Component - Component

Regular content.
"""

    parser = MarkdownParser("test.md")
    elements = parser.parse_markdown(markdown_text)

    purpose = next(e for e in elements if e.id == "R:Purpose")

    # Check that markdown formatting is preserved
    body = purpose.body_markdown
    assert "**bold**" in body
    assert "*italic*" in body
    assert "- List item 1" in body
    assert "```python" in body
    assert "[Link](https://example.com)" in body
    assert "`inline code`" in body
    assert "> Blockquote" in body
    assert "| Table |" in body


if __name__ == "__main__":
    # Run all tests manually
    print("Running markdown parser tests...")

    test_basic_parsing()
    print("✓ Basic parsing")

    test_file_enum_detection()
    print("✓ File enum detection")

    test_kind_detection()
    print("✓ Kind detection")

    test_task_status_detection()
    print("✓ Task status detection")

    test_anchor_generation()
    print("✓ Anchor generation")

    test_reference_integration()
    print("✓ Reference integration")

    test_empty_elements()
    print("✓ Empty elements handling")

    test_malformed_markdown()
    print("✓ Malformed markdown handling")

    test_validation()
    print("✓ Element validation")

    test_parsing_statistics()
    print("✓ Parsing statistics")

    test_convenience_functions()
    print("✓ Convenience functions")

    test_title_extraction()
    print("✓ Title extraction")

    test_error_handling()
    print("✓ Error handling")

    test_complex_markdown_preservation()
    print("✓ Complex markdown preservation")

    print("\nAll tests passed! T:0007 markdown parsing is complete.")