"""
Tests for PrivilegedRequest implementation.

This validates T:0002 acceptance criteria.
"""

from datetime import datetime, timedelta
from privileged_request import PrivilegedRequest, Status, RiskLevel, CreatedBy, CommandResult


def test_create_valid_privileged_request():
    """Test creating PrivilegedRequest with required fields."""
    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Install required dependencies",
        reason="Need to install Python packages for project development"
    )

    assert request.request_id == "PR:0001"
    assert request.title == "Install required dependencies"
    assert request.reason == "Need to install Python packages for project development"
    assert request.status == Status.PENDING
    assert request.risk_level == RiskLevel.MEDIUM  # Default
    assert request.created_by == CreatedBy.AI  # Default
    assert request.created_at is not None
    assert request.updated_at is not None
    assert isinstance(request.commands, list)
    assert isinstance(request.verification, list)
    assert isinstance(request.result, list)


def test_privileged_request_validation():
    """Test validation rules for PrivilegedRequest."""
    # Empty request_id should fail
    try:
        PrivilegedRequest(
            request_id="",
            title="Test",
            reason="Test reason"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "request_id cannot be empty" in str(e)

    # Invalid request_id format should fail
    try:
        PrivilegedRequest(
            request_id="INVALID:0001",
            title="Test",
            reason="Test reason"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must start with 'PR:'" in str(e)

    # Empty title should fail
    try:
        PrivilegedRequest(
            request_id="PR:0001",
            title="",
            reason="Test reason"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "title cannot be empty" in str(e)

    # Empty reason should fail
    try:
        PrivilegedRequest(
            request_id="PR:0001",
            title="Test",
            reason=""
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "reason cannot be empty" in str(e)


def test_enum_values():
    """Test enum fields accept only valid values."""
    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Test Request",
        reason="Testing enum values",
        risk_level=RiskLevel.HIGH,
        created_by=CreatedBy.HUMAN,
        status=Status.APPROVED
    )

    assert request.risk_level == RiskLevel.HIGH
    assert request.created_by == CreatedBy.HUMAN
    assert request.status == Status.APPROVED


def test_status_transitions():
    """Test valid status transitions through approval workflow."""
    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Test Request",
        reason="Testing status transitions"
    )

    # Start in pending state
    assert request.status == Status.PENDING
    assert request.is_pending() is True
    assert request.is_approved() is False

    # Approve request
    old_updated = request.updated_at
    request.approve()
    assert request.status == Status.APPROVED
    assert request.is_approved() is True
    assert request.updated_at > old_updated

    # Start execution
    old_updated = request.updated_at
    request.start_execution()
    assert request.status == Status.RUNNING
    assert request.updated_at > old_updated

    # Complete execution
    results = [
        CommandResult(command=["echo", "hello"], stdout="hello\n", exit_code=0)
    ]
    old_updated = request.updated_at
    request.complete_execution(results)
    assert request.status == Status.COMPLETED
    assert request.is_completed() is True
    assert request.result == results
    assert request.updated_at > old_updated


def test_invalid_status_transitions():
    """Test invalid status transitions are rejected."""
    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Test Request",
        reason="Testing invalid transitions"
    )

    # Cannot execute without approval
    try:
        request.start_execution()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Cannot execute request in status pending" in str(e)

    # Cannot complete without running
    try:
        request.complete_execution([])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Cannot complete request in status pending" in str(e)


def test_command_management():
    """Test adding and validating commands."""
    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Test Request",
        reason="Testing command management"
    )

    # Add valid commands
    request.add_command(["pip", "install", "requests"])
    request.add_command(["git", "status"])

    assert len(request.commands) == 2
    assert request.commands[0] == ["pip", "install", "requests"]
    assert request.commands[1] == ["git", "status"]

    # Add verification commands
    request.add_verification(["pip", "list"])
    request.add_verification(["git", "log", "--oneline", "-n", "1"])

    assert len(request.verification) == 2
    assert request.verification[0] == ["pip", "list"]
    assert request.verification[1] == ["git", "log", "--oneline", "-n", "1"]


def test_invalid_commands():
    """Test command validation rejects invalid formats."""
    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Test Request",
        reason="Testing command validation"
    )

    # Non-list command should fail
    try:
        request.add_command("pip install requests")  # String instead of list
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be argv array" in str(e)

    # Empty command should fail
    try:
        request.add_command([])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot be empty" in str(e)

    # Non-string arguments should fail
    try:
        request.add_command(["pip", "install", 123])  # Number instead of string
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be strings" in str(e)


