"""
Tests for ID extraction from markdown headings.

This validates T:0004 acceptance criteria.
"""

import tempfile
from pathlib import Path
from id_extraction import (
    MarkdownHeadingParser, IDValidator, ExtractedID, IDPrefix,
    extract_ids_from_markdown, extract_ids_from_file
)


def test_extract_valid_ids():
    """Test extraction of valid IDs from markdown headings."""
    markdown_text = """
# R:Purpose - System Purpose

This describes the purpose.

## C:WorkspaceManager - Workspace Manager Component

Component implementation.

### D:DocElement - Document Element

Data structure definition.

#### I:Parser - Parser Interface

Interface specification.

##### M:ExtractIDs - Extract IDs Method

Method implementation.

###### UI:MainWindow - Main Window

UI component.
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    # Should extract 6 IDs
    assert len(extracted_ids) == 6

    # Check first ID (R:Purpose)
    purpose_id = extracted_ids[0]
    assert purpose_id.full_id == "R:Purpose"
    assert purpose_id.prefix == IDPrefix.REQUIREMENT
    assert purpose_id.suffix == "Purpose"
    assert purpose_id.heading_level == 1
    assert purpose_id.heading_text == "R:Purpose - System Purpose"
    assert purpose_id.line_number == 1  # Second line (0-based)

    # Check component ID (C:WorkspaceManager)
    component_id = extracted_ids[1]
    assert component_id.full_id == "C:WorkspaceManager"
    assert component_id.prefix == IDPrefix.COMPONENT
    assert component_id.suffix == "WorkspaceManager"
    assert component_id.heading_level == 2

    # Check all prefixes are correctly identified
    expected_prefixes = [
        IDPrefix.REQUIREMENT, IDPrefix.COMPONENT, IDPrefix.DATA,
        IDPrefix.INTERFACE, IDPrefix.METHOD, IDPrefix.UI
    ]
    extracted_prefixes = [id.prefix for id in extracted_ids]
    assert extracted_prefixes == expected_prefixes


def test_extract_task_and_test_ids():
    """Test extraction of task and test IDs with numeric suffixes."""
    markdown_text = """
### T:0001 - First Task

Task description.

### T:0042 - Another Task

Another task.

### TP:0001 - First Test

Test description.

### TP:T0042 - Test for Task 42

Test linked to specific task.
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    # Should extract 4 IDs
    assert len(extracted_ids) == 4

    # Check task IDs
    task1 = extracted_ids[0]
    assert task1.full_id == "T:0001"
    assert task1.prefix == IDPrefix.TASK
    assert task1.suffix == "0001"

    task2 = extracted_ids[1]
    assert task2.full_id == "T:0042"
    assert task2.suffix == "0042"

    # Check test IDs
    test1 = extracted_ids[2]
    assert test1.full_id == "TP:0001"
    assert test1.prefix == IDPrefix.TEST
    assert test1.suffix == "0001"

    test2 = extracted_ids[3]
    assert test2.full_id == "TP:T0042"
    assert test2.suffix == "T0042"


def test_heading_levels():
    """Test correct identification of heading levels."""
    markdown_text = """
# R:Level1 - Level 1 Heading
## R:Level2 - Level 2 Heading
### R:Level3 - Level 3 Heading
#### R:Level4 - Level 4 Heading
##### R:Level5 - Level 5 Heading
###### R:Level6 - Level 6 Heading
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    # Should extract 6 IDs with different levels
    assert len(extracted_ids) == 6

    for i, extracted_id in enumerate(extracted_ids, 1):
        assert extracted_id.heading_level == i
        assert extracted_id.full_id == f"R:Level{i}"


def test_invalid_id_formats():
    """Test that invalid ID formats are ignored."""
    markdown_text = """
# Purpose - No ID prefix

This should be ignored.

## X:InvalidPrefix - Invalid prefix

Invalid prefix should be ignored.

### R: - Missing suffix

Missing suffix should be ignored.

#### R:Invalid@Chars - Invalid characters

Invalid characters should be ignored.

##### R:123Invalid - Starting with number

This should be ignored (starts with number).

###### R:Valid - Valid ID

This should be extracted.
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    # Should only extract the valid ID
    assert len(extracted_ids) == 1
    assert extracted_ids[0].full_id == "R:Valid"


