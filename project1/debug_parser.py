"""Debug script to check what the parser is actually generating."""

from markdown_parser import MarkdownParser

markdown_text = """# R:Purpose - System Purpose

This system provides a disciplined workflow for building software.
It references C:WorkspaceManager for workspace operations.

## C:WorkspaceManager - Workspace Management Component

Purpose: Load, validate, and index the workspace.
"""

parser = MarkdownParser("software-design.md")
elements = parser.parse_markdown(markdown_text)

print(f"Found {len(elements)} elements:")
for i, element in enumerate(elements):
    print(f"  {i+1}. ID: '{element.id}' | Kind: {element.kind} | Title: '{element.title}'")
    print(f"      File: {element.file} | Level: {element.heading_level}")
    print(f"      Refs: {element.refs}")
    print()