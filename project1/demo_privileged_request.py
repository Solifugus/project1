"""
Demo showing PrivilegedRequest usage in Project1 scenarios.
"""

from datetime import datetime
from privileged_request import PrivilegedRequest, Status, RiskLevel, CreatedBy, CommandResult


def main():
    """Demonstrate PrivilegedRequest with realistic Project1 scenarios."""
    print("PrivilegedRequest Demo - Project1 Scenarios")
    print("=" * 45)

    # Scenario 1: AI requests to install Python dependencies
    print("1. AI Requests Python Package Installation")
    print("-" * 40)

    install_request = PrivilegedRequest(
        request_id="PR:0001",
        title="Install Python dependencies for Project1",
        reason="Need to install required packages: click, watchdog, and jsonschema for MCP server implementation",
        risk_level=RiskLevel.LOW,
        created_by=CreatedBy.AI,
        related_task_id="T:0013"  # MCP read operations task
    )

    # Add the commands to execute
    install_request.add_command(["pip3", "install", "click", "watchdog", "jsonschema"])
    install_request.add_verification(["pip3", "list"])
    install_request.add_verification(["python3", "-c", "import click, watchdog, jsonschema; print('All imports successful')"])

    print(f"Request: {install_request}")
    print(f"Risk Level: {install_request.risk_level.value}")
    print(f"Commands: {install_request.commands}")
    print(f"Verification: {install_request.verification}")
    print()

    # Human approves the request
    print("Human reviews and approves the request...")
    install_request.approve()
    print(f"Status: {install_request.status.value}")
    print()

    # Simulate execution
    print("Executing approved command...")
    install_request.start_execution()

    # Simulate successful installation
    execution_results = [
        CommandResult(
            command=["pip3", "install", "click", "watchdog", "jsonschema"],
            stdout="Successfully installed click-8.1.3 watchdog-3.0.0 jsonschema-4.17.3\n",
            stderr="",
            exit_code=0,
            execution_time=5.2
        )
    ]

    install_request.complete_execution(execution_results)
    print(f"Final Status: {install_request.status.value}")
    print(f"Execution Result: {execution_results[0].stdout.strip()}")
    print()

    # Scenario 2: High-risk file system operation
    print("2. High-Risk File System Operation")
    print("-" * 35)

    cleanup_request = PrivilegedRequest(
        request_id="PR:0002",
        title="Clean up temporary build files",
        reason="Remove large temporary files from failed builds to free disk space",
        risk_level=RiskLevel.HIGH,  # File deletion is high risk
        created_by=CreatedBy.AI,
        related_task_id="T:0024"  # Future cleanup task
    )

    # Add dangerous cleanup commands
    cleanup_request.add_command(["find", "/tmp/project1-build", "-name", "*.tmp", "-type", "f", "-delete"])
    cleanup_request.add_command(["rm", "-rf", "/tmp/project1-build/cache"])
    cleanup_request.add_verification(["ls", "-la", "/tmp/project1-build"])

    print(f"Request: {cleanup_request}")
    print(f"Risk Level: {cleanup_request.risk_level.value}")
    print(f"Commands to execute:")
    for i, cmd in enumerate(cleanup_request.commands, 1):
        print(f"  {i}. {' '.join(cmd)}")
    print()

    # Human denies the high-risk request
    print("Human reviews and denies the high-risk request...")
    cleanup_request.deny("Too dangerous - could delete important files")
    print(f"Status: {cleanup_request.status.value}")
    print()

    # Scenario 3: Git operations for development
    print("3. Git Operations for Development")
    print("-" * 30)

    git_request = PrivilegedRequest(
        request_id="PR:0003",
        title="Commit T:0002 implementation",
        reason="Commit PrivilegedRequest implementation after successful testing",
        risk_level=RiskLevel.MEDIUM,
        created_by=CreatedBy.AI,
        related_task_id="T:0002"
    )

    # Add git commands
    git_request.add_command(["git", "add", "privileged_request.py", "test_privileged_request.py"])
    git_request.add_command(["git", "commit", "-m", "Implement T:0002 - PrivilegedRequest data structure"])
    git_request.add_verification(["git", "status"])
    git_request.add_verification(["git", "log", "--oneline", "-n", "1"])

    print(f"Request: {git_request}")
    print(f"Commands:")
    for i, cmd in enumerate(git_request.commands, 1):
        print(f"  {i}. {' '.join(cmd)}")
    print()

    # Approve and execute git operations
    print("Human approves git operations...")
    git_request.approve()
    git_request.start_execution()

    # Simulate git execution
    git_results = [
        CommandResult(
            command=["git", "add", "privileged_request.py", "test_privileged_request.py"],
            stdout="",
            stderr="",
            exit_code=0,
            execution_time=0.1
        ),
        CommandResult(
            command=["git", "commit", "-m", "Implement T:0002 - PrivilegedRequest data structure"],
            stdout="[master abc123] Implement T:0002 - PrivilegedRequest data structure\n 2 files changed, 500 insertions(+)\n",
            stderr="",
            exit_code=0,
            execution_time=0.3
        )
    ]

    git_request.complete_execution(git_results)
    print(f"Git operations completed: {git_request.status.value}")
    print()

    # Demonstrate serialization for audit logging
    print("4. Audit Trail Serialization")
    print("-" * 25)

    print("All requests can be serialized for audit logs:")
    print(f"- {install_request.request_id}: {len(install_request.to_json())} chars JSON")
    print(f"- {cleanup_request.request_id}: {len(cleanup_request.to_json())} chars JSON")
    print(f"- {git_request.request_id}: {len(git_request.to_json())} chars JSON")
    print()

    # Show status summary
    requests = [install_request, cleanup_request, git_request]
    print("Final Status Summary:")
    for req in requests:
        status_icon = "✓" if req.is_completed() else "✗" if req.status == Status.DENIED else "⏳"
        print(f"  {status_icon} {req.request_id}: {req.title} ({req.status.value})")

    print()
    print("✓ PrivilegedRequest handles real Project1 security scenarios!")
    print("✓ Full approval workflow with audit trail")
    print("✓ Risk-based categorization")
    print("✓ Command validation and execution tracking")
    print("✓ Complete serialization for persistence")


if __name__ == "__main__":
    main()