def test_id_validator():
    """Test ID format validation."""
    validator = IDValidator()

    # Valid IDs
    assert validator.validate_id_format("R:Purpose") is True
    assert validator.validate_id_format("C:WorkspaceManager") is True
    assert validator.validate_id_format("T:0001") is True
    assert validator.validate_id_format("TP:T0001") is True
    assert validator.validate_id_format("UI:Main-Window") is True
    assert validator.validate_id_format("M:get_data") is True

    # Invalid IDs
    assert validator.validate_id_format("") is False
    assert validator.validate_id_format("R:") is False
    assert validator.validate_id_format("Invalid:Format") is False
    assert validator.validate_id_format("R:123Invalid") is False
    assert validator.validate_id_format("R:Invalid@Chars") is False
    assert validator.validate_id_format("NoPrefix") is False


def test_uniqueness_validation():
    """Test ID uniqueness validation."""
    markdown_text = """
# R:Purpose - First occurrence

Content.

## R:Purpose - Duplicate ID

This should cause an error.
"""

    # Should raise ValueError for duplicate ID
    try:
        extract_ids_from_markdown(markdown_text, validate_uniqueness=True)
        assert False, "Should have raised ValueError for duplicate ID"
    except ValueError as e:
        assert "Duplicate ID found: R:Purpose" in str(e)
        assert "line 6" in str(e)  # Second occurrence is on line 6 (1-based)


def test_uniqueness_disabled():
    """Test that uniqueness validation can be disabled."""
    markdown_text = """
# R:Purpose - First occurrence

Content.

## R:Purpose - Duplicate ID allowed

This should not cause an error.
"""

    # Should not raise error when uniqueness checking is disabled
    extracted_ids = extract_ids_from_markdown(markdown_text, validate_uniqueness=False)

    # Should extract both IDs
    assert len(extracted_ids) == 2
    assert extracted_ids[0].full_id == "R:Purpose"
    assert extracted_ids[1].full_id == "R:Purpose"


def test_mixed_headings_with_and_without_ids():
    """Test parsing headings where some have IDs and some don't."""
    markdown_text = """
# Project Overview

No ID in this heading.

## R:Purpose - System Purpose

This has an ID.

### Implementation Details

No ID here either.

#### C:Parser - Parser Component

Another ID.

##### Usage Notes

No ID.
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    # Should only extract the 2 headings with IDs
    assert len(extracted_ids) == 2
    assert extracted_ids[0].full_id == "R:Purpose"
    assert extracted_ids[1].full_id == "C:Parser"


def test_file_extraction():
    """Test extracting IDs from a file."""
    markdown_content = """
# R:FileTest - File Test

Testing file extraction.

## C:Component - Test Component

Component in file.
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(markdown_content)
        temp_file = f.name

    try:
        extracted_ids = extract_ids_from_file(temp_file)

        assert len(extracted_ids) == 2
        assert extracted_ids[0].full_id == "R:FileTest"
        assert extracted_ids[1].full_id == "C:Component"

    finally:
        # Clean up temp file
        Path(temp_file).unlink()


def test_file_not_found():
    """Test proper error handling for missing files."""
    try:
        extract_ids_from_file("/nonexistent/file.md")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        assert "Markdown file not found" in str(e)


def test_project_uniqueness_validation():
    """Test validating uniqueness across multiple files."""
    # File 1 content
    file1_content = """
# R:Purpose - Purpose

Content.

## C:Parser - Parser

Parser component.
"""

    # File 2 content (with duplicate)
    file2_content = """
# R:Scope - Scope

Different content.

## C:Parser - Parser Duplicate

This is a duplicate of C:Parser from file1.
"""

    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f1:
        f1.write(file1_content)
        temp_file1 = f1.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f2:
        f2.write(file2_content)
        temp_file2 = f2.name

    try:
        parser = MarkdownHeadingParser()
        duplicates = parser.validate_project_uniqueness([temp_file1, temp_file2])

        # Should find C:Parser as duplicate
        assert "C:Parser" in duplicates
        assert len(duplicates["C:Parser"]) == 2
        assert temp_file1 in duplicates["C:Parser"]
        assert temp_file2 in duplicates["C:Parser"]

    finally:
        # Clean up temp files
        Path(temp_file1).unlink()
        Path(temp_file2).unlink()


