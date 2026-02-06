"""
WorkspaceManager: Unified interface for workspace operations.

Integrates workspace discovery, indexing, and file watching into a single component
that manages the complete workspace lifecycle.
"""

import logging
from pathlib import Path
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

from workspace_discovery import discover_workspace, find_projects, WorkspaceInfo, ProjectInfo
from indexer_operations import create_indexer, Indexer, IndexBuildResult, IndexerState
from file_watching import create_file_watcher, WorkspaceFileWatcher, FileEventType


class WorkspaceState(Enum):
    """Workspace manager state."""
    UNINITIALIZED = "uninitialized"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


@dataclass
class WorkspaceStatus:
    """Current workspace status information."""
    state: WorkspaceState
    workspace_path: Path
    project_count: int
    indexed_elements: int
    is_watching: bool
    last_error: Optional[str] = None


class WorkspaceManagerError(Exception):
    """Errors from workspace manager operations."""
    pass


class WorkspaceManager:
    """
    Unified workspace management component.

    Integrates workspace discovery, document indexing, and file watching
    to provide a complete workspace management solution.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize workspace manager with optional workspace path."""
        self.workspace_path = Path(workspace_path) if workspace_path else Path.home() / "software-projects"
        self.state = WorkspaceState.UNINITIALIZED
        self.last_error: Optional[str] = None

        # Components
        self._workspace_info: Optional[WorkspaceInfo] = None
        self._indexer: Optional[Indexer] = None
        self._file_watcher: Optional[WorkspaceFileWatcher] = None

        # Event handlers
        self._error_handlers: List[Callable[[str, Exception], None]] = []
        self._update_handlers: List[Callable[[], None]] = []

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def load(self, start_watching: bool = True) -> bool:
        """
        Load workspace: discover projects, build index, start file watching.

        Args:
            start_watching: Whether to start file watching after loading

        Returns:
            True if workspace loaded successfully, False otherwise
        """
        try:
            self.state = WorkspaceState.LOADING
            self.last_error = None
            self.logger.info(f"Loading workspace from {self.workspace_path}")

            # Step 1: Discover workspace and projects
            self._workspace_info = discover_workspace(str(self.workspace_path))
            project_count = len(self._workspace_info.projects)
            self.logger.info(f"Discovered {project_count} projects in workspace")

            # Step 2: Create and initialize indexer
            self._indexer = create_indexer(str(self.workspace_path))

            # Step 3: Build initial index from all markdown files
            self.logger.info("Building initial document index...")
            build_result = self._indexer.build_index(watch_files=False)

            if not build_result.success:
                error_msg = f"Failed to build initial index: {build_result.errors}"
                self.last_error = error_msg
                self.logger.error(error_msg)
                self.state = WorkspaceState.ERROR
                return False

            elements_count = build_result.elements_indexed
            self.logger.info(f"Index built successfully: {elements_count} elements indexed")

            # Step 4: Set up file watching if requested
            if start_watching:
                self._setup_file_watching()

            self.state = WorkspaceState.READY
            self.logger.info("Workspace loaded successfully")

            # Notify update handlers
            for handler in self._update_handlers:
                try:
                    handler()
                except Exception as e:
                    self.logger.warning(f"Update handler failed: {e}")

            return True

        except Exception as e:
            error_msg = f"Failed to load workspace: {e}"
            self.last_error = error_msg
            self.logger.error(error_msg, exc_info=True)
            self.state = WorkspaceState.ERROR

            # Notify error handlers
            for handler in self._error_handlers:
                try:
                    handler("workspace_load", e)
                except Exception as handler_error:
                    self.logger.warning(f"Error handler failed: {handler_error}")

            return False

    def _setup_file_watching(self):
        """Set up file system watching for continuous updates."""
        try:
            self.logger.info("Setting up file system watching...")

            # Create file watcher
            self._file_watcher = create_file_watcher()

            # Set up event handler to update indexer when files change
            def handle_file_change(file_path: Path, event_type: FileEventType):
                try:
                    if event_type in [FileEventType.MODIFIED, FileEventType.CREATED]:
                        self.logger.debug(f"File changed: {file_path}")

                        # Update indexer with the changed file
                        if self._indexer and self._indexer.is_ready():
                            update_result = self._indexer.update_file(str(file_path))
                            if update_result.success:
                                self.logger.debug(f"Index updated for {file_path}: "
                                                f"{update_result.elements_updated} elements updated")
                            else:
                                self.logger.warning(f"Failed to update index for {file_path}: "
                                                  f"{update_result.errors}")

                        # Notify update handlers
                        for handler in self._update_handlers:
                            try:
                                handler()
                            except Exception as e:
                                self.logger.warning(f"Update handler failed: {e}")

                except Exception as e:
                    self.logger.error(f"Error handling file event: {e}", exc_info=True)
                    for handler in self._error_handlers:
                        try:
                            handler("file_event", e)
                        except Exception as handler_error:
                            self.logger.warning(f"Error handler failed: {handler_error}")

            # Set up the change handler for the workspace file watcher
            self._file_watcher.add_change_handler(handle_file_change)

            # Start watching all projects in the workspace
            if self._workspace_info:
                for project in self._workspace_info.projects:
                    self._file_watcher.watch_project(str(project.path))
                    self.logger.debug(f"Started watching project: {project.name}")

            self.logger.info("File system watching started")

        except Exception as e:
            self.logger.error(f"Failed to set up file watching: {e}", exc_info=True)
            # Don't fail the entire load process if watching fails
            self._file_watcher = None

    def refresh(self) -> bool:
        """
        Refresh workspace: re-discover projects and rebuild index.

        Returns:
            True if refresh succeeded, False otherwise
        """
        try:
            if not self._indexer:
                return False

            self.logger.info("Refreshing workspace...")

            # Re-discover workspace
            self._workspace_info = discover_workspace(str(self.workspace_path))

            # Rebuild index from scratch
            build_result = self._indexer.build_index(watch_files=False)

            if build_result.success:
                self.logger.info(f"Workspace refreshed: {build_result.elements_indexed} elements indexed")

                # Notify update handlers
                for handler in self._update_handlers:
                    try:
                        handler()
                    except Exception as e:
                        self.logger.warning(f"Update handler failed: {e}")

                return True
            else:
                self.logger.error(f"Failed to refresh workspace: {build_result.errors}")
                return False

        except Exception as e:
            error_msg = f"Error refreshing workspace: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.last_error = error_msg
            return False

    def stop(self):
        """Stop file watching and clean up resources."""
        try:
            if self._file_watcher:
                self._file_watcher.stop_all_watching()
                self._file_watcher = None
                self.logger.info("File watching stopped")

            if self._indexer:
                self._indexer.stop_file_watching()

        except Exception as e:
            self.logger.error(f"Error stopping workspace manager: {e}", exc_info=True)

    # Property access methods

    def get_status(self) -> WorkspaceStatus:
        """Get current workspace status."""
        project_count = len(self._workspace_info.projects) if self._workspace_info else 0
        indexed_elements = 0
        is_watching = self._file_watcher is not None

        if self._indexer:
            stats = self._indexer.get_statistics()
            indexed_elements = stats.total_elements

        return WorkspaceStatus(
            state=self.state,
            workspace_path=self.workspace_path,
            project_count=project_count,
            indexed_elements=indexed_elements,
            is_watching=is_watching,
            last_error=self.last_error
        )

    def get_workspace_info(self) -> Optional[WorkspaceInfo]:
        """Get workspace discovery information."""
        return self._workspace_info

    def get_indexer(self) -> Optional[Indexer]:
        """Get access to the document indexer."""
        return self._indexer

    def get_projects(self) -> List[ProjectInfo]:
        """Get list of discovered projects."""
        if self._workspace_info:
            return self._workspace_info.projects
        return []

    def is_ready(self) -> bool:
        """Check if workspace is ready for operations."""
        return (self.state == WorkspaceState.READY and
                self._indexer is not None and
                self._indexer.is_ready())

    # Event handler management

    def add_error_handler(self, handler: Callable[[str, Exception], None]):
        """Add handler for error events."""
        self._error_handlers.append(handler)

    def add_update_handler(self, handler: Callable[[], None]):
        """Add handler for workspace update events."""
        self._update_handlers.append(handler)

    def remove_error_handler(self, handler: Callable[[str, Exception], None]):
        """Remove error event handler."""
        if handler in self._error_handlers:
            self._error_handlers.remove(handler)

    def remove_update_handler(self, handler: Callable[[], None]):
        """Remove workspace update event handler."""
        if handler in self._update_handlers:
            self._update_handlers.remove(handler)


# Factory function for easy instantiation
def create_workspace_manager(workspace_path: Optional[str] = None) -> WorkspaceManager:
    """
    Create a new WorkspaceManager instance.

    Args:
        workspace_path: Optional path to workspace directory

    Returns:
        WorkspaceManager instance
    """
    return WorkspaceManager(workspace_path)