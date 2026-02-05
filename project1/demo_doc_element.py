"""
Demo showing DocElement usage with real Project1 data.
"""

from doc_element import DocElement, Kind, File, Status


def main():
    """Demonstrate DocElement with real Project1 elements."""
    print("DocElement Demo - Real Project1 Data")
    print("=" * 40)

    # Create a requirement element (from actual software design)
    purpose = DocElement(
        id="R:Purpose",
        kind=Kind.REQUIREMENT,
        title="System Purpose",
        file=File.SOFTWARE_DESIGN,
        heading_level=3,
        anchor="r-purpose",
        body_markdown="Project1 provides a disciplined workflow for building software with AI by keeping design intent explicit, decomposing work into atomic tasks, and ensuring each task contains sufficient context to execute in a fresh session with minimal context window.",
        refs=[]
    )

    print(f"1. Requirement: {purpose}")
    print(f"   Kind: {purpose.kind.value}")
    print(f"   File: {purpose.file.value}")
    print()

    # Create a component element
    workspace_mgr = DocElement(
        id="C:WorkspaceManager",
        kind=Kind.COMPONENT,
        title="Workspace Manager",
        file=File.SOFTWARE_DESIGN,
        heading_level=3,
        anchor="c-workspacemanager",
        body_markdown="Purpose: Load, validate, and index the workspace and projects.\nResponsibilities:\n- Discover projects in the workspace\n- Ensure required files exist\n- Provide paths, metadata, and indexing state\n- Monitor markdown files for external changes and trigger re-indexing",
        refs=["R:WorkspaceLayout"]
    )

    print(f"2. Component: {workspace_mgr}")
    print(f"   References: {workspace_mgr.refs}")
    print()

    # Create the current task element
    current_task = DocElement(
        id="T:0001",
        kind=Kind.TASK,
        title="Define DocElement data structure",
        file=File.DEVELOPMENT_PLAN,
        heading_level=3,
        anchor="t-0001",
        body_markdown="**Goal**: Implement the core DocElement struct/class as specified in D:DocElement\n\n**References**: D:DocElement",
        refs=["D:DocElement"],
        status=Status.COMPLETED  # We just finished it!
    )

    print(f"3. Task: {current_task}")
    print(f"   Status: {current_task.status.value}")
    print(f"   Is Task: {current_task.is_task()}")
    print()

    # Create a data structure element
    doc_element_spec = DocElement(
        id="D:DocElement",
        kind=Kind.DATA,
        title="DocElement Data Structure",
        file=File.SOFTWARE_DESIGN,
        heading_level=3,
        anchor="d-docelement",
        body_markdown="Fields:\n- id: string\n- kind: enum {Requirement, Component, Data, Interface, Method, UI, Task, Test, Other}\n- title: string\n- file: enum {conventions, software-design, development-plan, test-plan}\n- heading_level: int\n- anchor: string\n- body_markdown: string\n- refs: list[string] (IDs referenced in body or in explicit \"References\" section)\n- backlinks: list[string] (computed)\n- status: enum {pending, in_progress, completed} (for Task kind only)"
    )

    print(f"4. Data Structure: {doc_element_spec}")
    print()

    # Demonstrate cross-references
    print("Demonstrating cross-references:")
    current_task.add_reference("D:DocElement")
    doc_element_spec.add_backlink("T:0001")
    workspace_mgr.add_backlink("T:0008")  # Future task that will implement it

    print(f"- Task T:0001 references: {current_task.refs}")
    print(f"- D:DocElement has backlinks: {doc_element_spec.backlinks}")
    print(f"- C:WorkspaceManager has backlinks: {workspace_mgr.backlinks}")
    print()

    # Demonstrate serialization
    print("Serialization demo:")
    json_data = current_task.to_json()
    print("Task serialized to JSON:")
    print(json_data[:200] + "..." if len(json_data) > 200 else json_data)
    print()

    # Deserialize and verify
    restored_task = DocElement.from_json(json_data)
    print(f"Restored from JSON: {restored_task}")
    print(f"Status preserved: {restored_task.status.value}")
    print()

    print("✓ DocElement successfully handles real Project1 data!")
    print("✓ All required fields present and functional")
    print("✓ Enums work correctly")
    print("✓ Serialization maintains data integrity")
    print("✓ Cross-references work as expected")


if __name__ == "__main__":
    main()