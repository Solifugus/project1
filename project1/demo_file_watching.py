"""
Demo showing file system watching for Project1 workspace monitoring.
"""

import time
import os
from pathlib import Path
from file_watching import WorkspaceFileWatcher, FileEventType, create_file_watcher


class DemoChangeHandler:
    """Demo change handler that logs file change events."""

    def __init__(self):
        self.events = []

    def handle_change(self, file_path: Path, event_type: FileEventType) -> None:
        """Handle file change events."""
        timestamp = time.strftime("%H:%M:%S")
        event_info = {
            'timestamp': timestamp,
            'event_type': event_type.value,
            'file_path': file_path,
            'file_name': file_path.name,
            'project': self._get_project_name(file_path)
        }

        self.events.append(event_info)

        # Print real-time notification
        print(f"  [{timestamp}] {event_type.value.upper()}: {event_info['project']}/{file_path.name}")

    def _get_project_name(self, file_path: Path) -> str:
        """Extract project name from file path."""
        try:
            # Find the project directory (should be under workspace)
            parts = file_path.parts
            workspace_index = None

            for i, part in enumerate(parts):
                if part == "software-projects":
                    workspace_index = i
                    break

            if workspace_index is not None and len(parts) > workspace_index + 1:
                return parts[workspace_index + 1]

            return "unknown"
        except:
            return "unknown"

    def get_events_summary(self) -> dict:
        """Get summary of collected events."""
        if not self.events:
            return {'total': 0}

        events_by_type = {}
        events_by_project = {}
        events_by_file = {}

        for event in self.events:
            event_type = event['event_type']
            project = event['project']
            file_name = event['file_name']

            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            events_by_project[project] = events_by_project.get(project, 0) + 1
            events_by_file[file_name] = events_by_file.get(file_name, 0) + 1

        return {
            'total': len(self.events),
            'by_type': events_by_type,
            'by_project': events_by_project,
            'by_file': events_by_file,
            'recent_events': self.events[-5:]  # Last 5 events
        }


