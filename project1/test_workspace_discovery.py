"""
Tests for workspace discovery functionality.

This validates T:0008 acceptance criteria.
"""

import os
import tempfile
from pathlib import Path
from workspace_discovery import (
    WorkspaceDiscovery, WorkspaceDiscoveryError, ProjectInfo, WorkspaceInfo,
    ProjectStatus, RequiredFile, discover_workspace, find_projects
)


def create_test_workspace(base_dir: Path) -> Path:
    """Create a test workspace structure for testing."""
    workspace_path = base_dir / "test_workspace"
    workspace_path.mkdir(exist_ok=True)

    # Create conventions.md
    conventions_file = workspace_path / "conventions.md"
    conventions_file.write_text("# Conventions\n\nProject conventions go here.\n")

    # Create complete project
    project1_path = workspace_path / "project1"
    project1_path.mkdir(exist_ok=True)
    (project1_path / "software-design.md").write_text("# Software Design\n\nDesign content.")
    (project1_path / "development-plan.md").write_text("# Development Plan\n\nPlan content.")
    (project1_path / "test-plan.md").write_text("# Test Plan\n\nTest content.")

    # Create incomplete project (missing test-plan)
    project2_path = workspace_path / "incomplete-project"
    project2_path.mkdir(exist_ok=True)
    (project2_path / "software-design.md").write_text("# Software Design\n\nDesign.")
    (project2_path / "development-plan.md").write_text("# Development Plan\n\nPlan.")

    # Create invalid project (empty directory)
    project3_path = workspace_path / "empty-project"
    project3_path.mkdir(exist_ok=True)

    # Create project with additional files
    project4_path = workspace_path / "project-with-extras"
    project4_path.mkdir(exist_ok=True)
    (project4_path / "software-design.md").write_text("# Design\n")
    (project4_path / "development-plan.md").write_text("# Plan\n")
    (project4_path / "test-plan.md").write_text("# Test\n")
    (project4_path / "README.md").write_text("# README\n")
    (project4_path / "notes.txt").write_text("Notes")

    # Create non-project directories to ignore
    (workspace_path / ".git").mkdir(exist_ok=True)
    (workspace_path / "__pycache__").mkdir(exist_ok=True)
    (workspace_path / "not-a-project-file.txt").write_text("Random file")

    return workspace_path


def test_workspace_discovery_initialization():
    """Test WorkspaceDiscovery initialization."""
    # Test default initialization
    discovery = WorkspaceDiscovery()
    expected_default = Path.home() / "software-projects"
    assert discovery.workspace_path == expected_default

    # Test custom path initialization
    custom_path = "/custom/workspace"
    discovery = WorkspaceDiscovery(custom_path)
    assert discovery.workspace_path == Path(custom_path).resolve()


def test_required_file_creation():
    """Test RequiredFile object creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test existing file
        existing_file = temp_path / "existing.md"
        existing_file.write_text("Content here")

        discovery = WorkspaceDiscovery()
        required_file = discovery._create_required_file(existing_file)

        assert required_file.name == "existing.md"
        assert required_file.path == existing_file
        assert required_file.exists is True
        assert required_file.size_bytes > 0
        assert required_file.last_modified is not None

        # Test non-existing file
        missing_file = temp_path / "missing.md"
        required_file = discovery._create_required_file(missing_file)

        assert required_file.name == "missing.md"
        assert required_file.path == missing_file
        assert required_file.exists is False
        assert required_file.size_bytes == 0
        assert required_file.last_modified is None


def test_project_name_validation():
    """Test project name validation logic."""
    discovery = WorkspaceDiscovery()

    # Valid names
    valid_names = ["project1", "my-project", "test_project", "Project123"]
    for name in valid_names:
        issues = discovery._validate_project_name(name)
        assert len(issues) == 0, f"Valid name '{name}' should not have issues"

    # Invalid names
    invalid_cases = [
        ("a", "too short"),
        ("project with spaces", "invalid characters"),
        ("project@invalid", "invalid characters"),
        ("templates", "reserved"),
        ("x" * 60, "too long"),
    ]

    for name, reason in invalid_cases:
        issues = discovery._validate_project_name(name)
        assert len(issues) > 0, f"Invalid name '{name}' should have issues ({reason})"


def test_project_discovery():
    """Test discovery of individual projects."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = create_test_workspace(Path(temp_dir))
        discovery = WorkspaceDiscovery(str(workspace_path))

        projects = discovery.discover_projects()

        # Should find 4 projects (ignoring .git, __pycache__, and the .txt file)
        assert len(projects) == 4

        # Find specific projects
        project1 = next(p for p in projects if p.name == "project1")
        incomplete = next(p for p in projects if p.name == "incomplete-project")
        empty = next(p for p in projects if p.name == "empty-project")
        extras = next(p for p in projects if p.name == "project-with-extras")

        # Test complete project
        assert project1.status == ProjectStatus.COMPLETE
        assert project1.software_design.exists
        assert project1.development_plan.exists
        assert project1.test_plan.exists
        assert len(project1.issues) == 0

        # Test incomplete project
        assert incomplete.status == ProjectStatus.INCOMPLETE
        assert incomplete.software_design.exists
        assert incomplete.development_plan.exists
        assert not incomplete.test_plan.exists
        assert len(incomplete.issues) > 0
        assert any("Missing required files" in issue for issue in incomplete.issues)

        # Test empty project
        assert empty.status == ProjectStatus.INVALID
        assert not empty.software_design.exists
        assert not empty.development_plan.exists
        assert not empty.test_plan.exists

        # Test project with extras
        assert extras.status == ProjectStatus.COMPLETE
        assert "README.md" in extras.additional_files
        assert "notes.txt" in extras.additional_files


