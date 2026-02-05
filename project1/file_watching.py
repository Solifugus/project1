"""
File system watching for Project1 workspace monitoring.

This module implements T:0009, monitoring markdown files for external changes
and triggering re-parsing when files are modified, added, or deleted.
"""

import os
import time
from pathlib import Path
from typing import List, Callable, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
from threading import Thread, Event, Lock
import hashlib


class FileEventType(Enum):
    """Types of file system events."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileSystemEvent:
    """
    Represents a file system event (D:FileSystemEvent).

    Contains information about file changes that may require re-indexing.
    """
    event_type: FileEventType     # Type of file system event
    file_path: Path              # Path to the affected file
    is_directory: bool           # Whether the path is a directory
    timestamp: float             # Unix timestamp when event occurred

    # For move/rename events
    src_path: Optional[Path] = None    # Original path (for move events)

    # Event metadata
    size_bytes: Optional[int] = None   # File size if available
    checksum: Optional[str] = None     # File content checksum for change detection

    def __str__(self) -> str:
        """String representation of the event."""
        event_desc = f"{self.event_type.value.upper()}"

        if self.event_type == FileEventType.MOVED and self.src_path:
            return f"{event_desc}: {self.src_path} -> {self.file_path}"
        else:
            return f"{event_desc}: {self.file_path}"


class FileWatcherError(Exception):
    """Exception raised when file watching fails."""
    pass


class FileSystemWatcher:
    """
    File system watcher interface (I:FileSystemWatcher).

    Provides abstract interface for file system monitoring implementations.
    """

    def start_watching(self, path: str) -> None:
        """Start watching a directory for file changes."""
        raise NotImplementedError

    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        raise NotImplementedError

    def add_event_handler(self, handler: Callable[[FileSystemEvent], None]) -> None:
        """Add a callback handler for file system events."""
        raise NotImplementedError

    def remove_event_handler(self, handler: Callable[[FileSystemEvent], None]) -> None:
        """Remove a callback handler for file system events."""
        raise NotImplementedError


class PollingFileWatcher(FileSystemWatcher):
    """
    Polling-based file system watcher implementation.

    Uses periodic directory scanning to detect file changes.
    Fallback implementation that works on all platforms.
    """

    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize polling watcher.

        Args:
            poll_interval: Time between polling checks in seconds.
        """
        self.poll_interval = poll_interval
        self.watch_paths: Set[Path] = set()
        self.event_handlers: List[Callable[[FileSystemEvent], None]] = []
        self.file_states: Dict[Path, Dict] = {}  # Track file states

        self._watch_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._lock = Lock()
        self._is_watching = False

    def _calculate_file_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate file content checksum for change detection."""
        try:
            if not file_path.exists() or not file_path.is_file():
                return None

            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def _get_file_state(self, file_path: Path) -> Optional[Dict]:
        """Get current file state (size, mtime, checksum)."""
        try:
            if not file_path.exists():
                return None

            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'checksum': self._calculate_file_checksum(file_path),
                'is_file': file_path.is_file()
            }
        except (OSError, PermissionError):
            return None

    def _scan_directory(self, directory: Path) -> None:
        """Scan directory for changes and generate events."""
        if not directory.exists() or not directory.is_dir():
            return

        try:
            # Get current files
            current_files = set()

            # Scan for markdown files recursively
            for file_path in directory.rglob("*.md"):
                if file_path.is_file():
                    current_files.add(file_path)

            # Check for new or modified files
            for file_path in current_files:
                current_state = self._get_file_state(file_path)
                previous_state = self.file_states.get(file_path)

                if current_state is None:
                    continue

                if previous_state is None:
                    # New file
                    event = FileSystemEvent(
                        event_type=FileEventType.CREATED,
                        file_path=file_path,
                        is_directory=False,
                        timestamp=time.time(),
                        size_bytes=current_state['size'],
                        checksum=current_state['checksum']
                    )
                    self._emit_event(event)

                elif (current_state['mtime'] != previous_state['mtime'] or
                      current_state['checksum'] != previous_state['checksum']):
                    # Modified file
                    event = FileSystemEvent(
                        event_type=FileEventType.MODIFIED,
                        file_path=file_path,
                        is_directory=False,
                        timestamp=time.time(),
                        size_bytes=current_state['size'],
                        checksum=current_state['checksum']
                    )
                    self._emit_event(event)

                # Update stored state
                self.file_states[file_path] = current_state

            # Check for deleted files
            previous_files = set(self.file_states.keys())
            deleted_files = previous_files - current_files

            for file_path in deleted_files:
                event = FileSystemEvent(
                    event_type=FileEventType.DELETED,
                    file_path=file_path,
                    is_directory=False,
                    timestamp=time.time()
                )
                self._emit_event(event)
                del self.file_states[file_path]

        except (OSError, PermissionError) as e:
            # Log error but continue watching
            print(f"Warning: Error scanning directory {directory}: {e}")

    def _emit_event(self, event: FileSystemEvent) -> None:
        """Emit event to all registered handlers."""
        with self._lock:
            for handler in self.event_handlers:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Warning: Event handler failed: {e}")

    def _watch_loop(self) -> None:
        """Main watching loop that runs in background thread."""
        while not self._stop_event.wait(self.poll_interval):
            with self._lock:
                watch_paths = self.watch_paths.copy()

            for path in watch_paths:
                self._scan_directory(path)

    def add_event_handler(self, handler: Callable[[FileSystemEvent], None]) -> None:
        """Add a callback handler for file system events."""
        with self._lock:
            if handler not in self.event_handlers:
                self.event_handlers.append(handler)

    def remove_event_handler(self, handler: Callable[[FileSystemEvent], None]) -> None:
        """Remove a callback handler for file system events."""
        with self._lock:
            if handler in self.event_handlers:
                self.event_handlers.remove(handler)

    def start_watching(self, path: str) -> None:
        """Start watching a directory for file changes."""
        watch_path = Path(path).resolve()

        if not watch_path.exists():
            raise FileWatcherError(f"Watch path does not exist: {watch_path}")

        if not watch_path.is_dir():
            raise FileWatcherError(f"Watch path is not a directory: {watch_path}")

        with self._lock:
            self.watch_paths.add(watch_path)

            # Initial scan to populate file states
            self._scan_directory(watch_path)

            # Start watch thread if not already running
            if not self._is_watching:
                self._stop_event.clear()
                self._watch_thread = Thread(target=self._watch_loop, daemon=True)
                self._watch_thread.start()
                self._is_watching = True

    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        with self._lock:
            if self._is_watching:
                self._stop_event.set()
                self._is_watching = False

            if self._watch_thread and self._watch_thread.is_alive():
                self._watch_thread.join(timeout=5.0)

            self.watch_paths.clear()
            self.file_states.clear()

    def is_watching(self) -> bool:
        """Check if watcher is currently active."""
        return self._is_watching

    def get_watched_paths(self) -> List[Path]:
        """Get list of currently watched paths."""
        with self._lock:
            return list(self.watch_paths)


# Try to use watchdog library for better performance if available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent, FileMovedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


if WATCHDOG_AVAILABLE:
    class WatchdogFileWatcher(FileSystemWatcher):
        """
        Watchdog-based file system watcher implementation.

        Uses the watchdog library for efficient, platform-native file watching.
        """

        class MarkdownEventHandler(FileSystemEventHandler):
            """Event handler that filters for markdown files."""

            def __init__(self, watcher: 'WatchdogFileWatcher'):
                self.watcher = watcher
                super().__init__()

            def _should_process_event(self, event) -> bool:
                """Check if event should be processed (markdown files only)."""
                if event.is_directory:
                    return False

                path = Path(event.src_path)
                return path.suffix.lower() == '.md'

            def on_created(self, event):
                if self._should_process_event(event):
                    fs_event = FileSystemEvent(
                        event_type=FileEventType.CREATED,
                        file_path=Path(event.src_path),
                        is_directory=event.is_directory,
                        timestamp=time.time()
                    )
                    self.watcher._emit_event(fs_event)

            def on_modified(self, event):
                if self._should_process_event(event):
                    fs_event = FileSystemEvent(
                        event_type=FileEventType.MODIFIED,
                        file_path=Path(event.src_path),
                        is_directory=event.is_directory,
                        timestamp=time.time()
                    )
                    self.watcher._emit_event(fs_event)

            def on_deleted(self, event):
                if self._should_process_event(event):
                    fs_event = FileSystemEvent(
                        event_type=FileEventType.DELETED,
                        file_path=Path(event.src_path),
                        is_directory=event.is_directory,
                        timestamp=time.time()
                    )
                    self.watcher._emit_event(fs_event)

            def on_moved(self, event):
                if self._should_process_event(event):
                    fs_event = FileSystemEvent(
                        event_type=FileEventType.MOVED,
                        file_path=Path(event.dest_path),
                        src_path=Path(event.src_path),
                        is_directory=event.is_directory,
                        timestamp=time.time()
                    )
                    self.watcher._emit_event(fs_event)

        def __init__(self):
            """Initialize watchdog-based watcher."""
            self.observer = Observer()
            self.event_handlers: List[Callable[[FileSystemEvent], None]] = []
            self.watch_handles = []
            self._lock = Lock()
            self.markdown_handler = self.MarkdownEventHandler(self)

        def _emit_event(self, event: FileSystemEvent) -> None:
            """Emit event to all registered handlers."""
            with self._lock:
                for handler in self.event_handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"Warning: Event handler failed: {e}")

        def add_event_handler(self, handler: Callable[[FileSystemEvent], None]) -> None:
            """Add a callback handler for file system events."""
            with self._lock:
                if handler not in self.event_handlers:
                    self.event_handlers.append(handler)

        def remove_event_handler(self, handler: Callable[[FileSystemEvent], None]) -> None:
            """Remove a callback handler for file system events."""
            with self._lock:
                if handler in self.event_handlers:
                    self.event_handlers.remove(handler)

        def start_watching(self, path: str) -> None:
            """Start watching a directory for file changes."""
            watch_path = Path(path).resolve()

            if not watch_path.exists():
                raise FileWatcherError(f"Watch path does not exist: {watch_path}")

            if not watch_path.is_dir():
                raise FileWatcherError(f"Watch path is not a directory: {watch_path}")

            # Schedule watching for the path
            watch_handle = self.observer.schedule(
                self.markdown_handler,
                str(watch_path),
                recursive=True
            )

            with self._lock:
                self.watch_handles.append((watch_handle, watch_path))

            # Start observer if not already running
            if not self.observer.is_alive():
                self.observer.start()

        def stop_watching(self) -> None:
            """Stop watching for file changes."""
            with self._lock:
                # Unschedule all watches
                for watch_handle, _ in self.watch_handles:
                    self.observer.unschedule(watch_handle)
                self.watch_handles.clear()

            # Stop observer
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5.0)

        def is_watching(self) -> bool:
            """Check if watcher is currently active."""
            return self.observer.is_alive() and len(self.watch_handles) > 0

        def get_watched_paths(self) -> List[Path]:
            """Get list of currently watched paths."""
            with self._lock:
                return [path for _, path in self.watch_handles]


class WorkspaceFileWatcher:
    """
    High-level workspace file watcher for Project1.

    Monitors markdown files in workspace projects and triggers re-parsing
    when files are modified externally.
    """

    def __init__(self, use_watchdog: bool = True):
        """
        Initialize workspace file watcher.

        Args:
            use_watchdog: Whether to use watchdog library if available.
        """
        # Choose watcher implementation
        if use_watchdog and WATCHDOG_AVAILABLE:
            self.watcher = WatchdogFileWatcher()
            self.watcher_type = "watchdog"
        else:
            self.watcher = PollingFileWatcher(poll_interval=2.0)
            self.watcher_type = "polling"

        self.change_handlers: List[Callable[[Path, FileEventType], None]] = []
        self.watched_projects: Set[Path] = set()
        self._setup_event_handling()

    def _setup_event_handling(self) -> None:
        """Set up internal event handling."""
        self.watcher.add_event_handler(self._handle_file_event)

    def _handle_file_event(self, event: FileSystemEvent) -> None:
        """Handle file system events and trigger change handlers."""
        # Filter for markdown files in watched projects
        if not event.file_path.suffix.lower() == '.md':
            return

        # Check if file is in a watched project
        for project_path in self.watched_projects:
            try:
                event.file_path.relative_to(project_path)
                # File is in this project, trigger handlers
                for handler in self.change_handlers:
                    try:
                        handler(event.file_path, event.event_type)
                    except Exception as e:
                        print(f"Warning: Change handler failed: {e}")
                break
            except ValueError:
                continue  # File not in this project

    def add_change_handler(self, handler: Callable[[Path, FileEventType], None]) -> None:
        """
        Add a handler for file changes.

        Args:
            handler: Callback that receives (file_path, event_type) when changes occur.
        """
        if handler not in self.change_handlers:
            self.change_handlers.append(handler)

    def remove_change_handler(self, handler: Callable[[Path, FileEventType], None]) -> None:
        """Remove a change handler."""
        if handler in self.change_handlers:
            self.change_handlers.remove(handler)

    def watch_project(self, project_path: str) -> None:
        """
        Start watching a project directory for markdown file changes.

        Args:
            project_path: Path to project directory to watch.

        Raises:
            FileWatcherError: If watching setup fails.
        """
        project_path_obj = Path(project_path).resolve()

        if not project_path_obj.exists():
            raise FileWatcherError(f"Project path does not exist: {project_path_obj}")

        if not project_path_obj.is_dir():
            raise FileWatcherError(f"Project path is not a directory: {project_path_obj}")

        self.watched_projects.add(project_path_obj)
        self.watcher.start_watching(str(project_path_obj))

    def unwatch_project(self, project_path: str) -> None:
        """Stop watching a project directory."""
        project_path_obj = Path(project_path).resolve()
        self.watched_projects.discard(project_path_obj)

        # If no projects are being watched, stop the watcher
        if not self.watched_projects:
            self.watcher.stop_watching()

    def stop_all_watching(self) -> None:
        """Stop watching all projects."""
        self.watched_projects.clear()
        self.watcher.stop_watching()

    def get_watched_projects(self) -> List[Path]:
        """Get list of currently watched project paths."""
        return list(self.watched_projects)

    def get_watcher_info(self) -> Dict[str, any]:
        """Get information about the file watcher."""
        return {
            'watcher_type': self.watcher_type,
            'is_watching': self.watcher.is_watching(),
            'watched_projects': [str(p) for p in self.watched_projects],
            'num_change_handlers': len(self.change_handlers),
            'watchdog_available': WATCHDOG_AVAILABLE
        }


def create_file_watcher(use_watchdog: bool = True) -> WorkspaceFileWatcher:
    """
    Convenience function to create a workspace file watcher.

    Args:
        use_watchdog: Whether to use watchdog library if available.

    Returns:
        WorkspaceFileWatcher instance.
    """
    return WorkspaceFileWatcher(use_watchdog=use_watchdog)