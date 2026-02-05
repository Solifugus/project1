"""
Demo showing workspace discovery with real Project1 workspace.
"""

from workspace_discovery import WorkspaceDiscovery, discover_workspace, find_projects
from pathlib import Path
import os


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB']
    size = size_bytes
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def format_timestamp(timestamp: float) -> str:
    """Format timestamp in readable format."""
    if timestamp is None:
        return "N/A"

    import datetime
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Demonstrate workspace discovery with real Project1 workspace."""
    print("Workspace Discovery Demo - Real Project1 Workspace")
    print("=" * 51)

    # Use the current workspace (~/software-projects)
    workspace_path = os.path.expanduser("~/software-projects")
    print(f"Scanning workspace: {workspace_path}")
    print()

    try:
        discovery = WorkspaceDiscovery(workspace_path)
        workspace_info = discovery.discover_workspace()

        # Workspace Overview
        print("WORKSPACE OVERVIEW")
        print("-" * 18)
        print(f"  Workspace Path: {workspace_info.path}")
        print(f"  Total Directories: {workspace_info.total_directories}")
        print(f"  Projects Found: {len(workspace_info.projects)}")
        print()

        # Conventions File Analysis
        print("CONVENTIONS FILE")
        print("-" * 16)
        conventions = workspace_info.conventions_file
        print(f"  File: {conventions.name}")
        print(f"  Exists: {'✓' if conventions.exists else '✗'}")

        if conventions.exists:
            print(f"  Size: {format_file_size(conventions.size_bytes)}")
            print(f"  Last Modified: {format_timestamp(conventions.last_modified)}")
        else:
            print("  Issue: Missing workspace conventions.md file")
        print()

        # Project Analysis
        print("PROJECT ANALYSIS")
        print("-" * 16)

        if not workspace_info.projects:
            print("  No projects found in workspace.")
        else:
            print(f"  Found {len(workspace_info.projects)} projects:")
            print()

            # Sort projects by status and name
            sorted_projects = sorted(workspace_info.projects, key=lambda p: (p.status.value, p.name))

            for i, project in enumerate(sorted_projects, 1):
                status_icon = {
                    'complete': '✅',
                    'incomplete': '⚠️',
                    'invalid': '❌'
                }.get(project.status.value, '❓')

                print(f"    {i}. {status_icon} {project.name} ({project.status.value})")
                print(f"       Path: {project.path}")

                # Required files status
                files_status = []
                for file_name, file_obj in [
                    ("software-design.md", project.software_design),
                    ("development-plan.md", project.development_plan),
                    ("test-plan.md", project.test_plan),
                ]:
                    if file_obj.exists:
                        size_str = format_file_size(file_obj.size_bytes)
                        files_status.append(f"{file_name} ({size_str})")
                    else:
                        files_status.append(f"{file_name} (missing)")

                print(f"       Required Files:")
                for status in files_status:
                    icon = "✓" if "missing" not in status else "✗"
                    print(f"         {icon} {status}")

                # Additional files
                if project.additional_files:
                    print(f"       Additional Files: {', '.join(project.additional_files[:5])}")
                    if len(project.additional_files) > 5:
                        print(f"                         ... and {len(project.additional_files) - 5} more")

                # Issues
                if project.issues:
                    print(f"       Issues:")
                    for issue in project.issues[:3]:
                        print(f"         • {issue}")
                    if len(project.issues) > 3:
                        print(f"         ... and {len(project.issues) - 3} more issues")

                print()

        # Statistics Summary
        print("STATISTICS SUMMARY")
        print("-" * 18)
        stats = discovery.get_workspace_statistics()

        print(f"  Project Status Distribution:")
        status_distribution = stats['project_status_distribution']
        total_projects = stats['total_projects']

        for status, count in status_distribution.items():
            percentage = (count / total_projects * 100) if total_projects > 0 else 0
            status_icon = {'complete': '✅', 'incomplete': '⚠️', 'invalid': '❌'}[status]
            print(f"    {status_icon} {status.title():<11}: {count:>2} projects ({percentage:>5.1f}%)")

        print(f"  File Statistics:")
        print(f"    Total Size: {format_file_size(stats['total_size_bytes'])}")
        print(f"    Average Project Size: {format_file_size(stats['average_project_size_bytes'])}")
        print(f"    Conventions File Size: {format_file_size(stats['conventions_file_size'])}")

        print(f"  Issue Summary:")
        print(f"    Workspace Issues: {stats['workspace_issues']}")
        print(f"    Project Issues: {stats['total_project_issues']}")

        # Validation Summary
        print()
        print("VALIDATION SUMMARY")
        print("-" * 18)

        all_issues = discovery.validate_workspace_structure()

        if not all_issues:
            print("  ✅ No issues found! Workspace is properly structured.")
        else:
            print(f"  Found {len(all_issues)} validation issues:")
            print()

            # Group issues by type
            workspace_issues = [issue for issue in all_issues if not any(p.name in issue for p in workspace_info.projects)]
            project_issues = [issue for issue in all_issues if any(p.name in issue for p in workspace_info.projects)]

            if workspace_issues:
                print(f"    Workspace Issues ({len(workspace_issues)}):")
                for issue in workspace_issues[:5]:
                    print(f"      • {issue}")
                if len(workspace_issues) > 5:
                    print(f"      ... and {len(workspace_issues) - 5} more workspace issues")

            if project_issues:
                print(f"    Project Issues ({len(project_issues)}):")
                for issue in project_issues[:5]:
                    print(f"      • {issue}")
                if len(project_issues) > 5:
                    print(f"      ... and {len(project_issues) - 5} more project issues")

        # Demonstration of specific functionality
        print()
        print("FUNCTIONALITY DEMONSTRATION")
        print("-" * 27)

        # Find specific project
        project1 = discovery.find_project_by_name("project1")
        if project1:
            print(f"✓ Successfully found project 'project1':")
            print(f"  Status: {project1.status.value}")
            print(f"  Required files complete: {all(f.exists for f in [project1.software_design, project1.development_plan, project1.test_plan])}")

            total_size = (
                project1.software_design.size_bytes +
                project1.development_plan.size_bytes +
                project1.test_plan.size_bytes
            )
            print(f"  Total size: {format_file_size(total_size)}")
        else:
            print("✗ Project 'project1' not found")

        # Test JSON export
        print()
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                export_path = f.name

            discovery.export_workspace_info(export_path)
            export_size = Path(export_path).stat().st_size
            print(f"✓ Exported workspace info to JSON ({format_file_size(export_size)})")

            # Clean up
            os.unlink(export_path)
        except Exception as e:
            print(f"✗ JSON export failed: {e}")

        # Convenience functions demo
        print()
        print("CONVENIENCE FUNCTIONS")
        print("-" * 21)

        # Test discover_workspace function
        ws_info = discover_workspace(workspace_path)
        print(f"✓ discover_workspace() found {len(ws_info.projects)} projects")

        # Test find_projects function
        projects = find_projects(workspace_path)
        print(f"✓ find_projects() found {len(projects)} projects")

        complete_projects = [p for p in projects if p.status.value == 'complete']
        print(f"✓ {len(complete_projects)} projects are complete and ready for development")

    except Exception as e:
        print(f"Error during workspace discovery: {e}")
        return

    print()
    print("✓ Workspace directory scanning")
    print("✓ Project structure validation")
    print("✓ Required file detection and analysis")
    print("✓ Project status classification (complete/incomplete/invalid)")
    print("✓ File size and modification tracking")
    print("✓ Additional file discovery")
    print("✓ Issue identification and reporting")
    print("✓ Comprehensive statistics generation")
    print("✓ JSON export capability")
    print("✓ Project lookup by name")
    print("✓ Workspace validation and health checking")


if __name__ == "__main__":
    main()