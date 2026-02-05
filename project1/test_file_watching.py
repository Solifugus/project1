"""
Tests for file system watching functionality.

This validates T:0009 acceptance criteria.
"""

import os
import time
import tempfile
from pathlib import Path
from threading import Event
from file_watching import (
    FileSystemEvent, FileEventType, PollingFileWatcher, WorkspaceFileWatcher,
    FileWatcherError, create_file_watcher
)


class EventCollector:
    """Helper class to collect file system events for testing."""

    def __init__(self):
        self.events = []
        self.event_received = Event()

    def handle_event(self, event: FileSystemEvent) -> None:
        """Handle file system event."""
        self.events.append(event)
        self.event_received.set()

    def handle_change(self, file_path: Path, event_type: FileEventType) -> None:
        """Handle workspace file change."""
        event = FileSystemEvent(
            event_type=event_type,
            file_path=file_path,
            is_directory=False,
            timestamp=time.time()
        )
        self.events.append(event)
        self.event_received.set()

    def wait_for_event(self, timeout: float = 5.0) -> bool:
        """Wait for an event to be received."""
        result = self.event_received.wait(timeout)
        self.event_received.clear()
        return result

    def clear_events(self) -> None:
        """Clear collected events."""
        self.events.clear()
        self.event_received.clear()


def test_file_system_event_creation():
    """Test FileSystemEvent data structure creation."""
    file_path = Path("/test/file.md")
    event = FileSystemEvent(
        event_type=FileEventType.CREATED,
        file_path=file_path,
        is_directory=False,
        timestamp=time.time(),
        size_bytes=1024,
        checksum="abc123"
    )

    assert event.event_type == FileEventType.CREATED
    assert event.file_path == file_path
    assert not event.is_directory
    assert event.size_bytes == 1024
    assert event.checksum == "abc123"
    assert "CREATED:" in str(event)


def test_file_system_event_move():
    """Test FileSystemEvent for move operations."""
    src_path = Path("/test/old.md")
    dest_path = Path("/test/new.md")
    event = FileSystemEvent(
        event_type=FileEventType.MOVED,
        file_path=dest_path,
        is_directory=False,
        timestamp=time.time(),
        src_path=src_path
    )

    assert event.event_type == FileEventType.MOVED
    assert event.src_path == src_path
    assert event.file_path == dest_path
    assert str(src_path) in str(event) and str(dest_path) in str(event)


def test_polling_file_watcher_initialization():
    """Test PollingFileWatcher initialization."""
    watcher = PollingFileWatcher(poll_interval=0.5)
    assert watcher.poll_interval == 0.5
    assert not watcher.is_watching()
    assert len(watcher.get_watched_paths()) == 0


def test_polling_file_watcher_event_handlers():
    """Test event handler management."""
    watcher = PollingFileWatcher()
    collector = EventCollector()

    # Add handler
    watcher.add_event_handler(collector.handle_event)
    assert len(watcher.event_handlers) == 1

    # Remove handler
    watcher.remove_event_handler(collector.handle_event)
    assert len(watcher.event_handlers) == 0

    # Adding same handler twice should not duplicate
    watcher.add_event_handler(collector.handle_event)
    watcher.add_event_handler(collector.handle_event)
    assert len(watcher.event_handlers) == 1


def test_file_checksum_calculation():
    """Test file checksum calculation for change detection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test.md"

        watcher = PollingFileWatcher()

        # Test non-existent file
        checksum = watcher._calculate_file_checksum(test_file)
        assert checksum is None

        # Test existing file
        test_file.write_text("# Test Content\n\nSome content here.")
        checksum1 = watcher._calculate_file_checksum(test_file)
        assert checksum1 is not None
        assert len(checksum1) == 32  # MD5 hex digest

        # Test same content produces same checksum
        checksum2 = watcher._calculate_file_checksum(test_file)
        assert checksum1 == checksum2

        # Test different content produces different checksum
        test_file.write_text("# Different Content\n\nDifferent content here.")
        checksum3 = watcher._calculate_file_checksum(test_file)
        assert checksum3 != checksum1


def test_polling_file_watcher_file_creation():
    """Test detection of file creation events."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        watcher = PollingFileWatcher(poll_interval=0.1)
        collector = EventCollector()

        watcher.add_event_handler(collector.handle_event)

        try:
            # Start watching
            watcher.start_watching(str(temp_path))
            assert watcher.is_watching()

            # Wait a bit for initial scan
            time.sleep(0.2)
            collector.clear_events()

            # Create a markdown file
            test_file = temp_path / "new_file.md"
            test_file.write_text("# New File\n\nContent here.")

            # Wait for event detection
            event_received = collector.wait_for_event(timeout=2.0)
            assert event_received, "Should have detected file creation"

            # Check event details
            creation_events = [e for e in collector.events if e.event_type == FileEventType.CREATED]
            assert len(creation_events) >= 1

            event = creation_events[0]
            assert event.file_path.name == "new_file.md"
            assert event.size_bytes > 0
            assert event.checksum is not None

        finally:
            watcher.stop_watching()


