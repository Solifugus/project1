"""
Tests for markdown body extraction functionality.

This validates T:0005 acceptance criteria.
"""

from body_extraction import (
    MarkdownBodyExtractor, BodyRange, HeadingBoundary, BodyExtractionError,
    extract_body_content, extract_all_bodies
)


def test_simple_body_extraction():
    """Test basic body extraction between headings."""
    markdown_text = """# R:Purpose - System Purpose

This is the purpose of the system.
It spans multiple lines.

## C:Component - Component Description

This is a component description.

### D:Data - Data Structure

Data structure content.
"""

    extractor = MarkdownBodyExtractor()
    body_ranges = extractor.extract_body_ranges(markdown_text)

    # Should extract 3 elements
    assert len(body_ranges) == 3

    # Check first element (R:Purpose)
    purpose_heading, purpose_body = body_ranges[0]
    assert purpose_heading.element_id == "R:Purpose"
    assert purpose_heading.heading_level == 1
    assert purpose_heading.heading_text == "R:Purpose - System Purpose"

    expected_purpose_content = "This is the purpose of the system.\nIt spans multiple lines."
    assert purpose_body.stripped_content == expected_purpose_content
    assert purpose_body.line_count == 4  # Includes empty line + content lines
    assert purpose_body.start_line == 1
    assert purpose_body.end_line == 5  # Stops at next heading

    # Check second element (C:Component)
    component_heading, component_body = body_ranges[1]
    assert component_heading.element_id == "C:Component"
    assert component_heading.heading_level == 2

    expected_component_content = "This is a component description."
    assert component_body.stripped_content == expected_component_content

    # Check third element (D:Data)
    data_heading, data_body = body_ranges[2]
    assert data_heading.element_id == "D:Data"
    assert data_heading.heading_level == 3

    expected_data_content = "Data structure content."
    assert data_body.stripped_content == expected_data_content


def test_heading_hierarchy():
    """Test body extraction respects heading hierarchy."""
    markdown_text = """# R:Main - Main Section

Content for main section.

## C:Sub1 - Sub Section 1

Content for sub 1.

### D:SubSub - Sub-sub Section

Content for sub-sub.

## C:Sub2 - Sub Section 2

Content for sub 2.

# R:Another - Another Main Section

Content for another main.
"""

    body_ranges = extract_all_bodies(markdown_text)

    # Should extract 5 elements
    assert len(body_ranges) == 5

    # Main section should include content until next h1
    main_heading, main_body = body_ranges[0]
    assert main_heading.element_id == "R:Main"
    main_lines = main_body.raw_content.split('\n')
    assert "Content for main section." in main_body.stripped_content
    # Should stop before the second # R:Another
    assert "Content for another main." not in main_body.stripped_content

    # Sub section 1 should include content until next h2 or higher
    sub1_heading, sub1_body = body_ranges[1]
    assert sub1_heading.element_id == "C:Sub1"
    assert "Content for sub 1." in sub1_body.stripped_content
    # Should not include sub-sub content
    assert "Content for sub-sub." not in sub1_body.stripped_content

    # Sub-sub should only include its own content
    subsub_heading, subsub_body = body_ranges[2]
    assert subsub_heading.element_id == "D:SubSub"
    assert subsub_body.stripped_content == "Content for sub-sub."

    # Sub section 2 content
    sub2_heading, sub2_body = body_ranges[3]
    assert sub2_heading.element_id == "C:Sub2"
    assert "Content for sub 2." in sub2_body.stripped_content

    # Another main section
    another_heading, another_body = body_ranges[4]
    assert another_heading.element_id == "R:Another"
    assert another_body.stripped_content == "Content for another main."


def test_empty_bodies():
    """Test handling of headings with no content."""
    markdown_text = """# R:Purpose - Purpose

## C:Component - Component

### D:Data - Data Structure

Some content here.

#### I:Interface - Interface

## C:Another - Another Component

Final content.
"""

    body_ranges = extract_all_bodies(markdown_text)

    # Check empty bodies
    purpose_heading, purpose_body = body_ranges[0]
    assert purpose_heading.element_id == "R:Purpose"
    assert purpose_body.stripped_content == ""
    assert purpose_body.char_count == 0

    component_heading, component_body = body_ranges[1]
    assert component_heading.element_id == "C:Component"
    assert component_body.stripped_content == ""

    # Check non-empty body
    data_heading, data_body = body_ranges[2]
    assert data_heading.element_id == "D:Data"
    assert data_body.stripped_content == "Some content here."

    # Interface should be empty
    interface_heading, interface_body = body_ranges[3]
    assert interface_heading.element_id == "I:Interface"
    assert interface_body.stripped_content == ""

    # Another component should have content
    another_heading, another_body = body_ranges[4]
    assert another_heading.element_id == "C:Another"
    assert another_body.stripped_content == "Final content."


