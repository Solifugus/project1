"""Debug title extraction logic."""

from markdown_parser import MarkdownParser

test_cases = [
    ("R:Purpose - System Purpose", True, "System Purpose"),
    ("No ID - Just a heading", False, "Just a heading"),
    ("C:Component - Component Title", True, "Component Title"),
    ("Simple Title", False, "Simple Title"),
]

parser = MarkdownParser("test.md")

for heading_text, has_valid_id, expected in test_cases:
    result = parser._extract_title_from_heading(heading_text, has_valid_id)
    print(f"Input: '{heading_text}'")
    print(f"Has ID: {has_valid_id}")
    print(f"Expected: '{expected}'")
    print(f"Got: '{result}'")
    print(f"Match: {'✓' if result == expected else '✗'}")
    print()