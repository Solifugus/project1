"""
Workspace path resolution utilities for Project1.

This module provides functions to resolve standard workspace paths as specified
in R:WorkspaceLayout and supports the ~/software-projects workspace structure.
"""

import os
from pathlib import Path
from typing import Optional, List
from enum import Enum


class ArtifactType(Enum):
    """Types of artifact files in the workspace."""
    CONVENTIONS = "conventions.md"
    SOFTWARE_DESIGN = "software-design.md"
    DEVELOPMENT_PLAN = "development-plan.md"
    TEST_PLAN = "test-plan.md"


def get_workspace_root() -> Path:
    """
    Resolve the workspace root directory (~/software-projects).

    Returns:
        Path: Absolute path to the workspace root directory.

    Raises:
        FileNotFoundError: If home directory cannot be determined.
    """
    home_dir = Path.home()
    if not home_dir.exists():
        raise FileNotFoundError(f"Home directory not found: {home_dir}")

    workspace_root = home_dir / "software-projects"
    return workspace_root


def get_conventions_path() -> Path:
    """
    Get path to global conventions.md file.

    Returns:
        Path: Full path to conventions.md in workspace root.
    """
    return get_workspace_root() / "conventions.md"


def get_project_directory(project_name: str) -> Path:
    """
    Get path to a project directory within the workspace.

    Args:
        project_name: Name of the project (e.g., "project1").

    Returns:
        Path: Full path to project directory.

    Raises:
        ValueError: If project_name is empty or contains invalid characters.
    """
    if not project_name:
        raise ValueError("Project name cannot be empty")

    if not project_name.replace("-", "").replace("_", "").isalnum():
        raise ValueError(f"Invalid project name: {project_name}")

    return get_workspace_root() / project_name


def get_artifact_path(project_name: str, artifact_type: ArtifactType) -> Path:
    """
    Get path to a specific artifact file within a project.

    Args:
        project_name: Name of the project.
        artifact_type: Type of artifact file.

    Returns:
        Path: Full path to the artifact file.
    """
    project_dir = get_project_directory(project_name)
    return project_dir / artifact_type.value


def get_all_artifact_paths(project_name: str) -> dict[ArtifactType, Path]:
    """
    Get paths to all standard artifact files for a project.

    Args:
        project_name: Name of the project.

    Returns:
        Dict mapping artifact types to their file paths (excluding conventions.md
        which is at workspace level).
    """
    return {
        artifact_type: get_artifact_path(project_name, artifact_type)
        for artifact_type in ArtifactType
        if artifact_type != ArtifactType.CONVENTIONS
    }


def validate_workspace_structure(check_existence: bool = True) -> dict[str, bool]:
    """
    Validate the workspace directory structure.

    Args:
        check_existence: Whether to check if files actually exist on disk.

    Returns:
        Dict with validation results:
        - workspace_root_exists: bool
        - conventions_exists: bool
        - workspace_writable: bool
    """
    results = {}
    workspace_root = get_workspace_root()

    # Check workspace root
    results['workspace_root_exists'] = workspace_root.exists() if check_existence else True

    # Check if workspace is writable (if it exists)
    if results['workspace_root_exists']:
        try:
            test_file = workspace_root / ".write_test"
            test_file.touch()
            test_file.unlink()
            results['workspace_writable'] = True
        except (PermissionError, OSError):
            results['workspace_writable'] = False
    else:
        results['workspace_writable'] = False

    # Check conventions file
    conventions_path = get_conventions_path()
    results['conventions_exists'] = conventions_path.exists() if check_existence else True

    return results


