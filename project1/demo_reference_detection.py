"""
Demo showing reference detection from Project1 markdown files.
"""

from reference_detection import ReferenceDetector, detect_references, extract_reference_ids
from workspace_paths import get_artifact_path, ArtifactType
import os


def main():
    """Demonstrate reference detection with real Project1 files."""
    print("Reference Detection Demo - Project1 Files")
    print("=" * 42)

    # Test files to analyze
    project_name = "project1"
    test_files = [
        ("software-design.md", ArtifactType.SOFTWARE_DESIGN),
        ("development-plan.md", ArtifactType.DEVELOPMENT_PLAN),
        ("test-plan.md", ArtifactType.TEST_PLAN),
    ]

    detector = ReferenceDetector()
    all_references = []

    for file_desc, artifact_type in test_files:
        print(f"\n{file_desc.upper()}")
        print("-" * len(file_desc))

        file_path = get_artifact_path(project_name, artifact_type)

        if not file_path.exists():
            print(f"  File not found: {file_path}")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract references from the body content
            # For demo purposes, we'll analyze the full file content
            references = detector.detect_references_in_text(content)
            all_references.extend(references)

            if not references:
                print("  No references found in this file.")
                continue

            print(f"  Found {len(references)} references:")

            # Group by type
            inline_refs = [r for r in references if r.reference_type == "inline"]
            explicit_refs = [r for r in references if r.reference_type == "explicit"]

            if inline_refs:
                print(f"\n    Inline References ({len(inline_refs)}):")
                for ref in inline_refs[:10]:  # Show first 10
                    print(f"      {ref.target_id}")
                    print(f"        Context: {ref.context[:60]}...")
                    print(f"        Line: {ref.line_number + 1}")

                if len(inline_refs) > 10:
                    print(f"      ... and {len(inline_refs) - 10} more inline references")

            if explicit_refs:
                print(f"\n    Explicit References ({len(explicit_refs)}):")
                for ref in explicit_refs[:5]:  # Show first 5
                    print(f"      {ref.target_id}")
                    print(f"        Context: {ref.context}")
                    print(f"        Line: {ref.line_number + 1}")

                if len(explicit_refs) > 5:
                    print(f"      ... and {len(explicit_refs) - 5} more explicit references")

        except Exception as e:
            print(f"  Error processing file: {e}")

    # Overall statistics
    print(f"\nOVERALL ANALYSIS")
    print("-" * 16)

    if not all_references:
        print("No references found across all files.")
        return

    stats = detector.get_reference_statistics(all_references)

    print(f"  Total references found: {stats['total_references']}")
    print(f"  Unique targets: {stats['unique_targets']}")
    print(f"  Inline references: {stats['inline_references']}")
    print(f"  Explicit references: {stats['explicit_references']}")

    print(f"\n  References by type:")
    for prefix, count in sorted(stats['by_prefix'].items()):
        print(f"    {prefix:<4} {count:>3} references")

    # Find common reference patterns
    patterns = detector.find_reference_patterns(all_references)

    if patterns:
        print(f"\n  Common reference patterns:")
        for pattern_name, examples in patterns.items():
            if examples:
                print(f"    {pattern_name}: {len(examples)} occurrences")
                for example in examples[:2]:  # Show up to 2 examples
                    print(f"      \"{example[:50]}...\"")

    # Show most referenced elements
    grouped = detector.group_references_by_target(all_references)
    most_referenced = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

    print(f"\n  Most referenced elements:")
    for target_id, refs in most_referenced[:10]:
        print(f"    {target_id}: {len(refs)} references")

    # Demonstrate functionality
    print(f"\nFUNCTIONALITY DEMONSTRATION")
    print("-" * 27)

    demo_markdown = """# C:WorkspaceManager - Workspace Management Component

Purpose: Load, validate, and index the workspace and projects as specified in R:CoreWorkflow.

Responsibilities:
- Discover projects in the workspace (implements I:ProjectDiscovery)
- Ensure required files exist using M:validateStructure
- Provide paths, metadata, and indexing state
- Monitor markdown files for external changes (see D:FileSystemEvent)

The component integrates with C:MarkdownParser and C:Indexer.

## References:

- R:CoreWorkflow - Main workflow specification
- I:ProjectDiscovery - Project discovery interface
- M:validateStructure - Structure validation method
- D:FileSystemEvent - File change event data
- C:MarkdownParser - Markdown parsing component
- C:Indexer - Document indexing component

## Implementation Notes

Based on D:WorkspaceStructure design, this component calls M:loadWorkspace
to initialize the workspace state. It also uses C:PrivilegedHelper for
file system operations that require elevated permissions.
"""

    print("Analyzing demonstration markdown:")
    demo_references = detect_references(demo_markdown)

    print(f"\nFound {len(demo_references)} references:")

    # Show inline vs explicit breakdown
    inline_count = len([r for r in demo_references if r.reference_type == "inline"])
    explicit_count = len([r for r in demo_references if r.reference_type == "explicit"])

    print(f"  Inline: {inline_count}")
    print(f"  Explicit: {explicit_count}")

    print(f"\nReference details:")
    for i, ref in enumerate(demo_references, 1):
        ref_type_marker = "→" if ref.reference_type == "inline" else "•"
        print(f"  {i:>2}. {ref_type_marker} {ref.target_id} ({ref.reference_type})")
        print(f"       Line {ref.line_number + 1}: {ref.context[:60]}...")

    # Demonstrate validation (assuming we know some IDs)
    known_ids = {
        "R:CoreWorkflow", "C:WorkspaceManager", "C:MarkdownParser",
        "I:ProjectDiscovery", "M:validateStructure", "D:FileSystemEvent"
    }

    detector_with_validation = ReferenceDetector(known_ids)
    demo_references_with_validation = detector_with_validation.detect_references_in_text(demo_markdown)
    validation_result = detector_with_validation.validate_references(demo_references_with_validation)

    print(f"\nValidation results (against {len(known_ids)} known IDs):")
    print(f"  Valid references: {len(validation_result['valid'])}")
    print(f"  Invalid references: {len(validation_result['invalid'])}")

    if validation_result['invalid']:
        print(f"  Invalid IDs: {', '.join(validation_result['invalid'])}")

    # Pattern analysis
    demo_patterns = detector_with_validation.find_reference_patterns(demo_references_with_validation)

    if demo_patterns:
        print(f"\nPattern analysis:")
        for pattern, examples in demo_patterns.items():
            if examples:
                print(f"  {pattern}: {examples[0][:50]}...")

    # Demonstrate convenience function
    print(f"\nCONVENIENCE FUNCTION DEMO")
    print("-" * 25)

    simple_text = "This component implements C:WorkspaceManager and uses D:ProjectInfo for data storage."

    simple_refs = extract_reference_ids(simple_text)
    print(f"extract_reference_ids() found: {simple_refs}")

    detailed_refs = detect_references(simple_text)
    print(f"detect_references() found {len(detailed_refs)} Reference objects:")
    for ref in detailed_refs:
        print(f"  {ref.target_id} at position {ref.position_in_line} (context: '{ref.context}')")

    print()
    print("✓ Inline reference detection (within body text)")
    print("✓ Explicit reference detection (References: sections)")
    print("✓ Reference type classification and deduplication")
    print("✓ Context extraction with position tracking")
    print("✓ Reference validation against known IDs")
    print("✓ Statistical analysis and pattern recognition")
    print("✓ Convenience functions for common operations")
    print("✓ Case-insensitive ID matching")
    print("✓ Support for all ID prefixes (R:, C:, D:, I:, M:, UI:, T:, TP:)")


if __name__ == "__main__":
    main()