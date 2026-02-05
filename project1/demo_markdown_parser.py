"""
Demo showing full markdown parsing with real Project1 files.
"""

from markdown_parser import MarkdownParser, parse_markdown_file
from workspace_paths import get_artifact_path, ArtifactType
import json


def main():
    """Demonstrate complete markdown parsing with real Project1 files."""
    print("Markdown Parser Demo - Complete Document Processing")
    print("=" * 54)

    # Test files to parse
    project_name = "project1"
    test_files = [
        ("software-design.md", ArtifactType.SOFTWARE_DESIGN),
        ("development-plan.md", ArtifactType.DEVELOPMENT_PLAN),
        ("test-plan.md", ArtifactType.TEST_PLAN),
    ]

    all_elements = []

    for file_desc, artifact_type in test_files:
        print(f"\n{file_desc.upper()}")
        print("-" * len(file_desc))

        file_path = get_artifact_path(project_name, artifact_type)

        if not file_path.exists():
            print(f"  File not found: {file_path}")
            continue

        try:
            # Parse the entire file into DocElements
            parser = MarkdownParser(str(file_path))
            elements = parser.parse_file(str(file_path))
            all_elements.extend(elements)

            if not elements:
                print("  No elements found in this file.")
                continue

            print(f"  Parsed {len(elements)} elements:")
            print()

            # Show first few elements as examples
            for i, element in enumerate(elements[:5]):
                print(f"    {i+1}. {element.id} ({element.kind.value})")
                print(f"       Title: {element.title}")
                print(f"       Level: h{element.heading_level}")
                print(f"       File: {element.file.value}")
                print(f"       Anchor: {element.anchor}")

                if element.refs:
                    print(f"       References: {', '.join(element.refs[:5])}")
                    if len(element.refs) > 5:
                        print(f"                   ... and {len(element.refs) - 5} more")

                if element.status:
                    print(f"       Status: {element.status.value}")

                # Show content preview
                content_preview = element.body_markdown.replace('\n', ' ')[:80]
                if content_preview:
                    if len(element.body_markdown) > 80:
                        content_preview += "..."
                    print(f"       Content: {content_preview}")

                print()

            if len(elements) > 5:
                print(f"    ... and {len(elements) - 5} more elements")
                print()

            # Get parsing statistics for this file
            stats = parser.get_parsing_statistics(elements)
            print(f"  File Statistics:")
            print(f"    Total elements: {stats['total_elements']}")
            print(f"    Elements with content: {stats['elements_with_content']}")
            print(f"    Total references: {stats['total_references']}")
            print(f"    Average refs per element: {stats['average_references_per_element']}")

            print(f"    By kind:")
            for kind, count in sorted(stats['by_kind'].items()):
                print(f"      {kind}: {count}")

            # Validate elements
            warnings = parser.validate_parsed_elements(elements)
            if warnings:
                print(f"    Validation warnings ({len(warnings)}):")
                for warning in warnings[:3]:
                    print(f"      - {warning}")
                if len(warnings) > 3:
                    print(f"      ... and {len(warnings) - 3} more warnings")
            else:
                print(f"    ✓ No validation warnings")

        except Exception as e:
            print(f"  Error processing file: {e}")

    # Overall analysis
    print(f"\nOVERALL ANALYSIS")
    print("-" * 16)

    if not all_elements:
        print("No elements found across all files.")
        return

    print(f"Total elements parsed: {len(all_elements)}")

    # Combined statistics
    combined_parser = MarkdownParser()
    combined_stats = combined_parser.get_parsing_statistics(all_elements)

    print(f"\nCombined Statistics:")
    print(f"  Total elements: {combined_stats['total_elements']}")
    print(f"  Unique IDs: {combined_stats['unique_ids']}")
    print(f"  Elements with content: {combined_stats['elements_with_content']}")
    print(f"  Elements without content: {combined_stats['elements_without_content']}")
    print(f"  Total references: {combined_stats['total_references']}")
    print(f"  Average references per element: {combined_stats['average_references_per_element']}")

    print(f"\n  Distribution by Kind:")
    for kind, count in sorted(combined_stats['by_kind'].items()):
        percentage = (count / len(all_elements)) * 100
        print(f"    {kind:<12}: {count:>3} elements ({percentage:>5.1f}%)")

    print(f"\n  Distribution by Heading Level:")
    for level, count in sorted(combined_stats['by_heading_level'].items()):
        percentage = (count / len(all_elements)) * 100
        print(f"    {level:<4}: {count:>3} elements ({percentage:>5.1f}%)")

    print(f"\n  Distribution by File:")
    file_counts = {}
    for element in all_elements:
        file_name = element.file.value
        file_counts[file_name] = file_counts.get(file_name, 0) + 1

    for file_name, count in sorted(file_counts.items()):
        percentage = (count / len(all_elements)) * 100
        print(f"    {file_name:<20}: {count:>3} elements ({percentage:>5.1f}%)")

    # Find most referenced elements by analyzing all refs
    ref_counts = {}
    for element in all_elements:
        for ref in element.refs:
            ref_counts[ref] = ref_counts.get(ref, 0) + 1

    if ref_counts:
        print(f"\n  Most Referenced Elements:")
        top_refs = sorted(ref_counts.items(), key=lambda x: x[1], reverse=True)
        for ref_id, count in top_refs[:10]:
            print(f"    {ref_id:<25}: {count:>2} references")

    # Show examples of different element types
    print(f"\nELEMENT TYPE EXAMPLES")
    print("-" * 21)

    example_kinds = [
        ("Requirement", "R:"),
        ("Component", "C:"),
        ("Data", "D:"),
        ("Task", "T:"),
        ("Test", "TP:"),
    ]

    for kind_name, prefix in example_kinds:
        examples = [e for e in all_elements if e.id.startswith(prefix)]
        if examples:
            example = examples[0]
            print(f"\n{kind_name} Example: {example.id}")
            print(f"  Title: {example.title}")
            print(f"  File: {example.file.value}")
            print(f"  Level: h{example.heading_level}")
            if example.refs:
                print(f"  References: {', '.join(example.refs[:3])}")
                if len(example.refs) > 3:
                    print(f"              ... and {len(example.refs) - 3} more")
            if example.status:
                print(f"  Status: {example.status.value}")

    # Demonstrate integration functionality
    print(f"\nINTEGRATION DEMONSTRATION")
    print("-" * 25)

    demo_markdown = """# R:MainPurpose - Main System Purpose

The Project1 system provides a disciplined workflow for building software
with AI by keeping design intent explicit and decomposing work into atomic tasks.

Key benefits:
- Explicit design documentation through C:MarkdownParser integration
- Atomic task decomposition via T:TaskDecomposition workflow
- Fresh session execution capability using I:SessionInterface

## C:WorkspaceManager - Workspace Management Component

Purpose: Load, validate, and index the workspace and projects.

Responsibilities:
- Discover projects in the workspace (implements I:ProjectDiscovery)
- Ensure required files exist using M:validateStructure
- Provide paths, metadata, and indexing state
- Monitor markdown files for external changes (see D:FileSystemEvent)

### M:loadWorkspace - Load Workspace Method

```python
def load_workspace(workspace_path: str) -> WorkspaceInfo:
    \"""Load and validate workspace structure.\"""
    # Implementation details...
    pass
```

## T:0001 - Define DocElement data structure

**Goal**: Implement the core DocElement struct/class as specified in D:DocElement

This task is now completed and ready for use.

## TP:0001 - Test DocElement creation

Verify DocElement can be created with all required fields.
"""

    print("Parsing demonstration markdown:")
    demo_elements = parse_markdown_file("temp_demo.md") if False else []

    # Parse directly from content
    demo_parser = MarkdownParser("software-design.md")
    demo_elements = demo_parser.parse_markdown(demo_markdown)

    print(f"Found {len(demo_elements)} elements:")

    for i, element in enumerate(demo_elements, 1):
        kind_icon = {
            "Requirement": "📋", "Component": "🧩", "Data": "📊",
            "Method": "⚙️", "Task": "✅", "Test": "🧪", "Other": "📄"
        }.get(element.kind.value, "❓")

        status_marker = ""
        if element.status:
            status_marker = f" [{element.status.value}]"

        print(f"  {i}. {kind_icon} {element.id}{status_marker}")
        print(f"     {element.title}")
        if element.refs:
            print(f"     → References: {', '.join(element.refs[:4])}")
            if len(element.refs) > 4:
                print(f"                   ... and {len(element.refs) - 4} more")

    # Show JSON serialization capability
    print(f"\nSERIALIZATION EXAMPLE")
    print("-" * 20)

    if demo_elements:
        example_element = demo_elements[0]
        print(f"Element {example_element.id} as JSON:")
        json_str = example_element.to_json()
        print(json_str[:200] + "..." if len(json_str) > 200 else json_str)

    print()
    print("✓ Full markdown file parsing")
    print("✓ ID extraction and validation")
    print("✓ Body content extraction with formatting preservation")
    print("✓ Reference detection (inline and explicit)")
    print("✓ DocElement creation with all fields")
    print("✓ Kind classification from ID prefixes")
    print("✓ File enum detection from file paths")
    print("✓ Task status extraction from content")
    print("✓ URL anchor generation")
    print("✓ Parsing statistics and validation")
    print("✓ Error handling and graceful degradation")
    print("✓ JSON serialization/deserialization")


if __name__ == "__main__":
    main()