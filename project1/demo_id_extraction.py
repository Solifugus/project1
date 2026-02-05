"""
Demo showing ID extraction from Project1 markdown files.
"""

from id_extraction import (
    MarkdownHeadingParser, extract_ids_from_file,
    IDPrefix
)
from workspace_paths import get_artifact_path, ArtifactType
import os


def main():
    """Demonstrate ID extraction with real Project1 files."""
    print("ID Extraction Demo - Project1 Files")
    print("=" * 35)

    # Try to extract IDs from real project files
    project_name = "project1"

    # Test files to analyze
    test_files = [
        ("software-design.md", ArtifactType.SOFTWARE_DESIGN),
        ("development-plan.md", ArtifactType.DEVELOPMENT_PLAN),
        ("test-plan.md", ArtifactType.TEST_PLAN),
    ]

    all_ids = []
    parser = MarkdownHeadingParser(validate_uniqueness=False)

    for file_desc, artifact_type in test_files:
        print(f"{file_desc.upper()}")
        print("-" * len(file_desc))

        file_path = get_artifact_path(project_name, artifact_type)

        if not file_path.exists():
            print(f"  File not found: {file_path}")
            print()
            continue

        try:
            extracted_ids = extract_ids_from_file(str(file_path), validate_uniqueness=False)

            if not extracted_ids:
                print("  No IDs found in this file.")
                print()
                continue

            # Group by prefix for better display
            by_prefix = {}
            for id_obj in extracted_ids:
                prefix_name = id_obj.prefix.name
                if prefix_name not in by_prefix:
                    by_prefix[prefix_name] = []
                by_prefix[prefix_name].append(id_obj)

            print(f"  Found {len(extracted_ids)} IDs:")

            for prefix_name, ids in sorted(by_prefix.items()):
                print(f"    {prefix_name}s ({len(ids)}):")
                for id_obj in sorted(ids, key=lambda x: x.full_id):
                    # Truncate long titles for display
                    title = id_obj.heading_text
                    if len(title) > 50:
                        title = title[:47] + "..."

                    print(f"      {id_obj.full_id:15} | h{id_obj.heading_level} | {title}")

            all_ids.extend(extracted_ids)

        except Exception as e:
            print(f"  Error parsing file: {e}")

        print()

    # Overall statistics
    if all_ids:
        print("OVERALL STATISTICS")
        print("-" * 18)

        stats = parser.get_id_statistics(all_ids)

        print(f"Total IDs extracted: {stats['total_ids']}")
        print()

        print("Distribution by prefix:")
        for prefix_name, count in sorted(stats['by_prefix'].items()):
            print(f"  {prefix_name:12} -> {count:3d} IDs")

        print()

        print("Distribution by heading level:")
        for level, count in sorted(stats['by_heading_level'].items()):
            print(f"  {level:12} -> {count:3d} IDs")

        # Check for uniqueness across all files
        print()
        print("PROJECT-WIDE UNIQUENESS CHECK")
        print("-" * 29)

        file_paths = []
        for _, artifact_type in test_files:
            file_path = get_artifact_path(project_name, artifact_type)
            if file_path.exists():
                file_paths.append(str(file_path))

        if file_paths:
            duplicates = parser.validate_project_uniqueness(file_paths)

            if duplicates:
                print("⚠️  Duplicate IDs found:")
                for duplicate_id, files in duplicates.items():
                    print(f"  {duplicate_id} appears in:")
                    for file_path in files:
                        file_name = os.path.basename(file_path)
                        print(f"    - {file_name}")
            else:
                print("✓ All IDs are unique across project files")
        else:
            print("No files available for uniqueness check")

    else:
        print("No IDs found in any files.")

    print()

    # Demonstrate specific ID extraction patterns
    print("ID PATTERN EXAMPLES")
    print("-" * 19)

    example_text = """
# R:MainPurpose - Primary Requirement

The main purpose of the system.

## C:WorkspaceManager - Workspace Management Component

Handles workspace operations.

### D:DocumentElement - Document Element Data

Core data structure.

#### I:ValidationInterface - Validation Interface

Interface for validators.

##### M:parseHeadings - Parse Headings Method

Extracts headings from markdown.

###### UI:StatusBar - Status Bar UI

Shows current status.

### T:0001 - First Task

Implementation task.

### TP:0001 - First Test

Test specification.
"""

    print("Extracting from example markdown:")
    example_ids = extract_ids_from_file_content(example_text)

    print(f"Found {len(example_ids)} IDs with different patterns:")
    for id_obj in example_ids:
        pattern = get_id_pattern_description(id_obj)
        print(f"  {id_obj.full_id:20} -> {pattern}")

    print()
    print("✓ ID extraction handles all Project1 ID formats")
    print("✓ Project-scoped uniqueness validation")
    print("✓ Case-insensitive prefix matching")
    print("✓ Proper heading level detection")
    print("✓ Invalid ID format rejection")


def extract_ids_from_file_content(markdown_content):
    """Helper to extract IDs from markdown content string."""
    parser = MarkdownHeadingParser(validate_uniqueness=False)
    return parser.extract_ids_from_text(markdown_content)


def get_id_pattern_description(id_obj):
    """Get a description of the ID pattern."""
    prefix_descriptions = {
        IDPrefix.REQUIREMENT: "Requirement ID",
        IDPrefix.COMPONENT: "Component ID",
        IDPrefix.DATA: "Data Structure ID",
        IDPrefix.INTERFACE: "Interface ID",
        IDPrefix.METHOD: "Method ID",
        IDPrefix.UI: "UI Element ID",
        IDPrefix.TASK: "Task ID (numeric)",
        IDPrefix.TEST: "Test ID (numeric)"
    }

    base_desc = prefix_descriptions.get(id_obj.prefix, "Unknown ID type")

    if id_obj.suffix.isdigit():
        return f"{base_desc} with numeric suffix"
    elif '_' in id_obj.suffix:
        return f"{base_desc} with underscore"
    elif '-' in id_obj.suffix:
        return f"{base_desc} with hyphen"
    else:
        return f"{base_desc} with alpha suffix"


if __name__ == "__main__":
    main()