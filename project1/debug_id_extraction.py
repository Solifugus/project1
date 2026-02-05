"""Debug ID extraction specifically."""

from id_extraction import extract_ids_from_markdown

test_headings = [
    "# R:Purpose - System Purpose",
    "## C:WorkspaceManager - Workspace Management Component",
    "### D:Data - Data Structure",
    "No ID here"
]

for heading in test_headings:
    print(f"Heading: '{heading}'")
    ids = extract_ids_from_markdown(heading)
    print(f"  Found {len(ids)} IDs:")
    for extracted_id in ids:
        print(f"    {extracted_id.full_id}")
    print()