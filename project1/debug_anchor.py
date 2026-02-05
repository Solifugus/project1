"""Debug anchor generation."""

from markdown_parser import MarkdownParser

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

for element in elements:
    print(f"ID: {element.id}")
    print(f"Title: '{element.title}'")
    print(f"Anchor: '{element.anchor}'")
    print()