def test_preserve_formatting():
    """Test that formatting and whitespace are preserved."""
    markdown_text = """# R:Purpose - Purpose

This is **bold** text and *italic* text.

- List item 1
- List item 2
  - Nested item

```python
def example():
    return "code"
```

    Indented paragraph.

## C:Component - Component

Normal paragraph.
"""

    body_ranges = extract_all_bodies(markdown_text)

    purpose_heading, purpose_body = body_ranges[0]

    # Check that raw content preserves everything
    raw_content = purpose_body.raw_content

    # Should preserve markdown formatting
    assert "**bold**" in raw_content
    assert "*italic*" in raw_content

    # Should preserve list formatting
    assert "- List item 1" in raw_content
    assert "- List item 2" in raw_content
    assert "  - Nested item" in raw_content

    # Should preserve code blocks
    assert "```python" in raw_content
    assert 'def example():' in raw_content
    assert '    return "code"' in raw_content
    assert "```" in raw_content

    # Should preserve indentation
    assert "    Indented paragraph." in raw_content


def test_byte_and_line_positions():
    """Test accurate byte and line position tracking."""
    markdown_text = """# R:Purpose - Purpose

First line of content.
Second line of content.

## C:Component - Component

Component content.
"""

    body_ranges = extract_all_bodies(markdown_text)

    purpose_heading, purpose_body = body_ranges[0]

    # Check line positions
    assert purpose_body.start_line == 1  # Line after heading
    assert purpose_body.end_line == 5    # Before next heading

    # Check byte positions are reasonable
    assert purpose_body.start_byte > 0
    assert purpose_body.end_byte > purpose_body.start_byte

    # Verify byte positions by extracting content manually
    text_bytes = markdown_text.encode('utf-8')
    extracted_bytes = text_bytes[purpose_body.start_byte:purpose_body.end_byte]
    extracted_text = extracted_bytes.decode('utf-8')

    # The extracted text should match the raw content
    assert extracted_text.strip() == purpose_body.raw_content.strip()


def test_single_body_extraction():
    """Test extracting body for a specific heading line."""
    markdown_text = """# R:Purpose - Purpose

Purpose content.

## C:Component - Component

Component content.

## C:Another - Another

Another content.
"""

    # Extract body for the component heading (line 4)
    component_body = extract_body_content(markdown_text, 4)

    assert component_body.stripped_content == "Component content."
    assert component_body.start_line == 5
    assert component_body.end_line == 8  # Before next heading


def test_invalid_heading_line():
    """Test error handling for invalid heading line."""
    markdown_text = """# R:Purpose - Purpose

Content.
"""

    try:
        extract_body_content(markdown_text, 5)  # Non-existent line
        assert False, "Should have raised BodyExtractionError"
    except BodyExtractionError as e:
        assert "No heading found at line 5" in str(e)


def test_heading_at_end_of_document():
    """Test handling of heading at the very end of document."""
    markdown_text = """# R:Purpose - Purpose

Some content.

## C:Component - Component"""

    body_ranges = extract_all_bodies(markdown_text)

    # Component heading at end should have empty body
    component_heading, component_body = body_ranges[1]
    assert component_heading.element_id == "C:Component"
    assert component_body.stripped_content == ""
    assert component_body.line_count == 0


def test_content_update():
    """Test updating body content and reconstructing markdown."""
    markdown_text = """# R:Purpose - Purpose

Old content here.

## C:Component - Component

Component content.
"""

    extractor = MarkdownBodyExtractor()

    # Update purpose content
    new_content = "New purpose content.\nWith multiple lines."
    updated_text = extractor.extract_and_update_content(markdown_text, 0, new_content)

    # Check that content was updated
    assert "New purpose content." in updated_text
    assert "With multiple lines." in updated_text
    assert "Old content here." not in updated_text

    # Check that other content remained unchanged
    assert "Component content." in updated_text
    assert "## C:Component - Component" in updated_text