def test_polling_file_watcher_file_modification():
    """Test detection of file modification events."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "existing.md"

        # Create initial file
        test_file.write_text("# Original Content\n")

        watcher = PollingFileWatcher(poll_interval=0.1)
        collector = EventCollector()

        watcher.add_event_handler(collector.handle_event)

        try:
            # Start watching (initial scan will detect existing file)
            watcher.start_watching(str(temp_path))

            # Wait for initial scan
            time.sleep(0.2)
            collector.clear_events()

            # Modify the file
            test_file.write_text("# Modified Content\n\nNew content added.")

            # Wait for event detection
            event_received = collector.wait_for_event(timeout=2.0)
            assert event_received, "Should have detected file modification"

            # Check event details
            modification_events = [e for e in collector.events if e.event_type == FileEventType.MODIFIED]
            assert len(modification_events) >= 1

            event = modification_events[0]
            assert event.file_path.name == "existing.md"

        finally:
            watcher.stop_watching()


def test_polling_file_watcher_file_deletion():
    """Test detection of file deletion events."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "to_delete.md"

        # Create initial file
        test_file.write_text("# File to Delete\n")

        watcher = PollingFileWatcher(poll_interval=0.1)
        collector = EventCollector()

        watcher.add_event_handler(collector.handle_event)

        try:
            # Start watching (initial scan will detect existing file)
            watcher.start_watching(str(temp_path))

            # Wait for initial scan
            time.sleep(0.2)
            collector.clear_events()

            # Delete the file
            test_file.unlink()

            # Wait for event detection
            event_received = collector.wait_for_event(timeout=2.0)
            assert event_received, "Should have detected file deletion"

            # Check event details
            deletion_events = [e for e in collector.events if e.event_type == FileEventType.DELETED]
            assert len(deletion_events) >= 1

            event = deletion_events[0]
            assert event.file_path.name == "to_delete.md"

        finally:
            watcher.stop_watching()


