"""
ID extraction from markdown headings for Project1 document parsing.

This module implements ID extraction functionality as specified in T:0004,
following R:IDConvention for parsing structured document elements.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set, Dict
from enum import Enum


class IDPrefix(Enum):
    """Valid ID prefixes for different element types."""
    REQUIREMENT = "R:"
    COMPONENT = "C:"
    DATA = "D:"
    INTERFACE = "I:"
    METHOD = "M:"
    UI = "UI:"
    TASK = "T:"
    TEST = "TP:"


@dataclass
class ExtractedID:
    """
    Represents an ID extracted from a markdown heading.
    """
    # ID components
    full_id: str                    # Complete ID (e.g., "R:Purpose")
    prefix: IDPrefix               # ID prefix enum
    suffix: str                    # Part after prefix (e.g., "Purpose")

    # Heading context
    heading_level: int             # 1-6 for h1-h6
    heading_text: str              # Full heading text without markdown markers
    line_number: int               # Line number in source file (0-based)

    # Source tracking
    raw_line: str                  # Original markdown line

    def __post_init__(self):
        """Validate extracted ID components."""
        if not self.full_id:
            raise ValueError("Full ID cannot be empty")

        if not self.suffix:
            raise ValueError("ID suffix cannot be empty")

        if self.heading_level < 1 or self.heading_level > 6:
            raise ValueError(f"Invalid heading level: {self.heading_level}")


class IDValidator:
    """Validates ID format and uniqueness constraints."""

    def __init__(self):
        """Initialize validator with empty ID tracking."""
        self.seen_ids: Set[str] = set()

    def validate_id_format(self, id_string: str) -> bool:
        """
        Validate ID follows the expected format.

        Args:
            id_string: The ID string to validate (e.g., "R:Purpose")

        Returns:
            True if format is valid, False otherwise.
        """
        if not id_string:
            return False

        # Check if ID starts with valid prefix (case insensitive)
        valid_prefixes = [prefix.value for prefix in IDPrefix]

        for prefix in valid_prefixes:
            if id_string.lower().startswith(prefix.lower()):
                actual_prefix = id_string[:len(prefix)]  # Preserve original case
                suffix = id_string[len(prefix):]
                # Suffix must be non-empty and contain valid characters
                if suffix and self._is_valid_suffix(suffix, actual_prefix):
                    return True

        return False

    def _is_valid_suffix(self, suffix: str, prefix: str = "") -> bool:
        """Check if ID suffix contains valid characters."""
        # Allow alphanumeric, underscores, and hyphens
        # For task (T:) and test (TP:) IDs, allow numeric suffixes
        # For other IDs, must start with letter
        if prefix in ["T:", "TP:"]:
            # Tasks and tests can start with numbers (e.g., T:0001, TP:0001)
            if not suffix[0].isalnum():
                return False
        else:
            # Other IDs must start with letter
            if not suffix[0].isalpha():
                return False

        return all(c.isalnum() or c in ['_', '-'] for c in suffix)

    def check_uniqueness(self, id_string: str) -> bool:
        """
        Check if ID is unique (not previously seen).

        Args:
            id_string: The ID to check for uniqueness.

        Returns:
            True if unique, False if duplicate.
        """
        return id_string not in self.seen_ids

    def register_id(self, id_string: str) -> None:
        """Register an ID as seen."""
        self.seen_ids.add(id_string)

    def get_duplicate_ids(self) -> List[str]:
        """Get list of any duplicate IDs encountered."""
        # This would track duplicates during parsing - simple implementation for now
        return []


class MarkdownHeadingParser:
    """
    Parses markdown headings to extract IDs and metadata.
    """

    # Regex pattern to match markdown headings with optional IDs
    HEADING_PATTERN = re.compile(
        r'^(#{1,6})\s+(.+?)$',  # Capture heading level and text
        re.MULTILINE
    )

    # Pattern to extract ID from heading text
    ID_PATTERN = re.compile(
        r'^(R:|C:|D:|I:|M:|UI:|T:|TP:)([A-Za-z0-9][A-Za-z0-9_-]*)\b',  # ID at start, alphanumeric start
        re.IGNORECASE
    )

    def __init__(self, validate_uniqueness: bool = True):
        """
        Initialize parser.

        Args:
            validate_uniqueness: Whether to enforce ID uniqueness during parsing.
        """
        self.validator = IDValidator()
        self.validate_uniqueness = validate_uniqueness

    def extract_ids_from_text(self, markdown_text: str) -> List[ExtractedID]:
        """
        Extract all IDs from markdown text.

        Args:
            markdown_text: The markdown content to parse.

        Returns:
            List of extracted IDs with their metadata.

        Raises:
            ValueError: If duplicate IDs found and uniqueness validation enabled.
        """
        extracted_ids = []
        lines = markdown_text.split('\n')

        for line_num, line in enumerate(lines):
            # Check if line is a heading
            heading_match = self.HEADING_PATTERN.match(line)
            if not heading_match:
                continue

            heading_markers, heading_text = heading_match.groups()
            heading_level = len(heading_markers)  # Count # characters

            # Try to extract ID from heading text
            extracted_id = self._extract_id_from_heading(
                heading_text.strip(),
                heading_level,
                line_num,
                line
            )

            if extracted_id:
                # Validate uniqueness if enabled
                if self.validate_uniqueness:
                    if not self.validator.check_uniqueness(extracted_id.full_id):
                        raise ValueError(f"Duplicate ID found: {extracted_id.full_id} at line {line_num + 1}")

                    self.validator.register_id(extracted_id.full_id)

                extracted_ids.append(extracted_id)

        return extracted_ids

    def _extract_id_from_heading(self, heading_text: str, heading_level: int,
                                line_number: int, raw_line: str) -> Optional[ExtractedID]:
        """
        Extract ID from a single heading text.

        Args:
            heading_text: Clean heading text without markdown markers.
            heading_level: Heading level (1-6).
            line_number: Line number in source file.
            raw_line: Original markdown line.

        Returns:
            ExtractedID if ID found, None otherwise.
        """
        # Look for ID at the beginning of heading text
        id_match = self.ID_PATTERN.match(heading_text)
        if not id_match:
            return None

        prefix_str, suffix = id_match.groups()
        full_id = prefix_str + suffix

        # Additional validation: ensure the matched ID is a complete token
        # Check if there are invalid characters immediately after the matched ID
        match_end = id_match.end()
        if match_end < len(heading_text):
            next_char = heading_text[match_end]
            # If next char is alphanumeric or special char (not space/dash), it's not a complete ID
            if next_char.isalnum() or next_char in '@#$%^&*()+=[]{}|\\;:\'",.<>?/`~':
                return None

        # Validate ID format
        if not self.validator.validate_id_format(full_id):
            return None

        # Map string prefix to enum (case insensitive)
        try:
            # Find matching enum value (case insensitive)
            prefix_enum = None
            for prefix in IDPrefix:
                if prefix.value.lower() == prefix_str.lower():
                    prefix_enum = prefix
                    break

            if prefix_enum is None:
                return None
        except ValueError:
            return None

        return ExtractedID(
            full_id=full_id,
            prefix=prefix_enum,
            suffix=suffix,
            heading_level=heading_level,
            heading_text=heading_text,
            line_number=line_number,
            raw_line=raw_line
        )

    def extract_ids_from_file(self, file_path: str) -> List[ExtractedID]:
        """
        Extract IDs from a markdown file.

        Args:
            file_path: Path to the markdown file.

        Returns:
            List of extracted IDs.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If duplicate IDs found and validation enabled.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.extract_ids_from_text(content)

        except FileNotFoundError:
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

    def validate_project_uniqueness(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Validate ID uniqueness across multiple files in a project.

        Args:
            file_paths: List of markdown file paths to check.

        Returns:
            Dict mapping duplicate IDs to list of files where they appear.

        Raises:
            FileNotFoundError: If any file doesn't exist.
        """
        global_validator = IDValidator()
        duplicates = {}
        id_locations = {}  # Track where each ID was first seen

        for file_path in file_paths:
            # Parse each file independently first
            parser = MarkdownHeadingParser(validate_uniqueness=False)
            extracted_ids = parser.extract_ids_from_file(file_path)

            for extracted_id in extracted_ids:
                full_id = extracted_id.full_id

                if full_id in id_locations:
                    # Duplicate found
                    if full_id not in duplicates:
                        duplicates[full_id] = [id_locations[full_id], file_path]
                    else:
                        duplicates[full_id].append(file_path)
                else:
                    id_locations[full_id] = file_path

        return duplicates

    def get_id_statistics(self, extracted_ids: List[ExtractedID]) -> Dict[str, int]:
        """
        Get statistics about extracted IDs.

        Args:
            extracted_ids: List of extracted IDs to analyze.

        Returns:
            Dict with statistics about ID prefixes and heading levels.
        """
        stats = {
            'total_ids': len(extracted_ids),
            'by_prefix': {},
            'by_heading_level': {}
        }

        for extracted_id in extracted_ids:
            # Count by prefix
            prefix_name = extracted_id.prefix.name
            stats['by_prefix'][prefix_name] = stats['by_prefix'].get(prefix_name, 0) + 1

            # Count by heading level
            level = extracted_id.heading_level
            stats['by_heading_level'][f'h{level}'] = stats['by_heading_level'].get(f'h{level}', 0) + 1

        return stats


def extract_ids_from_markdown(markdown_text: str, validate_uniqueness: bool = True) -> List[ExtractedID]:
    """
    Convenience function to extract IDs from markdown text.

    Args:
        markdown_text: Markdown content to parse.
        validate_uniqueness: Whether to enforce ID uniqueness.

    Returns:
        List of extracted IDs.
    """
    parser = MarkdownHeadingParser(validate_uniqueness=validate_uniqueness)
    return parser.extract_ids_from_text(markdown_text)


def extract_ids_from_file(file_path: str, validate_uniqueness: bool = True) -> List[ExtractedID]:
    """
    Convenience function to extract IDs from a markdown file.

    Args:
        file_path: Path to markdown file.
        validate_uniqueness: Whether to enforce ID uniqueness.

    Returns:
        List of extracted IDs.
    """
    parser = MarkdownHeadingParser(validate_uniqueness=validate_uniqueness)
    return parser.extract_ids_from_file(file_path)