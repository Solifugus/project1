"""
Workspace discovery for Project1 workspace management.

This module implements T:0008, scanning workspace directories to find projects
and validate their structure according to R:WorkspaceLayout.
"""

import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class ProjectStatus(Enum):
    """Project validation status."""
    COMPLETE = "complete"           # All required files present
    INCOMPLETE = "incomplete"       # Some required files missing
    INVALID = "invalid"             # Invalid structure or naming


@dataclass
class RequiredFile:
    """Information about a required project file."""
    name: str
    path: Path
    exists: bool
    size_bytes: int = 0
    last_modified: Optional[float] = None  # Unix timestamp


@dataclass
class ProjectInfo:
    """Information about a discovered project."""
    name: str                           # Project directory name
    path: Path                          # Full path to project directory
    status: ProjectStatus               # Overall validation status

    # Required files
    software_design: RequiredFile
    development_plan: RequiredFile
    test_plan: RequiredFile

    # Additional discovered files
    additional_files: List[str] = field(default_factory=list)

    # Validation issues
    issues: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Update status based on required files."""
        required_files = [
            self.software_design,
            self.development_plan,
            self.test_plan
        ]

        missing_files = [f for f in required_files if not f.exists]

        if not missing_files:
            self.status = ProjectStatus.COMPLETE
        elif len(missing_files) < len(required_files):
            self.status = ProjectStatus.INCOMPLETE
        else:
            self.status = ProjectStatus.INVALID


@dataclass
class WorkspaceInfo:
    """Information about the discovered workspace."""
    path: Path                          # Workspace root path
    conventions_file: RequiredFile      # Global conventions.md file
    projects: List[ProjectInfo] = field(default_factory=list)

    # Discovery statistics
    total_directories: int = 0
    valid_projects: int = 0
    incomplete_projects: int = 0
    invalid_projects: int = 0

    # Global validation issues
    issues: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Update statistics based on projects."""
        self.valid_projects = len([p for p in self.projects if p.status == ProjectStatus.COMPLETE])
        self.incomplete_projects = len([p for p in self.projects if p.status == ProjectStatus.INCOMPLETE])
        self.invalid_projects = len([p for p in self.projects if p.status == ProjectStatus.INVALID])


class WorkspaceDiscoveryError(Exception):
    """Exception raised when workspace discovery fails."""
    pass