def test_polling_file_watcher_non_markdown_files():
    """Test that non-markdown files are ignored."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        watcher = PollingFileWatcher(poll_interval=0.1)
        collector = EventCollector()

        watcher.add_event_handler(collector.handle_event)

        try:
            # Start watching
            watcher.start_watching(str(temp_path))

            # Wait for initial scan
            time.sleep(0.2)
            collector.clear_events()

            # Create non-markdown files
            (temp_path / "test.txt").write_text("Text file")
            (temp_path / "config.json").write_text('{"key": "value"}')
            (temp_path / "script.py").write_text("print('hello')")

            # Create a markdown file
            (temp_path / "document.md").write_text("# Document\n")

            # Wait for events
            time.sleep(0.5)

            # Should only detect the markdown file
            creation_events = [e for e in collector.events if e.event_type == FileEventType.CREATED]
            assert len(creation_events) == 1
            assert creation_events[0].file_path.name == "document.md"

        finally:
            watcher.stop_watching()


def test_polling_file_watcher_error_handling():
    """Test error handling in PollingFileWatcher."""
    watcher = PollingFileWatcher()

    # Test watching non-existent directory
    try:
        watcher.start_watching("/nonexistent/directory")
        assert False, "Should raise FileWatcherError"
    except FileWatcherError as e:
        assert "does not exist" in str(e)

    # Test watching a file instead of directory
    with tempfile.NamedTemporaryFile() as temp_file:
        try:
            watcher.start_watching(temp_file.name)
            assert False, "Should raise FileWatcherError"
        except FileWatcherError as e:
            assert "not a directory" in str(e)


def test_workspace_file_watcher_initialization():
    """Test WorkspaceFileWatcher initialization."""
    # Test with polling watcher (always available)
    watcher = WorkspaceFileWatcher(use_watchdog=False)
    assert watcher.watcher_type == "polling"
    assert not watcher.watcher.is_watching()
    assert len(watcher.get_watched_projects()) == 0

    info = watcher.get_watcher_info()
    assert info['watcher_type'] == "polling"
    assert info['is_watching'] is False
    assert info['num_change_handlers'] == 0


def test_workspace_file_watcher_change_handlers():
    """Test change handler management in WorkspaceFileWatcher."""
    watcher = WorkspaceFileWatcher(use_watchdog=False)
    collector = EventCollector()

    # Add handler
    watcher.add_change_handler(collector.handle_change)
    assert len(watcher.change_handlers) == 1

    # Remove handler
    watcher.remove_change_handler(collector.handle_change)
    assert len(watcher.change_handlers) == 0


def test_workspace_file_watcher_project_watching():
    """Test project watching functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "test_project"
        project_path.mkdir()

        watcher = WorkspaceFileWatcher(use_watchdog=False)
        collector = EventCollector()

        # Cast to PollingFileWatcher to adjust poll interval
        if hasattr(watcher.watcher, 'poll_interval'):
            watcher.watcher.poll_interval = 0.1

        watcher.add_change_handler(collector.handle_change)

        try:
            # Start watching project
            watcher.watch_project(str(project_path))
            assert len(watcher.get_watched_projects()) == 1
            assert project_path in watcher.get_watched_projects()

            # Wait for initial scan
            time.sleep(0.2)
            collector.clear_events()

            # Create a markdown file in the project
            md_file = project_path / "software-design.md"
            md_file.write_text("# Software Design\n\nDesign content here.")

            # Wait for event detection
            event_received = collector.wait_for_event(timeout=2.0)
            assert event_received, "Should have detected markdown file creation"

            # Check event
            assert len(collector.events) >= 1
            event = collector.events[0]
            assert event.file_path.name == "software-design.md"
            assert event.event_type == FileEventType.CREATED

        finally:
            watcher.stop_all_watching()


def test_workspace_file_watcher_multiple_projects():
    """Test watching multiple projects simultaneously."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create multiple project directories
        project1_path = temp_path / "project1"
        project2_path = temp_path / "project2"
        project1_path.mkdir()
        project2_path.mkdir()

        watcher = WorkspaceFileWatcher(use_watchdog=False)
        collector = EventCollector()

        # Cast to PollingFileWatcher to adjust poll interval
        if hasattr(watcher.watcher, 'poll_interval'):
            watcher.watcher.poll_interval = 0.1

        watcher.add_change_handler(collector.handle_change)

        try:
            # Watch both projects
            watcher.watch_project(str(project1_path))
            watcher.watch_project(str(project2_path))

            assert len(watcher.get_watched_projects()) == 2

            # Wait for initial scan
            time.sleep(0.2)
            collector.clear_events()

            # Create files in different projects
            (project1_path / "design1.md").write_text("# Design 1")
            (project2_path / "design2.md").write_text("# Design 2")

            # Wait for events
            time.sleep(1.0)

            # Should detect files from both projects
            creation_events = [e for e in collector.events if e.event_type == FileEventType.CREATED]
            assert len(creation_events) >= 2

            file_names = {e.file_path.name for e in creation_events}
            assert "design1.md" in file_names
            assert "design2.md" in file_names

        finally:
            watcher.stop_all_watching()


def test_workspace_file_watcher_unwatch_project():
    """Test unwatching individual projects."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "test_project"
        project_path.mkdir()

        watcher = WorkspaceFileWatcher(use_watchdog=False)

        # Start watching
        watcher.watch_project(str(project_path))
        assert len(watcher.get_watched_projects()) == 1

        # Unwatch project
        watcher.unwatch_project(str(project_path))
        assert len(watcher.get_watched_projects()) == 0
        assert not watcher.watcher.is_watching()


def test_workspace_file_watcher_error_handling():
    """Test error handling in WorkspaceFileWatcher."""
    watcher = WorkspaceFileWatcher(use_watchdog=False)

    # Test watching non-existent project
    try:
        watcher.watch_project("/nonexistent/project")
        assert False, "Should raise FileWatcherError"
    except FileWatcherError as e:
        assert "does not exist" in str(e)