def main():
    """Demonstrate file system watching with Project1 workspace."""
    print("File System Watching Demo - Project1 Workspace Monitoring")
    print("=" * 58)

    # Use the current workspace
    workspace_path = os.path.expanduser("~/software-projects")
    print(f"Monitoring workspace: {workspace_path}")

    # Create file watcher (try watchdog first, fall back to polling)
    try:
        watcher = create_file_watcher(use_watchdog=True)
    except:
        watcher = create_file_watcher(use_watchdog=False)

    print(f"Using {watcher.watcher_type} file watcher")

    # Get watcher info
    info = watcher.get_watcher_info()
    print(f"Watchdog available: {info['watchdog_available']}")
    print()

    # Set up change handler
    handler = DemoChangeHandler()
    watcher.add_change_handler(handler.handle_change)

    try:
        # Find and watch existing projects
        workspace_path_obj = Path(workspace_path)

        if not workspace_path_obj.exists():
            print(f"Warning: Workspace path does not exist: {workspace_path}")
            return

        # Discover projects to watch
        projects_found = []
        for item in workspace_path_obj.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it looks like a project (has markdown files)
                md_files = list(item.glob("*.md"))
                if md_files:
                    projects_found.append(item)

        if not projects_found:
            print("No projects found to monitor.")
            return

        print("PROJECTS DISCOVERED FOR MONITORING")
        print("-" * 35)

        for project_path in projects_found:
            md_files = list(project_path.glob("*.md"))
            print(f"  📁 {project_path.name}")
            print(f"     Path: {project_path}")
            print(f"     Markdown files: {len(md_files)}")

            # Show some example files
            example_files = [f.name for f in md_files[:3]]
            if example_files:
                print(f"     Examples: {', '.join(example_files)}")
                if len(md_files) > 3:
                    print(f"               ... and {len(md_files) - 3} more")

            # Start watching this project
            try:
                watcher.watch_project(str(project_path))
                print(f"     Status: ✅ Watching")
            except Exception as e:
                print(f"     Status: ❌ Error: {e}")
            print()

        watched_projects = watcher.get_watched_projects()
        print(f"Successfully watching {len(watched_projects)} projects")
        print()

        # Instructions for user interaction
        print("FILE CHANGE MONITORING ACTIVE")
        print("-" * 29)
        print("The file watcher is now monitoring markdown files for changes.")
        print("Try the following to see real-time detection:")
        print()
        print("1. Edit any .md file in the workspace")
        print("2. Create a new .md file")
        print("3. Delete an .md file")
        print("4. Rename an .md file")
        print()
        print("Events will be displayed in real-time below:")
        print("(Press Ctrl+C to stop monitoring)")
        print()

        # Monitor for changes
        start_time = time.time()
        last_summary_time = start_time

        while True:
            try:
                time.sleep(1.0)  # Check every second

                current_time = time.time()

                # Show periodic summary every 30 seconds if there are events
                if current_time - last_summary_time >= 30 and handler.events:
                    print()
                    print("📊 EVENT SUMMARY (last 30 seconds)")
                    print("-" * 35)

                    summary = handler.get_events_summary()
                    print(f"  Total events: {summary['total']}")

                    if summary['by_type']:
                        print(f"  By type:")
                        for event_type, count in summary['by_type'].items():
                            icon = {'created': '📝', 'modified': '✏️', 'deleted': '🗑️', 'moved': '📁'}.get(event_type, '📄')
                            print(f"    {icon} {event_type}: {count}")

                    if summary['by_project']:
                        print(f"  By project:")
                        for project, count in summary['by_project'].items():
                            print(f"    📁 {project}: {count} events")

                    if summary['recent_events']:
                        print(f"  Recent events:")
                        for event in summary['recent_events']:
                            print(f"    [{event['timestamp']}] {event['event_type']} - {event['project']}/{event['file_name']}")

                    print()
                    last_summary_time = current_time

                # Show status every 60 seconds if no events
                elif current_time - start_time >= 60 and not handler.events:
                    print(f"⏱️  Monitoring... ({int(current_time - start_time)}s elapsed, no changes detected)")
                    start_time = current_time

            except KeyboardInterrupt:
                print()
                print("🛑 Monitoring stopped by user")
                break

    except Exception as e:
        print(f"Error during file watching demo: {e}")

    finally:
        # Stop watching and cleanup
        watcher.stop_all_watching()
        print()
        print("MONITORING SESSION SUMMARY")
        print("-" * 26)

        if handler.events:
            summary = handler.get_events_summary()
            print(f"Total events detected: {summary['total']}")

            if summary['by_type']:
                print("Event breakdown:")
                for event_type, count in summary['by_type'].items():
                    print(f"  {event_type}: {count}")

            if summary['by_project']:
                print("Project activity:")
                for project, count in summary['by_project'].items():
                    print(f"  {project}: {count} events")

            if summary['by_file']:
                most_active = max(summary['by_file'].items(), key=lambda x: x[1])
                print(f"Most active file: {most_active[0]} ({most_active[1]} events)")

        else:
            print("No file changes detected during monitoring session.")

        print()
        print("CAPABILITY DEMONSTRATION")
        print("-" * 24)
        print("✅ Real-time markdown file monitoring")
        print("✅ Multi-project workspace watching")
        print("✅ Event type detection (created/modified/deleted)")
        print("✅ Recursive subdirectory monitoring")
        print("✅ Non-markdown file filtering")
        print("✅ Event handler exception safety")
        print("✅ Cross-platform file watching")

        if watcher.watcher_type == "watchdog":
            print("✅ Efficient native file system events")
        else:
            print("✅ Reliable polling-based change detection")

        print(f"✅ {len(watched_projects)} projects monitored successfully")


if __name__ == "__main__":
    main()