def validate_project_structure(project_name: str, check_existence: bool = True) -> dict[str, bool]:
    """
    Validate a specific project's directory structure.

    Args:
        project_name: Name of the project to validate.
        check_existence: Whether to check if files actually exist on disk.

    Returns:
        Dict with validation results for each artifact file.
    """
    results = {}
    project_dir = get_project_directory(project_name)

    # Check project directory
    results['project_directory_exists'] = project_dir.exists() if check_existence else True

    # Check each artifact file
    for artifact_type in ArtifactType:
        if artifact_type == ArtifactType.CONVENTIONS:
            continue  # Conventions is at workspace level

        artifact_path = get_artifact_path(project_name, artifact_type)
        key = f"{artifact_type.name.lower()}_exists"
        results[key] = artifact_path.exists() if check_existence else True

    return results


def discover_projects() -> List[str]:
    """
    Discover all valid project directories in the workspace.

    Returns:
        List of project names found in the workspace.

    Raises:
        FileNotFoundError: If workspace root doesn't exist.
    """
    workspace_root = get_workspace_root()

    if not workspace_root.exists():
        raise FileNotFoundError(f"Workspace root does not exist: {workspace_root}")

    projects = []

    for item in workspace_root.iterdir():
        if not item.is_dir():
            continue

        # Skip hidden directories and known non-project directories
        if item.name.startswith('.') or item.name in ['templates', '__pycache__']:
            continue

        # Check if directory has at least software-design.md (minimum requirement)
        software_design_path = item / ArtifactType.SOFTWARE_DESIGN.value
        if software_design_path.exists():
            projects.append(item.name)

    return sorted(projects)


def ensure_workspace_structure() -> None:
    """
    Ensure the basic workspace structure exists, creating directories as needed.

    Raises:
        PermissionError: If unable to create directories due to permissions.
        OSError: If unable to create directories due to filesystem issues.
    """
    workspace_root = get_workspace_root()

    # Create workspace root if it doesn't exist
    workspace_root.mkdir(parents=True, exist_ok=True)

    # Ensure templates directory exists (for future use)
    templates_dir = workspace_root / "templates"
    templates_dir.mkdir(exist_ok=True)


def ensure_project_structure(project_name: str) -> None:
    """
    Ensure a project directory exists, creating it if needed.

    Args:
        project_name: Name of the project.

    Raises:
        PermissionError: If unable to create directory due to permissions.
        OSError: If unable to create directory due to filesystem issues.
    """
    project_dir = get_project_directory(project_name)
    project_dir.mkdir(parents=True, exist_ok=True)


def get_relative_path(absolute_path: Path) -> Optional[Path]:
    """
    Convert an absolute path to a path relative to workspace root.

    Args:
        absolute_path: The absolute path to convert.

    Returns:
        Path relative to workspace root, or None if path is outside workspace.
    """
    workspace_root = get_workspace_root()

    try:
        return absolute_path.relative_to(workspace_root)
    except ValueError:
        # Path is not within workspace
        return None


def is_within_workspace(path: Path) -> bool:
    """
    Check if a path is within the workspace directory.

    Args:
        path: The path to check.

    Returns:
        True if path is within workspace, False otherwise.
    """
    return get_relative_path(path) is not None


def get_workspace_info() -> dict:
    """
    Get comprehensive information about the workspace.

    Returns:
        Dict containing workspace paths and validation results.
    """
    workspace_root = get_workspace_root()

    info = {
        'workspace_root': str(workspace_root),
        'conventions_path': str(get_conventions_path()),
        'validation': validate_workspace_structure(),
        'discovered_projects': [],
    }

    try:
        projects = discover_projects()
        info['discovered_projects'] = projects

        # Add project info
        info['projects'] = {}
        for project_name in projects:
            info['projects'][project_name] = {
                'directory': str(get_project_directory(project_name)),
                'artifacts': {
                    artifact_type.name.lower(): str(path)
                    for artifact_type, path in get_all_artifact_paths(project_name).items()
                    if artifact_type != ArtifactType.CONVENTIONS
                },
                'validation': validate_project_structure(project_name)
            }

    except FileNotFoundError:
        info['error'] = "Workspace root does not exist"

    return info