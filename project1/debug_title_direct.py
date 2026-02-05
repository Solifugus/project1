"""Debug title extraction function directly."""

from markdown_parser import MarkdownParser

parser = MarkdownParser("test.md")

test_heading = "No ID - Just a heading"
result = parser._extract_title_from_heading(test_heading)

print(f"Input: '{test_heading}'")
print(f"Result: '{result}'")

# Test the regex directly
import re
title = re.sub(r'^#+\s*', '', test_heading).strip()
print(f"After # removal: '{title}'")

id_match = re.match(r'^([A-Za-z]+:\w+)\s*-\s*(.+)$', title)
print(f"Regex match: {id_match}")

if id_match:
    print(f"Group 1 (prefix): '{id_match.group(1)}'")
    print(f"Group 2 (title): '{id_match.group(2)}'")
else:
    print("No regex match")