def test_workspace_discovery():
    """Test complete workspace discovery."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = create_test_workspace(Path(temp_dir))
        discovery = WorkspaceDiscovery(str(workspace_path))

        workspace_info = discovery.discover_workspace()

        # Check workspace path
        assert workspace_info.path == workspace_path

        # Check conventions file
        assert workspace_info.conventions_file.exists
        assert workspace_info.conventions_file.size_bytes > 0

        # Check project counts
        assert workspace_info.valid_projects == 2  # project1, project-with-extras
        assert workspace_info.incomplete_projects == 1  # incomplete-project
        assert workspace_info.invalid_projects == 1  # empty-project
        assert len(workspace_info.projects) == 4

        # Check directory count (should exclude hidden dirs)
        assert workspace_info.total_directories >= 4


def test_missing_workspace():
    """Test handling of missing workspace directory."""
    discovery = WorkspaceDiscovery("/nonexistent/workspace")

    try:
        discovery.discover_workspace()
        assert False, "Should raise WorkspaceDiscoveryError"
    except WorkspaceDiscoveryError as e:
        assert "does not exist" in str(e)


def test_workspace_without_conventions():
    """Test workspace discovery without conventions file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "no_conventions_workspace"
        workspace_path.mkdir()

        # Create a project without conventions.md
        project_path = workspace_path / "test-project"
        project_path.mkdir()
        (project_path / "software-design.md").write_text("# Design")
        (project_path / "development-plan.md").write_text("# Plan")
        (project_path / "test-plan.md").write_text("# Test")

        discovery = WorkspaceDiscovery(str(workspace_path))
        workspace_info = discovery.discover_workspace()

        # Should still discover projects
        assert len(workspace_info.projects) == 1
        assert workspace_info.projects[0].name == "test-project"

        # Should report missing conventions file
        assert not workspace_info.conventions_file.exists
        assert len(workspace_info.issues) > 0
        assert any("Missing workspace conventions.md" in issue for issue in workspace_info.issues)


def test_find_project_by_name():
    """Test finding specific project by name."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = create_test_workspace(Path(temp_dir))
        discovery = WorkspaceDiscovery(str(workspace_path))

        # Find existing project
        project = discovery.find_project_by_name("project1")
        assert project is not None
        assert project.name == "project1"
        assert project.status == ProjectStatus.COMPLETE

        # Find non-existing project
        project = discovery.find_project_by_name("nonexistent")
        assert project is None


def test_workspace_statistics():
    """Test workspace statistics generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = create_test_workspace(Path(temp_dir))
        discovery = WorkspaceDiscovery(str(workspace_path))

        stats = discovery.get_workspace_statistics()

        # Check basic statistics
        assert stats['total_projects'] == 4
        assert stats['project_status_distribution']['complete'] == 2
        assert stats['project_status_distribution']['incomplete'] == 1
        assert stats['project_status_distribution']['invalid'] == 1

        # Check file statistics
        assert stats['total_size_bytes'] > 0
        assert stats['conventions_file_exists'] is True
        assert stats['conventions_file_size'] > 0

        # Check workspace path
        assert stats['workspace_path'] == str(workspace_path)


