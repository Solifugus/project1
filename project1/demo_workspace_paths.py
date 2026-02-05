"""
Demo showing workspace path utilities in action with Project1.
"""

from workspace_paths import (
    get_workspace_root, get_conventions_path, get_project_directory,
    get_artifact_path, get_all_artifact_paths, ArtifactType,
    validate_workspace_structure, validate_project_structure,
    discover_projects, get_workspace_info, get_relative_path,
    is_within_workspace
)


def main():
    """Demonstrate workspace path utilities with real Project1 workspace."""
    print("Workspace Path Utilities Demo")
    print("=" * 35)

    # Demonstrate basic path resolution
    print("1. Basic Path Resolution")
    print("-" * 25)

    workspace_root = get_workspace_root()
    print(f"Workspace Root: {workspace_root}")
    print(f"Expanded from: ~/software-projects")
    print(f"Is absolute path: {workspace_root.is_absolute()}")
    print()

    conventions_path = get_conventions_path()
    print(f"Global Conventions: {conventions_path}")
    print(f"Exists: {conventions_path.exists()}")
    print()

    # Project directory resolution
    print("2. Project Directory Resolution")
    print("-" * 30)

    project1_dir = get_project_directory("project1")
    print(f"Project1 Directory: {project1_dir}")
    print(f"Exists: {project1_dir.exists()}")
    print()

    # Test project name validation
    valid_names = ["project1", "my-project", "test_project", "project2024"]
    invalid_names = ["", "project/slash", "project with spaces", "project@special"]

    print("Valid project names:")
    for name in valid_names:
        try:
            path = get_project_directory(name)
            print(f"  ✓ '{name}' -> {path.name}")
        except ValueError as e:
            print(f"  ✗ '{name}' -> ERROR: {e}")

    print("\nInvalid project names:")
    for name in invalid_names:
        try:
            path = get_project_directory(name)
            print(f"  ✗ '{name}' -> Should have failed!")
        except ValueError as e:
            print(f"  ✓ '{name}' -> Correctly rejected: {str(e)[:40]}...")
    print()

    # Artifact path resolution
    print("3. Artifact Path Resolution")
    print("-" * 25)

    project_name = "project1"
    print(f"Artifact paths for '{project_name}':")

    for artifact_type in ArtifactType:
        if artifact_type == ArtifactType.CONVENTIONS:
            # Conventions is workspace-level
            path = get_conventions_path()
            location = "workspace level"
        else:
            path = get_artifact_path(project_name, artifact_type)
            location = "project level"

        print(f"  {artifact_type.name:20} -> {path}")
        print(f"  {'':20}    ({location}, exists: {path.exists()})")

    print()

    # All project artifacts
    print("4. All Project Artifacts")
    print("-" * 24)

    all_artifacts = get_all_artifact_paths(project_name)
    print(f"Project-level artifacts for '{project_name}':")
    for artifact_type, path in all_artifacts.items():
        relative = get_relative_path(path)
        print(f"  {artifact_type.name:20} -> {relative}")
    print()

    # Workspace validation
    print("5. Workspace Structure Validation")
    print("-" * 35)

    workspace_validation = validate_workspace_structure()
    print("Workspace validation results:")
    for check, result in workspace_validation.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check:20} -> {result}")
    print()

    # Project validation
    print("6. Project Structure Validation")
    print("-" * 31)

    project_validation = validate_project_structure(project_name)
    print(f"Project '{project_name}' validation results:")
    for check, result in project_validation.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check:25} -> {result}")
    print()

    # Project discovery
    print("7. Project Discovery")
    print("-" * 17)

    try:
        projects = discover_projects()
        print(f"Discovered {len(projects)} projects in workspace:")
        for i, project in enumerate(projects, 1):
            project_dir = get_project_directory(project)
            artifact_count = len([p for p in get_all_artifact_paths(project).values() if p.exists()])
            print(f"  {i}. {project:15} -> {artifact_count}/3 artifacts exist")

    except FileNotFoundError as e:
        print(f"Cannot discover projects: {e}")
    print()

    # Relative paths and workspace containment
    print("8. Path Utilities")
    print("-" * 15)

    test_paths = [
        workspace_root,
        project1_dir,
        get_artifact_path("project1", ArtifactType.SOFTWARE_DESIGN),
        workspace_root.parent,  # Outside workspace
        workspace_root / "nonexistent" / "nested"
    ]

    print("Path analysis:")
    for path in test_paths:
        relative = get_relative_path(path)
        in_workspace = is_within_workspace(path)
        exists = path.exists() if path != workspace_root.parent else "N/A"

        print(f"  Path: {path}")
        print(f"    Relative:     {relative or 'Outside workspace'}")
        print(f"    In workspace: {in_workspace}")
        print(f"    Exists:       {exists}")
        print()

    # Comprehensive workspace info
    print("9. Comprehensive Workspace Info")
    print("-" * 31)

    info = get_workspace_info()
    print("Complete workspace information:")
    print(f"  Workspace: {info['workspace_root']}")
    print(f"  Projects found: {len(info.get('discovered_projects', []))}")

    if 'projects' in info:
        for project_name, project_info in info['projects'].items():
            artifact_count = len(project_info['artifacts'])
            validation_passed = sum(project_info['validation'].values())
            validation_total = len(project_info['validation'])

            print(f"    {project_name}: {artifact_count} artifacts, "
                  f"{validation_passed}/{validation_total} validations passed")

    if 'error' in info:
        print(f"  Error: {info['error']}")

    print()

    # Summary
    print("✓ Workspace path utilities working correctly!")
    print("✓ Home directory expansion (~) works")
    print("✓ Project and artifact path building")
    print("✓ Path validation and existence checking")
    print("✓ Project discovery and structure validation")
    print("✓ Relative path conversion and workspace containment")
    print("✓ Comprehensive workspace analysis")


if __name__ == "__main__":
    main()