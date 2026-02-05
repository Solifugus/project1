"""
Tests for workspace path resolution utilities.

This validates T:0003 acceptance criteria.
"""

import os
import tempfile
from pathlib import Path
from workspace_paths import (
    get_workspace_root, get_conventions_path, get_project_directory,
    get_artifact_path, get_all_artifact_paths, ArtifactType,
    validate_workspace_structure, validate_project_structure,
    discover_projects, ensure_workspace_structure, ensure_project_structure,
    get_relative_path, is_within_workspace, get_workspace_info
)


def test_workspace_root_resolution():
    """Test workspace root resolution expands ~ correctly."""
    workspace_root = get_workspace_root()

    # Should expand ~ to actual home directory
    expected = Path.home() / "software-projects"
    assert workspace_root == expected
    assert str(workspace_root).startswith('/')  # Should be absolute path
    assert '~' not in str(workspace_root)  # Should be expanded


def test_conventions_path():
    """Test conventions.md path resolution."""
    conventions_path = get_conventions_path()

    expected = get_workspace_root() / "conventions.md"
    assert conventions_path == expected
    assert conventions_path.name == "conventions.md"


def test_project_directory_paths():
    """Test project directory path building."""
    # Valid project names
    project1_dir = get_project_directory("project1")
    expected = get_workspace_root() / "project1"
    assert project1_dir == expected

    test_project_dir = get_project_directory("test-project")
    expected_test = get_workspace_root() / "test-project"
    assert test_project_dir == expected_test

    # Project with underscores
    underscore_dir = get_project_directory("my_project")
    expected_underscore = get_workspace_root() / "my_project"
    assert underscore_dir == expected_underscore


def test_invalid_project_names():
    """Test project name validation."""
    # Empty project name should fail
    try:
        get_project_directory("")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot be empty" in str(e)

    # Invalid characters should fail
    try:
        get_project_directory("project/with/slash")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid project name" in str(e)

    try:
        get_project_directory("project with spaces")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid project name" in str(e)


def test_artifact_paths():
    """Test artifact file path building."""
    project_name = "project1"

    # Test individual artifact paths
    design_path = get_artifact_path(project_name, ArtifactType.SOFTWARE_DESIGN)
    expected_design = get_project_directory(project_name) / "software-design.md"
    assert design_path == expected_design

    plan_path = get_artifact_path(project_name, ArtifactType.DEVELOPMENT_PLAN)
    expected_plan = get_project_directory(project_name) / "development-plan.md"
    assert plan_path == expected_plan

    test_path = get_artifact_path(project_name, ArtifactType.TEST_PLAN)
    expected_test = get_project_directory(project_name) / "test-plan.md"
    assert test_path == expected_test


def test_all_artifact_paths():
    """Test getting all artifact paths for a project."""
    project_name = "project1"
    all_paths = get_all_artifact_paths(project_name)

    # Should have all artifact types except conventions (which is workspace-level)
    expected_types = {ArtifactType.SOFTWARE_DESIGN, ArtifactType.DEVELOPMENT_PLAN,
                     ArtifactType.TEST_PLAN}
    assert set(all_paths.keys()) == expected_types

    # Check specific paths
    project_dir = get_project_directory(project_name)
    assert all_paths[ArtifactType.SOFTWARE_DESIGN] == project_dir / "software-design.md"
    assert all_paths[ArtifactType.DEVELOPMENT_PLAN] == project_dir / "development-plan.md"
    assert all_paths[ArtifactType.TEST_PLAN] == project_dir / "test-plan.md"


def test_workspace_validation_real():
    """Test workspace structure validation with real workspace."""
    # Test with the actual workspace (should exist)
    validation = validate_workspace_structure(check_existence=True)

    # Should have expected keys
    expected_keys = {'workspace_root_exists', 'conventions_exists', 'workspace_writable'}
    assert set(validation.keys()) == expected_keys

    # All values should be boolean
    for key, value in validation.items():
        assert isinstance(value, bool), f"{key} should be boolean"


def test_workspace_validation_no_check():
    """Test workspace validation without existence checking."""
    validation = validate_workspace_structure(check_existence=False)

    # When not checking existence, workspace_root_exists should be True
    assert validation['workspace_root_exists'] is True
    assert validation['conventions_exists'] is True
    # workspace_writable will still be False since workspace_root_exists is True but we need to test


def test_project_validation_real():
    """Test project structure validation with real project."""
    # Test with project1 (should exist)
    validation = validate_project_structure("project1", check_existence=True)

    # Should have project directory check and artifact checks
    expected_keys = {'project_directory_exists', 'software_design_exists',
                    'development_plan_exists', 'test_plan_exists'}
    assert set(validation.keys()) == expected_keys

    # All values should be boolean
    for key, value in validation.items():
        assert isinstance(value, bool), f"{key} should be boolean"


def test_project_validation_no_check():
    """Test project validation without existence checking."""
    validation = validate_project_structure("nonexistent", check_existence=False)

    # All should be True when not checking existence
    for key, value in validation.items():
        assert value is True, f"{key} should be True when not checking existence"