def test_workspace_validation():
    """Test workspace structure validation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = create_test_workspace(Path(temp_dir))
        discovery = WorkspaceDiscovery(str(workspace_path))

        issues = discovery.validate_workspace_structure()

        # Should have issues for incomplete and invalid projects
        assert len(issues) > 0

        # Check for expected issues
        incomplete_issues = [issue for issue in issues if "incomplete-project" in issue]
        assert len(incomplete_issues) > 0

        empty_issues = [issue for issue in issues if "empty-project" in issue]
        assert len(empty_issues) > 0


def test_json_export():
    """Test exporting workspace information to JSON."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = create_test_workspace(Path(temp_dir))
        discovery = WorkspaceDiscovery(str(workspace_path))

        output_file = Path(temp_dir) / "workspace_info.json"
        discovery.export_workspace_info(str(output_file))

        # Check that file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Load and verify JSON structure
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert 'workspace' in data
        assert 'projects' in data
        assert data['workspace']['path'] == str(workspace_path)
        assert len(data['projects']) == 4


def test_convenience_functions():
    """Test convenience functions for workspace discovery."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = create_test_workspace(Path(temp_dir))

        # Test discover_workspace function
        workspace_info = discover_workspace(str(workspace_path))
        assert isinstance(workspace_info, WorkspaceInfo)
        assert len(workspace_info.projects) == 4

        # Test find_projects function
        projects = find_projects(str(workspace_path))
        assert isinstance(projects, list)
        assert len(projects) == 4
        assert all(isinstance(p, ProjectInfo) for p in projects)


def test_empty_workspace():
    """Test discovery on empty workspace."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "empty_workspace"
        workspace_path.mkdir()

        discovery = WorkspaceDiscovery(str(workspace_path))
        workspace_info = discovery.discover_workspace()

        assert len(workspace_info.projects) == 0
        assert workspace_info.valid_projects == 0
        assert workspace_info.incomplete_projects == 0
        assert workspace_info.invalid_projects == 0
        assert not workspace_info.conventions_file.exists


def test_project_status_calculation():
    """Test ProjectInfo status calculation logic."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create files for testing
        design_file = temp_path / "software-design.md"
        plan_file = temp_path / "development-plan.md"
        test_file = temp_path / "test-plan.md"

        design_file.write_text("content")
        plan_file.write_text("content")

        discovery = WorkspaceDiscovery()

        # Test complete project
        design_rf = discovery._create_required_file(design_file)
        plan_rf = discovery._create_required_file(plan_file)
        test_rf = discovery._create_required_file(test_file)

        # All files exist
        test_file.write_text("content")
        test_rf_exists = discovery._create_required_file(test_file)

        project_info = ProjectInfo(
            name="test",
            path=temp_path,
            status=ProjectStatus.INVALID,  # Will be updated
            software_design=design_rf,
            development_plan=plan_rf,
            test_plan=test_rf_exists,
            additional_files=[],
            issues=[]
        )

        assert project_info.status == ProjectStatus.COMPLETE

        # Test incomplete project (missing test file)
        project_info = ProjectInfo(
            name="test",
            path=temp_path,
            status=ProjectStatus.INVALID,  # Will be updated
            software_design=design_rf,
            development_plan=plan_rf,
            test_plan=test_rf,  # Doesn't exist
            additional_files=[],
            issues=[]
        )

        assert project_info.status == ProjectStatus.INCOMPLETE


def test_error_handling():
    """Test error handling in workspace discovery."""
    # Test with file instead of directory
    with tempfile.NamedTemporaryFile() as temp_file:
        discovery = WorkspaceDiscovery(temp_file.name)

        try:
            discovery.discover_workspace()
            assert False, "Should raise WorkspaceDiscoveryError"
        except WorkspaceDiscoveryError as e:
            assert "not a directory" in str(e)


if __name__ == "__main__":
    # Run all tests manually
    print("Running workspace discovery tests...")

    test_workspace_discovery_initialization()
    print("✓ WorkspaceDiscovery initialization")

    test_required_file_creation()
    print("✓ RequiredFile creation")

    test_project_name_validation()
    print("✓ Project name validation")

    test_project_discovery()
    print("✓ Project discovery")

    test_workspace_discovery()
    print("✓ Complete workspace discovery")

    test_missing_workspace()
    print("✓ Missing workspace handling")

    test_workspace_without_conventions()
    print("✓ Workspace without conventions file")

    test_find_project_by_name()
    print("✓ Find project by name")

    test_workspace_statistics()
    print("✓ Workspace statistics")

    test_workspace_validation()
    print("✓ Workspace validation")

    test_json_export()
    print("✓ JSON export")

    test_convenience_functions()
    print("✓ Convenience functions")

    test_empty_workspace()
    print("✓ Empty workspace handling")

    test_project_status_calculation()
    print("✓ Project status calculation")

    test_error_handling()
    print("✓ Error handling")

    print("\nAll tests passed! T:0008 workspace discovery is complete.")