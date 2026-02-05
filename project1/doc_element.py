"""
Core data structures for Project1 document model.

This module defines the DocElement class and related enums as specified in D:DocElement.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import json


class Kind(Enum):
    """Element kind classification for organizing design artifacts."""
    REQUIREMENT = "Requirement"
    COMPONENT = "Component"
    DATA = "Data"
    INTERFACE = "Interface"
    METHOD = "Method"
    UI = "UI"
    TASK = "Task"
    TEST = "Test"
    OTHER = "Other"


class File(Enum):
    """Source file enumeration for workspace artifacts."""
    CONVENTIONS = "conventions"
    SOFTWARE_DESIGN = "software-design"
    DEVELOPMENT_PLAN = "development-plan"
    TEST_PLAN = "test-plan"


class Status(Enum):
    """Task status tracking (for Task kind only)."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class DocElement:
    """
    Core document element representing an addressable artifact component.

    Each DocElement corresponds to a heading-delimited section in a markdown file
    with a stable ID for referencing and cross-linking.
    """

    # Core identification
    id: str
    kind: Kind
    title: str

    # File location and structure
    file: File
    heading_level: int
    anchor: str

    # Content and relationships
    body_markdown: str
    refs: List[str] = field(default_factory=list)  # IDs referenced in body
    backlinks: List[str] = field(default_factory=list)  # Computed reverse refs

    # Task-specific status (only applicable for Task kind)
    status: Optional[Status] = None

    def __post_init__(self):
        """Validate element after initialization."""
        if not self.id:
            raise ValueError("DocElement id cannot be empty")

        if self.kind == Kind.TASK and self.status is None:
            # Default status for new tasks
            self.status = Status.PENDING
        elif self.kind != Kind.TASK and self.status is not None:
            # Status only valid for Task kind
            raise ValueError(f"Status field only valid for Task kind, got {self.kind}")

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            'id': self.id,
            'kind': self.kind.value,
            'title': self.title,
            'file': self.file.value,
            'heading_level': self.heading_level,
            'anchor': self.anchor,
            'body_markdown': self.body_markdown,
            'refs': self.refs.copy(),
            'backlinks': self.backlinks.copy(),
        }

        if self.status is not None:
            result['status'] = self.status.value

        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'DocElement':
        """Create DocElement from dictionary (deserialization)."""
        # Convert enum string values back to enum instances
        kind = Kind(data['kind'])
        file = File(data['file'])
        status = Status(data['status']) if data.get('status') else None

        return cls(
            id=data['id'],
            kind=kind,
            title=data['title'],
            file=file,
            heading_level=data['heading_level'],
            anchor=data['anchor'],
            body_markdown=data['body_markdown'],
            refs=data.get('refs', []),
            backlinks=data.get('backlinks', []),
            status=status
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'DocElement':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def add_reference(self, ref_id: str) -> None:
        """Add a reference to another element (if not already present)."""
        if ref_id not in self.refs:
            self.refs.append(ref_id)

    def add_backlink(self, ref_id: str) -> None:
        """Add a backlink from another element (if not already present)."""
        if ref_id not in self.backlinks:
            self.backlinks.append(ref_id)

    def is_task(self) -> bool:
        """Check if this element is a task."""
        return self.kind == Kind.TASK

    def __str__(self) -> str:
        """String representation showing key element info."""
        status_str = f" ({self.status.value})" if self.status else ""
        return f"DocElement[{self.id}: {self.title}{status_str}]"