def test_id_statistics():
    """Test ID statistics generation."""
    markdown_text = """
# R:Purpose - Requirement
## R:Scope - Another Requirement
### C:Parser - Component
#### C:Indexer - Another Component
##### T:0001 - Task
###### TP:0001 - Test
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    parser = MarkdownHeadingParser()
    stats = parser.get_id_statistics(extracted_ids)

    assert stats['total_ids'] == 6

    # Check prefix distribution
    assert stats['by_prefix']['REQUIREMENT'] == 2
    assert stats['by_prefix']['COMPONENT'] == 2
    assert stats['by_prefix']['TASK'] == 1
    assert stats['by_prefix']['TEST'] == 1

    # Check heading level distribution
    assert stats['by_heading_level']['h1'] == 1
    assert stats['by_heading_level']['h2'] == 1
    assert stats['by_heading_level']['h3'] == 1
    assert stats['by_heading_level']['h4'] == 1
    assert stats['by_heading_level']['h5'] == 1
    assert stats['by_heading_level']['h6'] == 1


def test_case_insensitive_prefixes():
    """Test that ID prefixes are case insensitive."""
    markdown_text = """
# r:Purpose - Lowercase prefix
## C:Component - Mixed case
### tp:Test - Lowercase test prefix
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    # Should extract all 3 IDs despite case differences
    assert len(extracted_ids) == 3
    assert extracted_ids[0].full_id == "r:Purpose"  # Preserves original case
    assert extracted_ids[1].full_id == "C:Component"
    assert extracted_ids[2].full_id == "tp:Test"


def test_whitespace_handling():
    """Test proper handling of whitespace around headings."""
    markdown_text = """
#    R:Purpose   - Purpose with extra spaces

Content.

##   C:Component - Component with spaces

More content.
"""

    extracted_ids = extract_ids_from_markdown(markdown_text)

    assert len(extracted_ids) == 2
    assert extracted_ids[0].full_id == "R:Purpose"
    assert extracted_ids[1].full_id == "C:Component"


def test_real_project_file():
    """Test extraction from actual project files."""
    # Test with the actual software-design.md if it exists
    design_file = "/home/solifugus/software-projects/project1/software-design.md"

    try:
        extracted_ids = extract_ids_from_file(design_file, validate_uniqueness=False)

        # Should find some IDs in the real file
        assert len(extracted_ids) > 0

        # Should find expected IDs like R:Purpose, C:WorkspaceManager, D:DocElement
        found_ids = {id.full_id for id in extracted_ids}
        expected_ids = ["R:Purpose", "C:WorkspaceManager", "D:DocElement"]

        for expected_id in expected_ids:
            assert expected_id in found_ids, f"Expected ID {expected_id} not found in real file"

    except FileNotFoundError:
        # If file doesn't exist, that's fine for this test
        pass


if __name__ == "__main__":
    # Run all tests manually
    print("Running ID extraction tests...")

    test_extract_valid_ids()
    print("✓ Valid ID extraction")

    test_extract_task_and_test_ids()
    print("✓ Task and test ID extraction")

    test_heading_levels()
    print("✓ Heading level detection")

    test_invalid_id_formats()
    print("✓ Invalid ID format rejection")

    test_id_validator()
    print("✓ ID format validation")

    test_uniqueness_validation()
    print("✓ Uniqueness validation")

    test_uniqueness_disabled()
    print("✓ Uniqueness validation can be disabled")

    test_mixed_headings_with_and_without_ids()
    print("✓ Mixed headings parsing")

    test_file_extraction()
    print("✓ File extraction")

    test_file_not_found()
    print("✓ File not found error handling")

    test_project_uniqueness_validation()
    print("✓ Project-wide uniqueness validation")

    test_id_statistics()
    print("✓ ID statistics generation")

    test_case_insensitive_prefixes()
    print("✓ Case insensitive prefix handling")

    test_whitespace_handling()
    print("✓ Whitespace handling")

    test_real_project_file()
    print("✓ Real project file parsing")

    print("\nAll tests passed! T:0004 implementation is complete.")