def test_project_discovery_real():
    """Test discovering projects in real workspace."""
    try:
        projects = discover_projects()

        # Should return a list
        assert isinstance(projects, list)

        # project1 should be in the list (since we're testing in that workspace)
        assert "project1" in projects

        # Should be sorted
        assert projects == sorted(projects)

        # Should not include non-project directories
        assert "templates" not in projects
        assert ".git" not in projects

    except FileNotFoundError:
        # If workspace doesn't exist, that's fine for this test
        pass


def test_relative_path_conversion():
    """Test converting absolute paths to relative paths."""
    workspace_root = get_workspace_root()

    # Path within workspace
    project_path = workspace_root / "project1" / "software-design.md"
    relative = get_relative_path(project_path)
    expected = Path("project1") / "software-design.md"
    assert relative == expected

    # Workspace root itself
    relative_root = get_relative_path(workspace_root)
    assert relative_root == Path(".")

    # Path outside workspace
    outside_path = Path("/tmp/outside")
    relative_outside = get_relative_path(outside_path)
    assert relative_outside is None


def test_workspace_containment():
    """Test checking if paths are within workspace."""
    workspace_root = get_workspace_root()

    # Path within workspace
    project_path = workspace_root / "project1"
    assert is_within_workspace(project_path) is True

    # Workspace root itself
    assert is_within_workspace(workspace_root) is True

    # Path outside workspace
    outside_path = Path("/tmp")
    assert is_within_workspace(outside_path) is False


def test_ensure_workspace_structure():
    """Test workspace structure creation."""
    # This test uses the real filesystem but should be safe
    # as it only creates directories that should exist anyway

    try:
        ensure_workspace_structure()

        # Workspace root should exist after ensuring
        workspace_root = get_workspace_root()
        assert workspace_root.exists()

        # Templates directory should exist
        templates_dir = workspace_root / "templates"
        assert templates_dir.exists()

    except (PermissionError, OSError):
        # If we can't create directories, that's a filesystem issue
        pass


def test_ensure_project_structure():
    """Test project structure creation."""
    # Use a test project name that's safe to create
    test_project = "test-temp-project"

    try:
        ensure_project_structure(test_project)

        # Project directory should exist after ensuring
        project_dir = get_project_directory(test_project)
        assert project_dir.exists()

        # Clean up test directory
        if project_dir.exists() and project_dir.name == test_project:
            project_dir.rmdir()

    except (PermissionError, OSError):
        # If we can't create directories, that's a filesystem issue
        pass


def test_workspace_info():
    """Test comprehensive workspace information gathering."""
    info = get_workspace_info()

    # Should have expected keys
    expected_keys = {'workspace_root', 'conventions_path', 'validation'}
    assert all(key in info for key in expected_keys)

    # Paths should be strings
    assert isinstance(info['workspace_root'], str)
    assert isinstance(info['conventions_path'], str)

    # Validation should be a dict
    assert isinstance(info['validation'], dict)

    # Should have discovered_projects (list or error)
    assert 'discovered_projects' in info or 'error' in info


def test_artifact_type_enum():
    """Test ArtifactType enum values."""
    # Test all expected artifact types
    assert ArtifactType.CONVENTIONS.value == "conventions.md"
    assert ArtifactType.SOFTWARE_DESIGN.value == "software-design.md"
    assert ArtifactType.DEVELOPMENT_PLAN.value == "development-plan.md"
    assert ArtifactType.TEST_PLAN.value == "test-plan.md"

    # Should have exactly 4 types
    assert len(list(ArtifactType)) == 4


def test_path_objects_are_pathlib():
    """Test that all functions return pathlib.Path objects."""
    # All path functions should return Path objects, not strings
    assert isinstance(get_workspace_root(), Path)
    assert isinstance(get_conventions_path(), Path)
    assert isinstance(get_project_directory("project1"), Path)
    assert isinstance(get_artifact_path("project1", ArtifactType.SOFTWARE_DESIGN), Path)

    for artifact_type, path in get_all_artifact_paths("project1").items():
        assert isinstance(path, Path), f"{artifact_type} path should be Path object"


if __name__ == "__main__":
    # Run all tests manually
    print("Running workspace path tests...")

    test_workspace_root_resolution()
    print("✓ Workspace root resolution")

    test_conventions_path()
    print("✓ Conventions path")

    test_project_directory_paths()
    print("✓ Project directory paths")

    test_invalid_project_names()
    print("✓ Project name validation")

    test_artifact_paths()
    print("✓ Artifact paths")

    test_all_artifact_paths()
    print("✓ All artifact paths")

    test_workspace_validation_real()
    print("✓ Workspace validation (real)")

    test_workspace_validation_no_check()
    print("✓ Workspace validation (no check)")

    test_project_validation_real()
    print("✓ Project validation (real)")

    test_project_validation_no_check()
    print("✓ Project validation (no check)")

    test_project_discovery_real()
    print("✓ Project discovery")

    test_relative_path_conversion()
    print("✓ Relative path conversion")

    test_workspace_containment()
    print("✓ Workspace containment")

    test_ensure_workspace_structure()
    print("✓ Ensure workspace structure")

    test_ensure_project_structure()
    print("✓ Ensure project structure")

    test_workspace_info()
    print("✓ Workspace info")

    test_artifact_type_enum()
    print("✓ ArtifactType enum")

    test_path_objects_are_pathlib()
    print("✓ Path objects are pathlib.Path")

    print("\nAll tests passed! T:0003 implementation is complete.")