def test_workspace_file_watcher_subdirectories():
    """Test that subdirectories are watched recursively."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = temp_path / "test_project"
        subdir_path = project_path / "docs"

        project_path.mkdir()
        subdir_path.mkdir()

        watcher = WorkspaceFileWatcher(use_watchdog=False)
        collector = EventCollector()

        # Cast to PollingFileWatcher to adjust poll interval
        if hasattr(watcher.watcher, 'poll_interval'):
            watcher.watcher.poll_interval = 0.1

        watcher.add_change_handler(collector.handle_change)

        try:
            # Start watching project
            watcher.watch_project(str(project_path))

            # Wait for initial scan
            time.sleep(0.2)
            collector.clear_events()

            # Create file in subdirectory
            subfile = subdir_path / "documentation.md"
            subfile.write_text("# Documentation\n")

            # Wait for event detection
            event_received = collector.wait_for_event(timeout=2.0)
            assert event_received, "Should have detected file creation in subdirectory"

            # Check event
            creation_events = [e for e in collector.events if e.event_type == FileEventType.CREATED]
            assert len(creation_events) >= 1
            assert creation_events[0].file_path.name == "documentation.md"

        finally:
            watcher.stop_all_watching()


def test_convenience_function():
    """Test convenience function for creating file watcher."""
    watcher = create_file_watcher(use_watchdog=False)
    assert isinstance(watcher, WorkspaceFileWatcher)
    assert watcher.watcher_type == "polling"

    info = watcher.get_watcher_info()
    assert 'watcher_type' in info
    assert 'watchdog_available' in info


def test_event_handler_exception_handling():
    """Test that exceptions in event handlers don't crash the watcher."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        def failing_handler(event: FileSystemEvent) -> None:
            raise Exception("Handler error")

        def working_handler(event: FileSystemEvent) -> None:
            working_handler.called = True

        working_handler.called = False

        watcher = PollingFileWatcher(poll_interval=0.1)
        watcher.add_event_handler(failing_handler)
        watcher.add_event_handler(working_handler)

        try:
            # Start watching
            watcher.start_watching(str(temp_path))

            # Wait for initial scan
            time.sleep(0.2)

            # Create a file
            test_file = temp_path / "test.md"
            test_file.write_text("# Test")

            # Wait for events
            time.sleep(0.5)

            # Working handler should still be called despite failing handler
            assert working_handler.called

        finally:
            watcher.stop_watching()


if __name__ == "__main__":
    # Run all tests manually
    print("Running file watching tests...")

    test_file_system_event_creation()
    print("✓ FileSystemEvent creation")

    test_file_system_event_move()
    print("✓ FileSystemEvent move operations")

    test_polling_file_watcher_initialization()
    print("✓ PollingFileWatcher initialization")

    test_polling_file_watcher_event_handlers()
    print("✓ Event handler management")

    test_file_checksum_calculation()
    print("✓ File checksum calculation")

    test_polling_file_watcher_file_creation()
    print("✓ File creation detection")

    test_polling_file_watcher_file_modification()
    print("✓ File modification detection")

    test_polling_file_watcher_file_deletion()
    print("✓ File deletion detection")

    test_polling_file_watcher_non_markdown_files()
    print("✓ Non-markdown file filtering")

    test_polling_file_watcher_error_handling()
    print("✓ PollingFileWatcher error handling")

    test_workspace_file_watcher_initialization()
    print("✓ WorkspaceFileWatcher initialization")

    test_workspace_file_watcher_change_handlers()
    print("✓ Change handler management")

    test_workspace_file_watcher_project_watching()
    print("✓ Project watching")

    test_workspace_file_watcher_multiple_projects()
    print("✓ Multiple project watching")

    test_workspace_file_watcher_unwatch_project()
    print("✓ Project unwatching")

    test_workspace_file_watcher_error_handling()
    print("✓ WorkspaceFileWatcher error handling")

    test_workspace_file_watcher_subdirectories()
    print("✓ Recursive subdirectory watching")

    test_convenience_function()
    print("✓ Convenience function")

    test_event_handler_exception_handling()
    print("✓ Exception handling in event handlers")

    print("\nAll tests passed! T:0009 file system watching is complete.")