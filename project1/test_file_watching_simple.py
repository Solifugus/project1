"""
Simplified tests for file watching functionality to verify core features.
"""

import os
import time
import tempfile
from pathlib import Path
from file_watching import (
    FileSystemEvent, FileEventType, PollingFileWatcher, WorkspaceFileWatcher,
    FileWatcherError, create_file_watcher
)


def test_basic_functionality():
    """Test basic file watching functionality without threading."""
    print("Testing basic file watching functionality...")

    # Test FileSystemEvent creation
    event = FileSystemEvent(
        event_type=FileEventType.CREATED,
        file_path=Path("/test/file.md"),
        is_directory=False,
        timestamp=time.time()
    )
    assert event.event_type == FileEventType.CREATED
    assert "CREATED:" in str(event)
    print("✓ FileSystemEvent creation")

    # Test PollingFileWatcher initialization
    watcher = PollingFileWatcher(poll_interval=0.1)
    assert watcher.poll_interval == 0.1
    assert not watcher.is_watching()
    print("✓ PollingFileWatcher initialization")

    # Test file state detection
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test.md"

        # Test non-existent file
        state = watcher._get_file_state(test_file)
        assert state is None

        # Test existing file
        test_file.write_text("# Test Content")
        state = watcher._get_file_state(test_file)
        assert state is not None
        assert state['size'] > 0
        assert state['is_file'] is True

        # Test checksum calculation
        checksum1 = watcher._calculate_file_checksum(test_file)
        checksum2 = watcher._calculate_file_checksum(test_file)
        assert checksum1 == checksum2  # Same content = same checksum

        # Modify file and check checksum changes
        test_file.write_text("# Different Content")
        checksum3 = watcher._calculate_file_checksum(test_file)
        assert checksum3 != checksum1  # Different content = different checksum

    print("✓ File state detection and checksums")

    # Test error handling
    try:
        watcher.start_watching("/nonexistent/directory")
        assert False, "Should raise FileWatcherError"
    except FileWatcherError as e:
        assert "does not exist" in str(e)
    print("✓ Error handling")

    # Test WorkspaceFileWatcher initialization
    workspace_watcher = WorkspaceFileWatcher(use_watchdog=False)
    assert workspace_watcher.watcher_type == "polling"
    assert len(workspace_watcher.get_watched_projects()) == 0

    info = workspace_watcher.get_watcher_info()
    assert info['watcher_type'] == "polling"
    assert info['is_watching'] is False

    print("✓ WorkspaceFileWatcher initialization")

    # Test convenience function
    convenience_watcher = create_file_watcher(use_watchdog=False)
    assert isinstance(convenience_watcher, WorkspaceFileWatcher)
    print("✓ Convenience function")

    print("✓ All basic tests passed!")


def test_file_scanning():
    """Test file scanning functionality without background threads."""
    print("\nTesting file scanning functionality...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        watcher = PollingFileWatcher(poll_interval=1.0)  # Won't start background thread

        # Create initial files
        md_file1 = temp_path / "doc1.md"
        md_file2 = temp_path / "doc2.md"
        non_md_file = temp_path / "readme.txt"

        md_file1.write_text("# Document 1")
        non_md_file.write_text("This is not markdown")

        # Set up event collection
        events = []
        def collect_events(event):
            events.append(event)

        watcher.add_event_handler(collect_events)

        # Initial scan (populate file states)
        watcher._scan_directory(temp_path)

        # Should have detected the markdown file but not the txt file
        creation_events = [e for e in events if e.event_type == FileEventType.CREATED]
        assert len(creation_events) == 1
        assert creation_events[0].file_path.name == "doc1.md"

        events.clear()

        # Create another markdown file
        md_file2.write_text("# Document 2")
        watcher._scan_directory(temp_path)

        # Should detect new file
        creation_events = [e for e in events if e.event_type == FileEventType.CREATED]
        assert len(creation_events) == 1
        assert creation_events[0].file_path.name == "doc2.md"

        events.clear()

        # Modify existing file
        md_file1.write_text("# Modified Document 1\n\nNew content added.")
        time.sleep(0.1)  # Ensure different timestamp
        watcher._scan_directory(temp_path)

        # Should detect modification
        modification_events = [e for e in events if e.event_type == FileEventType.MODIFIED]
        assert len(modification_events) >= 1
        assert any(e.file_path.name == "doc1.md" for e in modification_events)

        events.clear()

        # Delete file
        md_file2.unlink()
        watcher._scan_directory(temp_path)

        # Should detect deletion
        deletion_events = [e for e in events if e.event_type == FileEventType.DELETED]
        assert len(deletion_events) == 1
        assert deletion_events[0].file_path.name == "doc2.md"

    print("✓ File creation detection")
    print("✓ File modification detection")
    print("✓ File deletion detection")
    print("✓ Non-markdown file filtering")
    print("✓ File scanning tests passed!")


def test_workspace_integration():
    """Test workspace-level integration."""
    print("\nTesting workspace integration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create project structure
        project1_path = temp_path / "project1"
        project2_path = temp_path / "project2"
        project1_path.mkdir()
        project2_path.mkdir()

        workspace_watcher = WorkspaceFileWatcher(use_watchdog=False)

        # Test error handling
        try:
            workspace_watcher.watch_project("/nonexistent/project")
            assert False, "Should raise FileWatcherError"
        except FileWatcherError:
            pass  # Expected

        # Test watching valid projects
        workspace_watcher.watch_project(str(project1_path))
        assert len(workspace_watcher.get_watched_projects()) == 1

        workspace_watcher.watch_project(str(project2_path))
        assert len(workspace_watcher.get_watched_projects()) == 2

        # Test unwatching
        workspace_watcher.unwatch_project(str(project1_path))
        assert len(workspace_watcher.get_watched_projects()) == 1

        # Test stop all
        workspace_watcher.stop_all_watching()
        assert len(workspace_watcher.get_watched_projects()) == 0

    print("✓ Project watching management")
    print("✓ Multiple project support")
    print("✓ Workspace integration tests passed!")


if __name__ == "__main__":
    print("File Watching Tests - Simplified Version")
    print("=" * 40)

    try:
        test_basic_functionality()
        test_file_scanning()
        test_workspace_integration()

        print("\n" + "=" * 40)
        print("✅ All simplified tests passed!")
        print("T:0009 file system watching implementation verified.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()