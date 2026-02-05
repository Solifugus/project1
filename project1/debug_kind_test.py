"""Debug the kind detection test."""

from markdown_parser import MarkdownParser

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

print(f"Found {len(elements)} elements:")
for element in elements:
    print(f"  ID: '{element.id}' | Kind: {element.kind}")

print("\nExpected IDs:")
expected_ids = ["R:Requirement", "C:Component", "D:Data", "I:Interface", "M:Method", "UI:Window", "T:0001", "TP:0001", "UnknownPrefix:Something"]
for expected_id in expected_ids:
    found = any(e.id == expected_id for e in elements)
    print(f"  {expected_id}: {'✓' if found else '✗'}")