def test_timestamp_handling():
    """Test timestamp creation and updates."""
    before = datetime.utcnow()

    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Test Request",
        reason="Testing timestamps"
    )

    after = datetime.utcnow()

    # Timestamps should be set automatically
    assert request.created_at is not None
    assert request.updated_at is not None
    assert before <= request.created_at <= after
    assert before <= request.updated_at <= after

    # Explicit timestamps should be preserved
    explicit_time = datetime(2023, 1, 1, 12, 0, 0)
    request_explicit = PrivilegedRequest(
        request_id="PR:0002",
        title="Test Request",
        reason="Testing explicit timestamps",
        created_at=explicit_time,
        updated_at=explicit_time
    )

    assert request_explicit.created_at == explicit_time
    assert request_explicit.updated_at == explicit_time


def test_serialization_roundtrip():
    """Test JSON serialization and deserialization."""
    original = PrivilegedRequest(
        request_id="PR:0001",
        title="Install dependencies",
        reason="Need packages for development",
        risk_level=RiskLevel.LOW,
        created_by=CreatedBy.HUMAN,
        related_task_id="T:0005"
    )

    # Add some commands and results
    original.add_command(["pip", "install", "requests"])
    original.add_verification(["pip", "list"])

    # Simulate execution
    original.approve()
    original.start_execution()
    results = [
        CommandResult(
            command=["pip", "install", "requests"],
            stdout="Successfully installed requests\n",
            stderr="",
            exit_code=0,
            execution_time=2.5
        )
    ]
    original.complete_execution(results)

    # Serialize and deserialize
    json_str = original.to_json()
    restored = PrivilegedRequest.from_json(json_str)

    # Verify all fields preserved
    assert restored.request_id == original.request_id
    assert restored.title == original.title
    assert restored.reason == original.reason
    assert restored.commands == original.commands
    assert restored.verification == original.verification
    assert restored.risk_level == original.risk_level
    assert restored.created_by == original.created_by
    assert restored.related_task_id == original.related_task_id
    assert restored.status == original.status
    assert restored.created_at == original.created_at
    assert restored.updated_at == original.updated_at

    # Verify results preserved
    assert len(restored.result) == 1
    assert restored.result[0].command == results[0].command
    assert restored.result[0].stdout == results[0].stdout
    assert restored.result[0].exit_code == results[0].exit_code


def test_command_result():
    """Test CommandResult data structure."""
    result = CommandResult(
        command=["echo", "hello"],
        stdout="hello\n",
        stderr="",
        exit_code=0,
        execution_time=0.1
    )

    assert result.command == ["echo", "hello"]
    assert result.stdout == "hello\n"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.execution_time == 0.1

    # Test serialization
    result_dict = result.to_dict()
    restored = CommandResult.from_dict(result_dict)

    assert restored.command == result.command
    assert restored.stdout == result.stdout
    assert restored.stderr == result.stderr
    assert restored.exit_code == result.exit_code
    assert restored.execution_time == result.execution_time


def test_denial_workflow():
    """Test request denial workflow."""
    request = PrivilegedRequest(
        request_id="PR:0001",
        title="Dangerous Operation",
        reason="This might be risky"
    )

    # Deny pending request
    old_updated = request.updated_at
    request.deny()

    assert request.status == Status.DENIED
    assert request.updated_at > old_updated

    # Cannot execute denied request
    try:
        request.start_execution()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Cannot execute request in status denied" in str(e)


if __name__ == "__main__":
    # Run all tests manually
    print("Running PrivilegedRequest tests...")

    test_create_valid_privileged_request()
    print("✓ Valid PrivilegedRequest creation")

    test_privileged_request_validation()
    print("✓ Request validation")

    test_enum_values()
    print("✓ Enum field validation")

    test_status_transitions()
    print("✓ Valid status transitions")

    test_invalid_status_transitions()
    print("✓ Invalid status transition rejection")

    test_command_management()
    print("✓ Command management")

    test_invalid_commands()
    print("✓ Command validation")

    test_timestamp_handling()
    print("✓ Timestamp handling")

    test_serialization_roundtrip()
    print("✓ JSON serialization roundtrip")

    test_command_result()
    print("✓ CommandResult structure")

    test_denial_workflow()
    print("✓ Denial workflow")

    print("\nAll tests passed! T:0002 implementation is complete.")