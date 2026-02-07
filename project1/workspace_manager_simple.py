"""
Simplified WorkspaceManager for GUI integration.
Provides basic workspace management with indexer interface.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Import our existing DocElement
from doc_element import DocElement, Kind, File, Status


class IndexerState(Enum):
    """Indexer state enumeration."""
    UNINITIALIZED = "uninitialized"
    BUILDING = "building"
    READY = "ready"
    ERROR = "error"


@dataclass
class IndexState:
    """Current index state."""
    name: str
    element_count: int = 0
    last_updated: Optional[str] = None


class SimpleIndexer:
    """Simplified indexer that provides the interface expected by the GUI."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._state = IndexerState.UNINITIALIZED
        self._index: Dict[str, DocElement] = {}
        self._file_elements: Dict[str, List[str]] = {}

    def get_state(self) -> IndexState:
        """Get current indexer state."""
        return IndexState(
            name=self._state.value.upper(),
            element_count=len(self._index)
        )

    def get_index(self):
        """Get the document index."""
        return self

    def get_elements_by_kind(self, kind: Kind) -> List[DocElement]:
        """Get elements filtered by kind."""
        return [element for element in self._index.values() if element.kind == kind]

    def get_element(self, element_id: str) -> Optional[DocElement]:
        """Get a specific element by ID."""
        return self._index.get(element_id)

    def list_elements(self, file_filter: Optional[str] = None, kind_filter: Optional[Kind] = None) -> List[DocElement]:
        """List elements with optional filters."""
        elements = list(self._index.values())

        if file_filter:
            elements = [e for e in elements if e.file and e.file.name == file_filter]

        if kind_filter:
            elements = [e for e in elements if e.kind == kind_filter]

        return sorted(elements, key=lambda e: e.id)

    def build_index(self, workspace_path: Path) -> bool:
        """Build the document index from workspace files."""
        try:
            self._state = IndexerState.BUILDING
            self._index.clear()
            self._file_elements.clear()

            # Look for markdown files in workspace
            project_dirs = [d for d in workspace_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

            for project_dir in project_dirs:
                # Look for standard files
                for filename in ['software-design.md', 'development-plan.md', 'test-plan.md']:
                    file_path = project_dir / filename
                    if file_path.exists():
                        self._parse_markdown_file(file_path, filename)

            self._state = IndexerState.READY
            self.logger.info(f"Index built successfully: {len(self._index)} elements indexed")
            return True

        except Exception as e:
            self._state = IndexerState.ERROR
            self.logger.error(f"Error building index: {e}")
            return False

    def _parse_markdown_file(self, file_path: Path, filename: str):
        """Parse a markdown file and extract elements."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()

            current_element = None
            current_body_lines = []

            for i, line in enumerate(lines):
                # Check for heading with ID pattern
                if line.startswith('#') and ':' in line:
                    # Save previous element if exists
                    if current_element:
                        current_element.body_markdown = '\n'.join(current_body_lines)
                        self._add_element(current_element, filename)

                    # Parse new element
                    current_element = self._parse_heading(line, filename)
                    current_body_lines = []

                elif current_element and line.strip():
                    # Add content to current element body
                    current_body_lines.append(line)

            # Add final element
            if current_element:
                current_element.body_markdown = '\n'.join(current_body_lines)
                self._add_element(current_element, filename)

        except Exception as e:
            self.logger.warning(f"Error parsing {file_path}: {e}")

    def _parse_heading(self, line: str, filename: str) -> DocElement:
        """Parse a heading line to create a DocElement."""
        # Extract heading level
        heading_level = len(line) - len(line.lstrip('#'))

        # Extract title (remove # and strip)
        title = line.lstrip('# ').strip()

        # Try to extract ID from title
        element_id = None
        kind = Kind.OTHER

        if ':' in title:
            # Look for patterns like "T:0024 - Title" or "C:ComponentName"
            parts = title.split(' - ', 1)
            id_part = parts[0].strip()

            if ':' in id_part:
                prefix, number = id_part.split(':', 1)
                element_id = id_part

                # Map prefix to kind
                kind_map = {
                    'R': Kind.REQUIREMENT,
                    'C': Kind.COMPONENT,
                    'D': Kind.DATA,
                    'I': Kind.INTERFACE,
                    'M': Kind.METHOD,
                    'UI': Kind.UI,
                    'T': Kind.TASK,
                    'TP': Kind.TEST
                }
                kind = kind_map.get(prefix, Kind.OTHER)

                if len(parts) > 1:
                    title = parts[1].strip()
                else:
                    title = title

        if not element_id:
            # Generate ID from title if no explicit ID
            element_id = self._generate_id_from_title(title)

        # Map filename to File enum
        file_enum = File.SOFTWARE_DESIGN  # default
        if 'software-design' in filename:
            file_enum = File.SOFTWARE_DESIGN
        elif 'development-plan' in filename:
            file_enum = File.DEVELOPMENT_PLAN
        elif 'test-plan' in filename:
            file_enum = File.TEST_PLAN

        # Only add status for Task elements
        status = Status.PENDING if kind == Kind.TASK else None

        return DocElement(
            id=element_id,
            kind=kind,
            title=title,
            file=file_enum,
            heading_level=heading_level,
            anchor=self._title_to_anchor(title),
            body_markdown="",
            refs=[],
            backlinks=[],
            status=status
        )

    def _generate_id_from_title(self, title: str) -> str:
        """Generate an ID from title if no explicit ID found."""
        # Simple slug generation
        clean_title = ''.join(c for c in title if c.isalnum() or c.isspace())
        slug = clean_title.lower().replace(' ', '_')[:20]
        return f"auto_{slug}"

    def _title_to_anchor(self, title: str) -> str:
        """Convert title to anchor link."""
        return title.lower().replace(' ', '-').replace('_', '-')

    def _add_element(self, element: DocElement, filename: str):
        """Add element to index."""
        self._index[element.id] = element

        # Track elements by file
        if filename not in self._file_elements:
            self._file_elements[filename] = []
        self._file_elements[filename].append(element.id)

    def _group_by_kind(self) -> Dict[str, List[str]]:
        """Group elements by kind."""
        by_kind: Dict[str, List[str]] = {}

        for element in self._index.values():
            kind_name = element.kind.name
            if kind_name not in by_kind:
                by_kind[kind_name] = []
            by_kind[kind_name].append(element.id)

        return by_kind


class SimpleWorkspaceManager:
    """Simplified workspace manager for GUI integration."""

    def __init__(self, workspace_path: str):
        self.logger = logging.getLogger(__name__)
        self.workspace_path = Path(workspace_path).expanduser().resolve()
        self.indexer = SimpleIndexer()
        self.last_error: Optional[str] = None
        self._projects: List[Path] = []

    def load(self, start_watching: bool = False) -> bool:
        """Load workspace and build index."""
        try:
            self.logger.info(f"Loading workspace from {self.workspace_path}")

            # Check if workspace exists
            if not self.workspace_path.exists():
                self.last_error = f"Workspace path does not exist: {self.workspace_path}"
                self.logger.error(self.last_error)
                return False

            # Discover projects
            self._discover_projects()

            # Build document index
            success = self.indexer.build_index(self.workspace_path)

            if success:
                self.logger.info("Workspace loaded successfully")
                self.last_error = None
                return True
            else:
                self.last_error = "Failed to build document index"
                return False

        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Error loading workspace: {e}")
            return False

    def _discover_projects(self):
        """Discover projects in workspace."""
        self._projects = []

        if not self.workspace_path.exists():
            return

        # Look for directories that contain project files
        for item in self.workspace_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it has project files
                project_files = ['software-design.md', 'development-plan.md', 'test-plan.md']
                if any((item / f).exists() for f in project_files):
                    self._projects.append(item)

        self.logger.info(f"Discovered {len(self._projects)} projects in workspace")

    def get_projects(self) -> List[Path]:
        """Get list of project directories."""
        return self._projects.copy()

    def stop(self):
        """Stop workspace manager and cleanup."""
        self.logger.info("Workspace manager stopped")


def create_workspace_manager(workspace_path: str) -> SimpleWorkspaceManager:
    """Factory function to create a workspace manager."""
    return SimpleWorkspaceManager(workspace_path)