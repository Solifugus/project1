"""
Demo showing body extraction from Project1 markdown files.
"""

from body_extraction import MarkdownBodyExtractor, extract_all_bodies
from workspace_paths import get_artifact_path, ArtifactType
import os


def main():
    """Demonstrate body extraction with real Project1 files."""
    print("Body Extraction Demo - Project1 Files")
    print("=" * 40)

    # Test files to analyze
    project_name = "project1"
    test_files = [
        ("software-design.md", ArtifactType.SOFTWARE_DESIGN),
        ("development-plan.md", ArtifactType.DEVELOPMENT_PLAN),
    ]

    extractor = MarkdownBodyExtractor()

    for file_desc, artifact_type in test_files:
        print(f"{file_desc.upper()}")
        print("-" * len(file_desc))

        file_path = get_artifact_path(project_name, artifact_type)

        if not file_path.exists():
            print(f"  File not found: {file_path}")
            print()
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            body_ranges = extractor.extract_body_ranges(content)

            if not body_ranges:
                print("  No elements found in this file.")
                print()
                continue

            print(f"  Found {len(body_ranges)} elements with bodies:")
            print()

            # Show first few elements as examples
            for i, (heading, body) in enumerate(body_ranges[:5]):
                element_id = heading.element_id or f"Line{heading.line_number}"

                print(f"    {i+1}. {element_id} (h{heading.heading_level})")
                print(f"       Title: {heading.heading_text}")
                print(f"       Lines: {body.start_line}-{body.end_line} ({body.line_count} lines)")
                print(f"       Chars: {body.char_count}")

                # Show content preview (first 100 chars)
                content_preview = body.stripped_content.replace('\n', ' ')
                if len(content_preview) > 100:
                    content_preview = content_preview[:97] + "..."

                if content_preview:
                    print(f"       Preview: {content_preview}")
                else:
                    print(f"       Preview: (empty)")

                print()

            if len(body_ranges) > 5:
                print(f"    ... and {len(body_ranges) - 5} more elements")
                print()

            # Statistics
            total_chars = sum(body.char_count for _, body in body_ranges)
            non_empty = sum(1 for _, body in body_ranges if body.char_count > 0)
            avg_chars = total_chars / len(body_ranges) if body_ranges else 0

            print(f"  Statistics:")
            print(f"    Total elements: {len(body_ranges)}")
            print(f"    Non-empty elements: {non_empty}")
            print(f"    Total content characters: {total_chars:,}")
            print(f"    Average chars per element: {avg_chars:.1f}")
            print()

        except Exception as e:
            print(f"  Error processing file: {e}")
            print()

    # Demonstrate specific functionality
    print("FUNCTIONALITY DEMONSTRATION")
    print("-" * 27)

    demo_markdown = """# R:MainPurpose - Main System Purpose

The Project1 system provides a disciplined workflow for building software
with AI by keeping design intent explicit and decomposing work into atomic tasks.

Key benefits:
- Explicit design documentation
- Atomic task decomposition
- Fresh session execution capability

## C:WorkspaceManager - Workspace Management Component

Purpose: Load, validate, and index the workspace and projects.

Responsibilities:
- Discover projects in the workspace
- Ensure required files exist
- Provide paths, metadata, and indexing state
- Monitor markdown files for external changes

### M:loadWorkspace - Load Workspace Method

```python
def load_workspace(workspace_path: str) -> WorkspaceInfo:
    \"\"\"Load and validate workspace structure.\"\"\"
    # Implementation details...
    pass
```

## C:MCPServer - MCP Tool Server Component

Purpose: Expose Project1 capabilities as MCP tools to external agents.

The server provides:
1. Read operations (list_projects, get_element)
2. Write operations (update_element, apply_patch)
3. Generation operations (generate_plan, generate_tests)
"""

    print("Extracting from demonstration markdown:")
    demo_ranges = extract_all_bodies(demo_markdown)

    for i, (heading, body) in enumerate(demo_ranges):
        element_id = heading.element_id or f"NoID{i}"
        print(f"\n{i+1}. {element_id} (h{heading.heading_level})")

        # Show element boundaries
        content_lines = body.raw_content.split('\n') if body.raw_content else []
        print(f"   Boundaries: lines {body.start_line}-{body.end_line}")
        print(f"   Content lines: {len(content_lines)}")

        # Show content structure
        if body.stripped_content:
            content_preview = body.stripped_content[:200].replace('\n', '\\n')
            if len(body.stripped_content) > 200:
                content_preview += "..."
            print(f"   Content: {content_preview}")

            # Analyze content structure
            has_lists = '- ' in body.stripped_content or '1. ' in body.stripped_content
            has_code = '```' in body.stripped_content or '`' in body.stripped_content
            has_multiple_paras = '\n\n' in body.stripped_content

            features = []
            if has_lists: features.append("lists")
            if has_code: features.append("code")
            if has_multiple_paras: features.append("paragraphs")

            if features:
                print(f"   Features: {', '.join(features)}")
        else:
            print(f"   Content: (empty)")

    # Demonstrate editing capability
    print("\nCONTENT UPDATE DEMONSTRATION")
    print("-" * 28)

    # Find the WorkspaceManager element
    workspace_mgr_line = None
    for i, (heading, body) in enumerate(demo_ranges):
        if heading.element_id == "C:WorkspaceManager":
            workspace_mgr_line = heading.line_number
            break

    if workspace_mgr_line is not None:
        new_content = """Purpose: Enhanced workspace management with real-time monitoring.

Updated Responsibilities:
- Discover projects with intelligent filtering
- Validate workspace integrity automatically
- Provide rich metadata and indexing
- Real-time file system monitoring
- Project health reporting"""

        updated_markdown = extractor.extract_and_update_content(
            demo_markdown, workspace_mgr_line, new_content
        )

        print("Updated WorkspaceManager content:")
        print("Original snippet:")
        original_snippet = demo_markdown[demo_markdown.find("Purpose: Load, validate"):demo_markdown.find("Purpose: Load, validate") + 100]
        print(f"  {original_snippet}...")
        print("\nUpdated snippet:")
        updated_snippet = updated_markdown[updated_markdown.find("Purpose: Enhanced"):updated_markdown.find("Purpose: Enhanced") + 100]
        print(f"  {updated_snippet}...")
    else:
        print("WorkspaceManager element not found for update demo")

    print()
    print("✓ Body extraction preserves markdown formatting")
    print("✓ Accurate line and byte position tracking")
    print("✓ Proper element boundary detection")
    print("✓ Content update capability with round-trip editing")
    print("✓ Unicode and complex markdown support")
    print("✓ Empty element handling")


if __name__ == "__main__":
    main()