def test_headings_without_ids():
    """Test handling of headings that don't have IDs."""
    markdown_text = """# Introduction

This is an introduction.

## R:Purpose - Purpose

Purpose content.

### Implementation Notes

Some implementation notes.

## C:Component - Component

Component content.
"""

    body_ranges = extract_all_bodies(markdown_text)

    # Should extract all headings, even those without IDs
    assert len(body_ranges) == 4

    # Introduction heading (no ID)
    intro_heading, intro_body = body_ranges[0]
    assert intro_heading.element_id is None
    assert intro_heading.heading_text == "Introduction"
    assert "This is an introduction." in intro_body.stripped_content

    # Implementation notes (no ID)
    notes_heading, notes_body = body_ranges[2]
    assert notes_heading.element_id is None
    assert notes_heading.heading_text == "Implementation Notes"
    assert "Some implementation notes." in notes_body.stripped_content


def test_range_validation():
    """Test body range validation functionality."""
    markdown_text = """# R:Purpose - Purpose

Content.

## C:Component - Component

Component content.
"""

    extractor = MarkdownBodyExtractor()
    body_ranges = extractor.extract_body_ranges(markdown_text)

    # Validate ranges
    warnings = extractor.validate_ranges(body_ranges)

    # Should have no warnings for valid ranges
    assert len(warnings) == 0


def test_unicode_content():
    """Test handling of Unicode content and proper byte calculation."""
    markdown_text = """# R:Purpose - Purpose

Content with émojis 🎉 and unicôde characters.
中文内容 and العربية.

## C:Component - Component

More unicode: café, résumé, naïve.
"""

    body_ranges = extract_all_bodies(markdown_text)

    purpose_heading, purpose_body = body_ranges[0]

    # Should handle Unicode properly
    assert "émojis 🎉" in purpose_body.stripped_content
    assert "unicôde" in purpose_body.stripped_content
    assert "中文内容" in purpose_body.stripped_content
    assert "العربية" in purpose_body.stripped_content

    # Byte positions should be calculated correctly for Unicode
    assert purpose_body.start_byte > 0
    assert purpose_body.end_byte > purpose_body.start_byte


def test_element_summary():
    """Test element summary generation."""
    markdown_text = """# R:Purpose - System Purpose

This is the purpose.
It has multiple lines.

## C:Component - Component

Component description.
"""

    extractor = MarkdownBodyExtractor()
    body_ranges = extractor.extract_body_ranges(markdown_text)

    purpose_heading, purpose_body = body_ranges[0]
    summary = extractor.get_element_summary(purpose_heading, purpose_body)

    assert summary['id'] == 'R:Purpose'
    assert summary['heading_text'] == 'R:Purpose - System Purpose'
    assert summary['heading_level'] == 1
    assert summary['content_lines'] > 0
    assert summary['content_chars'] > 0
    assert summary['has_content'] is True


def test_multiline_code_blocks():
    """Test handling of complex markdown with code blocks."""
    markdown_text = """# R:Purpose - Purpose

Here's some code:

```python
def complex_function():
    \"\"\"
    Multi-line docstring
    with various content.
    \"\"\"
    for i in range(10):
        print(f"Line {i}")
    return True
```

And some more text.

## C:Component - Component

Component text.
"""

    body_ranges = extract_all_bodies(markdown_text)

    purpose_heading, purpose_body = body_ranges[0]

    # Should preserve the entire code block
    assert "```python" in purpose_body.raw_content
    assert "def complex_function():" in purpose_body.raw_content
    assert '"""' in purpose_body.raw_content
    assert "for i in range(10):" in purpose_body.raw_content
    assert "```" in purpose_body.raw_content

    # Should also preserve text after code block
    assert "And some more text." in purpose_body.raw_content


if __name__ == "__main__":
    # Run all tests manually
    print("Running body extraction tests...")

    test_simple_body_extraction()
    print("✓ Simple body extraction")

    test_heading_hierarchy()
    print("✓ Heading hierarchy handling")

    test_empty_bodies()
    print("✓ Empty body handling")

    test_preserve_formatting()
    print("✓ Formatting preservation")

    test_byte_and_line_positions()
    print("✓ Position tracking")

    test_single_body_extraction()
    print("✓ Single body extraction")

    test_invalid_heading_line()
    print("✓ Error handling")

    test_heading_at_end_of_document()
    print("✓ End-of-document handling")

    test_content_update()
    print("✓ Content updating")

    test_headings_without_ids()
    print("✓ Headings without IDs")

    test_range_validation()
    print("✓ Range validation")

    test_unicode_content()
    print("✓ Unicode handling")

    test_element_summary()
    print("✓ Element summary")

    test_multiline_code_blocks()
    print("✓ Complex markdown handling")

    print("\nAll tests passed! T:0005 implementation is complete.")