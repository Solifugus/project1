"""
Privileged request data structures for Project1 security system.

This module defines the PrivilegedRequest class and related enums as specified
in D:PrivilegedRequest for handling approved command execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json


class Status(Enum):
    """Request lifecycle status for tracking approval and execution."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(Enum):
    """Risk assessment for privileged operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CreatedBy(Enum):
    """Origin of the privileged request."""
    AI = "AI"
    HUMAN = "Human"


@dataclass
class CommandResult:
    """Result of executing a single command."""
    command: List[str]  # argv array that was executed
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None  # seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'command': self.command.copy(),
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exit_code': self.exit_code,
            'execution_time': self.execution_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CommandResult':
        """Create from dictionary (deserialization)."""
        return cls(
            command=data['command'],
            stdout=data.get('stdout', ''),
            stderr=data.get('stderr', ''),
            exit_code=data.get('exit_code'),
            execution_time=data.get('execution_time')
        )


@dataclass
class PrivilegedRequest:
    """
    Request for privileged command execution requiring human approval.

    Represents a security-gated request to execute commands with elevated
    privileges, including full audit trail and approval workflow.
    """

    # Core identification and description
    request_id: str  # Format: PR:####
    title: str
    reason: str

    # Command specification (argv arrays only, no shell)
    commands: List[List[str]] = field(default_factory=list)
    verification: List[List[str]] = field(default_factory=list)

    # Risk and approval metadata
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_by: CreatedBy = CreatedBy.AI
    related_task_id: Optional[str] = None

    # Workflow state
    status: Status = Status.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Execution results
    result: List[CommandResult] = field(default_factory=list)

    def __post_init__(self):
        """Initialize timestamps and validate request."""
        if not self.request_id:
            raise ValueError("PrivilegedRequest request_id cannot be empty")

        if not self.request_id.startswith("PR:"):
            raise ValueError("PrivilegedRequest request_id must start with 'PR:'")

        if not self.title:
            raise ValueError("PrivilegedRequest title cannot be empty")

        if not self.reason:
            raise ValueError("PrivilegedRequest reason cannot be empty")

        # Set timestamps if not provided
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def approve(self, approver: str = "human") -> None:
        """Approve the request for execution."""
        if self.status != Status.PENDING:
            raise ValueError(f"Cannot approve request in status {self.status.value}")

        self.status = Status.APPROVED
        self.updated_at = datetime.utcnow()
        # Could extend to track approver identity

    def deny(self, reason: str = "") -> None:
        """Deny the request."""
        if self.status not in [Status.PENDING, Status.APPROVED]:
            raise ValueError(f"Cannot deny request in status {self.status.value}")

        self.status = Status.DENIED
        self.updated_at = datetime.utcnow()
        # Could extend to track denial reason

    def start_execution(self) -> None:
        """Mark request as running."""
        if self.status != Status.APPROVED:
            raise ValueError(f"Cannot execute request in status {self.status.value}")

        self.status = Status.RUNNING
        self.updated_at = datetime.utcnow()

    def complete_execution(self, results: List[CommandResult]) -> None:
        """Mark request as completed with execution results."""
        if self.status != Status.RUNNING:
            raise ValueError(f"Cannot complete request in status {self.status.value}")

        self.result = results
        self.status = Status.COMPLETED
        self.updated_at = datetime.utcnow()

    def fail_execution(self, results: List[CommandResult]) -> None:
        """Mark request as failed with partial execution results."""
        if self.status != Status.RUNNING:
            raise ValueError(f"Cannot fail request in status {self.status.value}")

        self.result = results
        self.status = Status.FAILED
        self.updated_at = datetime.utcnow()

    def add_command(self, command: List[str]) -> None:
        """Add a command to execute (argv array)."""
        if not isinstance(command, list):
            raise ValueError("Command must be argv array (list of strings)")
        if not command:
            raise ValueError("Command cannot be empty")
        if not all(isinstance(arg, str) for arg in command):
            raise ValueError("All command arguments must be strings")

        self.commands.append(command.copy())

    def add_verification(self, verification: List[str]) -> None:
        """Add a verification command (argv array)."""
        if not isinstance(verification, list):
            raise ValueError("Verification must be argv array (list of strings)")
        if not verification:
            raise ValueError("Verification cannot be empty")
        if not all(isinstance(arg, str) for arg in verification):
            raise ValueError("All verification arguments must be strings")

        self.verification.append(verification.copy())

    def is_pending(self) -> bool:
        """Check if request is pending approval."""
        return self.status == Status.PENDING

    def is_approved(self) -> bool:
        """Check if request is approved for execution."""
        return self.status == Status.APPROVED

    def is_completed(self) -> bool:
        """Check if request execution is finished (success or failure)."""
        return self.status in [Status.COMPLETED, Status.FAILED]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            'request_id': self.request_id,
            'title': self.title,
            'reason': self.reason,
            'commands': [cmd.copy() for cmd in self.commands],
            'verification': [ver.copy() for ver in self.verification],
            'risk_level': self.risk_level.value,
            'created_by': self.created_by.value,
            'related_task_id': self.related_task_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'result': [res.to_dict() for res in self.result]
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'PrivilegedRequest':
        """Create PrivilegedRequest from dictionary (deserialization)."""
        # Parse timestamps
        created_at = None
        updated_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])

        # Parse enums
        risk_level = RiskLevel(data['risk_level'])
        created_by = CreatedBy(data['created_by'])
        status = Status(data['status'])

        # Parse results
        results = [CommandResult.from_dict(res) for res in data.get('result', [])]

        return cls(
            request_id=data['request_id'],
            title=data['title'],
            reason=data['reason'],
            commands=data.get('commands', []),
            verification=data.get('verification', []),
            risk_level=risk_level,
            created_by=created_by,
            related_task_id=data.get('related_task_id'),
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            result=results
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'PrivilegedRequest':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """String representation showing key request info."""
        return f"PrivilegedRequest[{self.request_id}: {self.title} ({self.status.value})]"