"""Debug malformed markdown test."""

from markdown_parser import MarkdownParser

test_case = "# No ID - Just a heading"

parser = MarkdownParser("test.md")
elements = parser.parse_markdown(test_case)

print(f"Found {len(elements)} elements:")
for element in elements:
    print(f"  ID: '{element.id}'")
    print(f"  Title: '{element.title}'")
    print(f"  Expected: 'Just a heading'")
    print()