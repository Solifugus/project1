"""
Markdown body extraction for Project1 document parsing.

This module implements body content extraction between markdown headings as
specified in T:0005, working with ID extraction to create complete DocElements.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum


@dataclass
class BodyRange:
    """
    Represents the location and boundaries of element body content.
    """
    # Content boundaries
    start_line: int              # Start line number (0-based, inclusive)
    end_line: int                # End line number (0-based, exclusive)
    start_byte: int              # Start byte position (0-based, inclusive)
    end_byte: int                # End byte position (0-based, exclusive)

    # Content data
    raw_content: str             # Original body content with formatting
    stripped_content: str        # Content with leading/trailing whitespace removed

    # Metadata
    line_count: int              # Number of lines in body
    char_count: int              # Number of characters in stripped content

    def __post_init__(self):
        """Validate range boundaries."""
        if self.start_line < 0 or self.end_line < self.start_line:
            raise ValueError(f"Invalid line range: {self.start_line} to {self.end_line}")

        if self.start_byte < 0 or self.end_byte < self.start_byte:
            raise ValueError(f"Invalid byte range: {self.start_byte} to {self.end_byte}")


@dataclass
class HeadingBoundary:
    """
    Represents a heading and its position in the document.
    """
    line_number: int             # Line number (0-based)
    byte_position: int           # Byte position in document (0-based)
    heading_level: int           # Heading level (1-6)
    heading_text: str            # Complete heading text
    element_id: Optional[str]    # Extracted ID if present

    def is_same_or_higher_level(self, other_level: int) -> bool:
        """Check if this heading is at same or higher level than given level."""
        return self.heading_level <= other_level


class BodyExtractionError(Exception):
    """Exception raised when body extraction fails."""
    pass


class MarkdownBodyExtractor:
    """
    Extracts body content between markdown headings while preserving formatting.
    """

    # Regex pattern to match markdown headings
    HEADING_PATTERN = re.compile(
        r'^(#{1,6})\s+(.+?)$',  # Capture heading level and text
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the body extractor."""
        self.current_text = ""
        self.current_lines = []
        self.heading_boundaries = []

    def extract_body_ranges(self, markdown_text: str) -> List[Tuple[HeadingBoundary, BodyRange]]:
        """
        Extract body content ranges for all headings in markdown text.

        Args:
            markdown_text: The markdown content to parse.

        Returns:
            List of (heading, body_range) tuples for each element.

        Raises:
            BodyExtractionError: If parsing fails.
        """
        try:
            self.current_text = markdown_text
            self.current_lines = markdown_text.split('\n')

            # Find all heading boundaries
            self.heading_boundaries = self._find_heading_boundaries()

            # Extract body for each heading
            body_ranges = []
            for i, heading in enumerate(self.heading_boundaries):
                body_range = self._extract_body_for_heading(i)
                body_ranges.append((heading, body_range))

            return body_ranges

        except Exception as e:
            raise BodyExtractionError(f"Failed to extract body ranges: {e}")

    def extract_single_body(self, markdown_text: str, heading_line: int) -> BodyRange:
        """
        Extract body content for a specific heading line.

        Args:
            markdown_text: The markdown content.
            heading_line: Line number of the heading (0-based).

        Returns:
            BodyRange for the specified heading.

        Raises:
            BodyExtractionError: If heading not found or extraction fails.
        """
        self.current_text = markdown_text
        self.current_lines = markdown_text.split('\n')

        # Find all headings to determine boundaries
        self.heading_boundaries = self._find_heading_boundaries()

        # Find the heading at the specified line
        target_heading = None
        heading_index = None

        for i, boundary in enumerate(self.heading_boundaries):
            if boundary.line_number == heading_line:
                target_heading = boundary
                heading_index = i
                break

        if target_heading is None:
            raise BodyExtractionError(f"No heading found at line {heading_line}")

        return self._extract_body_for_heading(heading_index)

    def _find_heading_boundaries(self) -> List[HeadingBoundary]:
        """Find all heading boundaries in the current text."""
        boundaries = []
        byte_position = 0

        for line_num, line in enumerate(self.current_lines):
            # Check if line is a heading
            heading_match = self.HEADING_PATTERN.match(line)

            if heading_match:
                heading_markers, heading_text = heading_match.groups()
                heading_level = len(heading_markers)

                # Try to extract ID from heading text (basic check)
                element_id = self._extract_id_from_heading_text(heading_text.strip())

                boundary = HeadingBoundary(
                    line_number=line_num,
                    byte_position=byte_position,
                    heading_level=heading_level,
                    heading_text=heading_text.strip(),
                    element_id=element_id
                )

                boundaries.append(boundary)

            # Update byte position (including newline character)
            byte_position += len(line.encode('utf-8')) + 1

        return boundaries

    def _extract_id_from_heading_text(self, heading_text: str) -> Optional[str]:
        """Extract ID from heading text if present."""
        # Simple regex to detect ID at start of heading
        id_pattern = re.compile(r'^(R:|C:|D:|I:|M:|UI:|T:|TP:)([A-Za-z0-9_-]+)', re.IGNORECASE)
        match = id_pattern.match(heading_text)

        if match:
            return match.group(0)  # Return full ID

        return None

    def _extract_body_for_heading(self, heading_index: int) -> BodyRange:
        """Extract body content for a specific heading by index."""
        current_heading = self.heading_boundaries[heading_index]

        # Determine body start (line after heading)
        body_start_line = current_heading.line_number + 1

        # Determine body end (next heading at any level, or end of document)
        body_end_line = len(self.current_lines)  # Default to end of document

        # Find the next heading (any level stops the current element's content)
        if heading_index + 1 < len(self.heading_boundaries):
            next_heading = self.heading_boundaries[heading_index + 1]
            body_end_line = next_heading.line_number

        # Extract body lines
        if body_start_line >= len(self.current_lines):
            # Heading is at end of document
            body_lines = []
        else:
            body_lines = self.current_lines[body_start_line:body_end_line]

        # Calculate byte positions
        body_start_byte = self._calculate_byte_position(body_start_line)
        body_end_byte = self._calculate_byte_position(body_end_line)

        # Create content strings
        raw_content = '\n'.join(body_lines)
        stripped_content = raw_content.strip()

        return BodyRange(
            start_line=body_start_line,
            end_line=body_end_line,
            start_byte=body_start_byte,
            end_byte=body_end_byte,
            raw_content=raw_content,
            stripped_content=stripped_content,
            line_count=len(body_lines),
            char_count=len(stripped_content)
        )

    def _calculate_byte_position(self, line_number: int) -> int:
        """Calculate byte position for the start of a line."""
        if line_number >= len(self.current_lines):
            # Position at end of document
            return len(self.current_text.encode('utf-8'))

        byte_position = 0
        for i in range(line_number):
            if i < len(self.current_lines):
                # Add line length + newline character
                byte_position += len(self.current_lines[i].encode('utf-8')) + 1

        return byte_position

    def extract_and_update_content(self, markdown_text: str, heading_line: int,
                                  new_content: str) -> str:
        """
        Extract body and return updated markdown with new content.

        Args:
            markdown_text: Original markdown content.
            heading_line: Line number of heading to update (0-based).
            new_content: New body content to replace existing.

        Returns:
            Updated markdown text with new content.

        Raises:
            BodyExtractionError: If update fails.
        """
        try:
            # Extract current body range
            body_range = self.extract_single_body(markdown_text, heading_line)

            # Split text into parts
            lines = markdown_text.split('\n')

            # Prepare new content lines
            new_lines = new_content.split('\n') if new_content else ['']

            # Reconstruct document
            before_lines = lines[:body_range.start_line]
            after_lines = lines[body_range.end_line:]

            updated_lines = before_lines + new_lines + after_lines

            return '\n'.join(updated_lines)

        except Exception as e:
            raise BodyExtractionError(f"Failed to update content: {e}")

    def get_element_summary(self, heading: HeadingBoundary, body: BodyRange) -> dict:
        """Get summary information for an element."""
        return {
            'id': heading.element_id,
            'heading_text': heading.heading_text,
            'heading_level': heading.heading_level,
            'line_range': (body.start_line, body.end_line),
            'byte_range': (body.start_byte, body.end_byte),
            'content_lines': body.line_count,
            'content_chars': body.char_count,
            'has_content': body.char_count > 0
        }

    def validate_ranges(self, body_ranges: List[Tuple[HeadingBoundary, BodyRange]]) -> List[str]:
        """
        Validate that body ranges don't overlap and cover expected areas.

        Args:
            body_ranges: List of (heading, body_range) tuples to validate.

        Returns:
            List of validation warnings/errors.
        """
        warnings = []

        for i, (heading, body_range) in enumerate(body_ranges):
            # Check for valid ranges
            if body_range.start_line < 0 or body_range.end_line < body_range.start_line:
                warnings.append(f"Invalid line range for {heading.element_id or 'heading at line ' + str(heading.line_number)}")

            # Check for overlapping ranges
            if i > 0:
                prev_heading, prev_body = body_ranges[i-1]
                if body_range.start_line < prev_body.end_line:
                    warnings.append(f"Overlapping ranges between {prev_heading.element_id} and {heading.element_id}")

            # Check byte position consistency
            calculated_start = self._calculate_byte_position(body_range.start_line)
            if abs(calculated_start - body_range.start_byte) > 10:  # Allow small encoding differences
                warnings.append(f"Byte position mismatch for {heading.element_id}")

        return warnings


def extract_body_content(markdown_text: str, heading_line: int) -> BodyRange:
    """
    Convenience function to extract body content for a single heading.

    Args:
        markdown_text: Markdown content to parse.
        heading_line: Line number of heading (0-based).

    Returns:
        BodyRange with extracted content.
    """
    extractor = MarkdownBodyExtractor()
    return extractor.extract_single_body(markdown_text, heading_line)


def extract_all_bodies(markdown_text: str) -> List[Tuple[HeadingBoundary, BodyRange]]:
    """
    Convenience function to extract all body contents from markdown.

    Args:
        markdown_text: Markdown content to parse.

    Returns:
        List of (heading, body_range) tuples.
    """
    extractor = MarkdownBodyExtractor()
    return extractor.extract_body_ranges(markdown_text)