class WorkspaceDiscovery:
    """
    Discovers and validates Project1 workspace structure.

    Scans workspace directories to find projects and validate their structure
    according to the R:WorkspaceLayout specification.
    """

    # Required files for each project
    REQUIRED_PROJECT_FILES = [
        "software-design.md",
        "development-plan.md",
        "test-plan.md"
    ]

    # Required file at workspace level
    WORKSPACE_CONVENTIONS_FILE = "conventions.md"

    # Directories to skip during discovery
    SKIP_DIRECTORIES = {
        ".git", ".vscode", "__pycache__", "node_modules",
        "venv", ".env", "dist", "build", "target"
    }

    def __init__(self, workspace_path: Optional[str] = None):
        """
        Initialize workspace discovery.

        Args:
            workspace_path: Path to workspace root. Defaults to ~/software-projects.
        """
        if workspace_path is None:
            workspace_path = os.path.expanduser("~/software-projects")

        self.workspace_path = Path(workspace_path).resolve()

    def _create_required_file(self, file_path: Path) -> RequiredFile:
        """Create RequiredFile object with file information."""
        exists = file_path.exists()
        size_bytes = 0
        last_modified = None

        if exists and file_path.is_file():
            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
                last_modified = stat.st_mtime
            except OSError:
                # Handle permission or other file system errors
                pass

        return RequiredFile(
            name=file_path.name,
            path=file_path,
            exists=exists,
            size_bytes=size_bytes,
            last_modified=last_modified
        )

    def _validate_project_name(self, name: str) -> List[str]:
        """Validate project directory name and return issues."""
        issues = []

        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not name.replace('-', '').replace('_', '').isalnum():
            issues.append(f"Project name '{name}' contains invalid characters")

        # Check length
        if len(name) < 2:
            issues.append(f"Project name '{name}' is too short")
        elif len(name) > 50:
            issues.append(f"Project name '{name}' is too long")

        # Check for reserved names
        reserved_names = {'templates', 'shared', 'common', 'lib', 'bin'}
        if name.lower() in reserved_names:
            issues.append(f"Project name '{name}' is reserved")

        return issues

    def _discover_project_files(self, project_path: Path) -> Tuple[List[RequiredFile], List[str]]:
        """Discover all files in a project directory."""
        try:
            required_files = []
            additional_files = []

            # Check for required files
            for file_name in self.REQUIRED_PROJECT_FILES:
                file_path = project_path / file_name
                required_files.append(self._create_required_file(file_path))

            # Discover additional files
            if project_path.exists() and project_path.is_dir():
                try:
                    for item in project_path.iterdir():
                        if item.is_file() and item.name not in self.REQUIRED_PROJECT_FILES:
                            additional_files.append(item.name)
                except OSError:
                    # Handle permission errors
                    pass

            return required_files, additional_files

        except Exception as e:
            raise WorkspaceDiscoveryError(f"Failed to discover files in {project_path}: {e}")

    def _analyze_project_directory(self, project_path: Path) -> ProjectInfo:
        """Analyze a single project directory and return ProjectInfo."""
        project_name = project_path.name
        issues = []

        # Validate project name
        name_issues = self._validate_project_name(project_name)
        issues.extend(name_issues)

        # Discover files
        try:
            required_files, additional_files = self._discover_project_files(project_path)
        except WorkspaceDiscoveryError as e:
            issues.append(str(e))
            # Create empty required files for invalid projects
            required_files = [
                self._create_required_file(project_path / file_name)
                for file_name in self.REQUIRED_PROJECT_FILES
            ]
            additional_files = []

        # Map required files
        software_design = required_files[0]
        development_plan = required_files[1]
        test_plan = required_files[2]

        # Check for missing files
        missing_files = [f.name for f in required_files if not f.exists]
        if missing_files:
            issues.append(f"Missing required files: {', '.join(missing_files)}")

        # Check for empty files
        empty_files = [f.name for f in required_files if f.exists and f.size_bytes == 0]
        if empty_files:
            issues.append(f"Empty required files: {', '.join(empty_files)}")

        return ProjectInfo(
            name=project_name,
            path=project_path,
            status=ProjectStatus.INVALID,  # Will be updated in __post_init__
            software_design=software_design,
            development_plan=development_plan,
            test_plan=test_plan,
            additional_files=additional_files,
            issues=issues
        )

    def discover_projects(self) -> List[ProjectInfo]:
        """
        Discover all projects in the workspace.

        Returns:
            List of ProjectInfo objects for discovered projects.

        Raises:
            WorkspaceDiscoveryError: If workspace scanning fails.
        """
        if not self.workspace_path.exists():
            raise WorkspaceDiscoveryError(f"Workspace path does not exist: {self.workspace_path}")

        if not self.workspace_path.is_dir():
            raise WorkspaceDiscoveryError(f"Workspace path is not a directory: {self.workspace_path}")

        projects = []

        try:
            # Scan for project directories
            for item in self.workspace_path.iterdir():
                # Skip non-directories and hidden/system directories
                if not item.is_dir() or item.name.startswith('.') or item.name in self.SKIP_DIRECTORIES:
                    continue

                try:
                    project_info = self._analyze_project_directory(item)
                    projects.append(project_info)
                except Exception as e:
                    # Log warning but continue with other projects
                    print(f"Warning: Failed to analyze project directory {item.name}: {e}")

        except OSError as e:
            raise WorkspaceDiscoveryError(f"Failed to scan workspace directory: {e}")

        return projects

    def discover_workspace(self) -> WorkspaceInfo:
        """
        Discover complete workspace information including conventions file and projects.

        Returns:
            WorkspaceInfo object with complete workspace information.

        Raises:
            WorkspaceDiscoveryError: If workspace discovery fails.
        """
        issues = []

        # Check conventions file
        conventions_path = self.workspace_path / self.WORKSPACE_CONVENTIONS_FILE
        conventions_file = self._create_required_file(conventions_path)

        if not conventions_file.exists:
            issues.append("Missing workspace conventions.md file")
        elif conventions_file.size_bytes == 0:
            issues.append("Workspace conventions.md file is empty")

        # Discover projects
        projects = self.discover_projects()

        # Count directories for statistics
        total_directories = 0
        if self.workspace_path.exists():
            try:
                total_directories = len([
                    item for item in self.workspace_path.iterdir()
                    if item.is_dir() and not item.name.startswith('.')
                    and item.name not in self.SKIP_DIRECTORIES
                ])
            except OSError:
                pass

        return WorkspaceInfo(
            path=self.workspace_path,
            conventions_file=conventions_file,
            projects=projects,
            total_directories=total_directories,
            issues=issues
        )

    def find_project_by_name(self, name: str) -> Optional[ProjectInfo]:
        """
        Find a specific project by name.

        Args:
            name: Project name to search for.

        Returns:
            ProjectInfo if found, None otherwise.
        """
        projects = self.discover_projects()
        return next((p for p in projects if p.name == name), None)

    def get_workspace_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive workspace statistics.

        Returns:
            Dictionary with workspace statistics.
        """
        workspace_info = self.discover_workspace()

        # Calculate file size statistics
        total_size = workspace_info.conventions_file.size_bytes

        project_sizes = []
        for project in workspace_info.projects:
            project_size = (
                project.software_design.size_bytes +
                project.development_plan.size_bytes +
                project.test_plan.size_bytes
            )
            project_sizes.append(project_size)
            total_size += project_size

        avg_project_size = sum(project_sizes) / len(project_sizes) if project_sizes else 0

        # Status distribution
        status_counts = {
            'complete': workspace_info.valid_projects,
            'incomplete': workspace_info.incomplete_projects,
            'invalid': workspace_info.invalid_projects,
        }

        return {
            'workspace_path': str(workspace_info.path),
            'total_projects': len(workspace_info.projects),
            'total_directories': workspace_info.total_directories,
            'project_status_distribution': status_counts,
            'total_size_bytes': total_size,
            'average_project_size_bytes': int(avg_project_size),
            'conventions_file_exists': workspace_info.conventions_file.exists,
            'conventions_file_size': workspace_info.conventions_file.size_bytes,
            'workspace_issues': len(workspace_info.issues),
            'total_project_issues': sum(len(p.issues) for p in workspace_info.projects),
        }

    def validate_workspace_structure(self) -> List[str]:
        """
        Validate workspace structure and return all issues.

        Returns:
            List of validation issues found.
        """
        workspace_info = self.discover_workspace()
        all_issues = workspace_info.issues.copy()

        for project in workspace_info.projects:
            for issue in project.issues:
                all_issues.append(f"{project.name}: {issue}")

        return all_issues

    def export_workspace_info(self, output_path: str) -> None:
        """
        Export workspace information to JSON file.

        Args:
            output_path: Path to save JSON file.
        """
        workspace_info = self.discover_workspace()

        # Convert to serializable format
        data = {
            'workspace': {
                'path': str(workspace_info.path),
                'conventions_file': {
                    'name': workspace_info.conventions_file.name,
                    'exists': workspace_info.conventions_file.exists,
                    'size_bytes': workspace_info.conventions_file.size_bytes,
                    'last_modified': workspace_info.conventions_file.last_modified,
                },
                'issues': workspace_info.issues,
                'statistics': {
                    'total_directories': workspace_info.total_directories,
                    'valid_projects': workspace_info.valid_projects,
                    'incomplete_projects': workspace_info.incomplete_projects,
                    'invalid_projects': workspace_info.invalid_projects,
                }
            },
            'projects': []
        }

        for project in workspace_info.projects:
            project_data = {
                'name': project.name,
                'path': str(project.path),
                'status': project.status.value,
                'required_files': {
                    'software_design': {
                        'exists': project.software_design.exists,
                        'size_bytes': project.software_design.size_bytes,
                        'last_modified': project.software_design.last_modified,
                    },
                    'development_plan': {
                        'exists': project.development_plan.exists,
                        'size_bytes': project.development_plan.size_bytes,
                        'last_modified': project.development_plan.last_modified,
                    },
                    'test_plan': {
                        'exists': project.test_plan.exists,
                        'size_bytes': project.test_plan.size_bytes,
                        'last_modified': project.test_plan.last_modified,
                    },
                },
                'additional_files': project.additional_files,
                'issues': project.issues,
            }
            data['projects'].append(project_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


def discover_workspace(workspace_path: Optional[str] = None) -> WorkspaceInfo:
    """
    Convenience function to discover workspace information.

    Args:
        workspace_path: Path to workspace root. Defaults to ~/software-projects.

    Returns:
        WorkspaceInfo object with complete workspace information.
    """
    discovery = WorkspaceDiscovery(workspace_path)
    return discovery.discover_workspace()


def find_projects(workspace_path: Optional[str] = None) -> List[ProjectInfo]:
    """
    Convenience function to find all projects in workspace.

    Args:
        workspace_path: Path to workspace root. Defaults to ~/software-projects.

    Returns:
        List of ProjectInfo objects.
    """
    discovery = WorkspaceDiscovery(workspace_path)
    return discovery.discover_projects()