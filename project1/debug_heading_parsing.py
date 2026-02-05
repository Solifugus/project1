"""Debug what heading text is being extracted."""

from body_extraction import extract_all_bodies
from id_extraction import extract_ids_from_markdown

markdown_text = """# R:Purpose - System Purpose

This system provides a disciplined workflow for building software.
It references C:WorkspaceManager for workspace operations.

## C:WorkspaceManager - Workspace Management Component

Purpose: Load, validate, and index the workspace.
"""

# Extract body ranges using existing body extraction
body_ranges = extract_all_bodies(markdown_text)

print(f"Found {len(body_ranges)} body ranges:")
for i, (heading_boundary, body_range) in enumerate(body_ranges):
    print(f"\n{i+1}. Heading text: '{heading_boundary.heading_text}'")
    print(f"   Heading level: {heading_boundary.heading_level}")
    print(f"   Line number: {heading_boundary.line_number}")

    # Extract ID from heading if present
    extracted_ids = extract_ids_from_markdown(heading_boundary.heading_text)
    print(f"   Extracted IDs: {[id.full_id for id in extracted_ids]}")
    element_id = extracted_ids[0].full_id if extracted_ids else None
    print(f"   Final element ID: {element_id}")

    print(f"   Body content preview: '{body_range.stripped_content[:50]}...'")