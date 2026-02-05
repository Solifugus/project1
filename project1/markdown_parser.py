"""
Full markdown parsing for Project1 document processing.

This module implements T:0007, integrating ID extraction, body extraction, and
reference detection to create complete DocElement objects from markdown files.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from doc_element import DocElement, Kind, File, Status
from id_extraction import extract_ids_from_markdown
from body_extraction import extract_all_bodies, BodyExtractionError
from reference_detection import detect_references, ReferenceDetectionError


class MarkdownParsingError(Exception):
    """Exception raised when markdown parsing fails."""
    pass


@dataclass
class ParsedElement:
    """Intermediate representation during parsing."""
    id: Optional[str]
    title: str
    heading_level: int
    line_number: int
    body_content: str
    refs: List[str]


class MarkdownParser:
    """
    Parses markdown files into lists of DocElement objects.

    Integrates ID extraction, body extraction, and reference detection
    to create complete document element representations.
    """

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize parser.

        Args:
            file_path: Path to the markdown file being parsed (for File enum detection).
        """
        self.file_path = file_path
        self.file_enum = self._determine_file_enum(file_path)

    def _determine_file_enum(self, file_path: Optional[str]) -> Optional[File]:
        """Determine File enum from file path."""
        if not file_path:
            return None

        filename = Path(file_path).stem.lower()

        file_mapping = {
            'conventions': File.CONVENTIONS,
            'software-design': File.SOFTWARE_DESIGN,
            'development-plan': File.DEVELOPMENT_PLAN,
            'test-plan': File.TEST_PLAN,
        }

        return file_mapping.get(filename)

    def _determine_kind_from_id(self, element_id: str) -> Kind:
        """Determine element kind from ID prefix."""
        if not element_id or ':' not in element_id:
            return Kind.OTHER

        prefix = element_id.split(':', 1)[0].upper() + ':'

        kind_mapping = {
            'R:': Kind.REQUIREMENT,
            'C:': Kind.COMPONENT,
            'D:': Kind.DATA,
            'I:': Kind.INTERFACE,
            'M:': Kind.METHOD,
            'UI:': Kind.UI,
            'T:': Kind.TASK,
            'TP:': Kind.TEST,
        }

        return kind_mapping.get(prefix, Kind.OTHER)

    def _create_anchor(self, title: str) -> str:
        """Create URL anchor from title text."""
        # Convert to lowercase, replace spaces with hyphens, keep only alphanumeric and hyphens
        anchor = re.sub(r'[^\w\s-]', '', title.lower())
        anchor = re.sub(r'\s+', '-', anchor)
        anchor = re.sub(r'-+', '-', anchor)  # Collapse multiple hyphens
        return anchor.strip('-')

    def _extract_title_from_heading(self, heading_text: str) -> str:
        """Extract clean title from heading text, removing ID prefix if present."""
        # Remove leading # characters and whitespace
        title = re.sub(r'^#+\s*', '', heading_text).strip()

        # If title starts with ID: pattern, extract just the descriptive part
        id_match = re.match(r'^([A-Za-z]+:\w+)\s*-\s*(.+)$', title)
        if id_match:
            return id_match.group(2).strip()

        return title

    def parse_markdown(self, markdown_content: str) -> List[DocElement]:
        """
        Parse markdown content into DocElement objects.

        Args:
            markdown_content: Raw markdown file content.

        Returns:
            List of DocElement objects.

        Raises:
            MarkdownParsingError: If parsing fails.
        """
        try:
            # Extract body ranges using existing body extraction
            body_ranges = extract_all_bodies(markdown_content)

            if not body_ranges:
                return []  # No elements found

            # Convert to parsed elements
            parsed_elements = []

            for heading_boundary, body_range in body_ranges:
                # Extract ID from heading if present
                # Reconstruct full heading for ID extraction
                full_heading = '#' * heading_boundary.heading_level + ' ' + heading_boundary.heading_text
                extracted_ids = extract_ids_from_markdown(full_heading)
                element_id = extracted_ids[0].full_id if extracted_ids else None

                # Extract references from body content
                try:
                    references = detect_references(body_range.stripped_content or "")
                    ref_ids = [ref.target_id for ref in references]
                except ReferenceDetectionError:
                    ref_ids = []  # Continue parsing even if reference detection fails

                parsed_element = ParsedElement(
                    id=element_id,
                    title=self._extract_title_from_heading(heading_boundary.heading_text),
                    heading_level=heading_boundary.heading_level,
                    line_number=heading_boundary.line_number,
                    body_content=body_range.stripped_content or "",
                    refs=ref_ids
                )

                parsed_elements.append(parsed_element)

            # Convert to DocElement objects
            doc_elements = []

            for parsed in parsed_elements:
                try:
                    doc_element = self._create_doc_element(parsed)
                    doc_elements.append(doc_element)
                except Exception as e:
                    # Log warning but continue with other elements
                    print(f"Warning: Failed to create DocElement for '{parsed.title}': {e}")
                    continue

            return doc_elements

        except (BodyExtractionError, Exception) as e:
            raise MarkdownParsingError(f"Failed to parse markdown: {e}")

    def _create_doc_element(self, parsed: ParsedElement) -> DocElement:
        """Create DocElement from parsed data."""
        # Determine element kind
        if parsed.id:
            kind = self._determine_kind_from_id(parsed.id)
        else:
            kind = Kind.OTHER

        # Use ID if available, otherwise generate a placeholder
        element_id = parsed.id or f"NoID_Line{parsed.line_number}"

        # Default file enum if not determined from path
        file_enum = self.file_enum or File.SOFTWARE_DESIGN  # Default fallback

        # Create anchor from title
        anchor = self._create_anchor(parsed.title)

        # Determine status for tasks
        status = None
        if kind == Kind.TASK:
            # Try to extract status from body content
            status = self._extract_task_status(parsed.body_content)

        return DocElement(
            id=element_id,
            kind=kind,
            title=parsed.title,
            file=file_enum,
            heading_level=parsed.heading_level,
            anchor=anchor,
            body_markdown=parsed.body_content,
            refs=parsed.refs,
            backlinks=[],  # Will be computed later during indexing
            status=status
        )

    def _extract_task_status(self, body_content: str) -> Status:
        """Extract task status from body content."""
        content_lower = body_content.lower()

        # Look for status indicators in the content
        if any(word in content_lower for word in ['completed', 'done', 'finished']):
            return Status.COMPLETED
        elif any(word in content_lower for word in ['in progress', 'working', 'implementing']):
            return Status.IN_PROGRESS
        else:
            return Status.PENDING

    def parse_file(self, file_path: str) -> List[DocElement]:
        """
        Parse a markdown file and return DocElement objects.

        Args:
            file_path: Path to the markdown file.

        Returns:
            List of DocElement objects.

        Raises:
            MarkdownParsingError: If file reading or parsing fails.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update file path for this parsing operation
            old_file_path = self.file_path
            old_file_enum = self.file_enum

            self.file_path = file_path
            self.file_enum = self._determine_file_enum(file_path)

            try:
                return self.parse_markdown(content)
            finally:
                # Restore original file path
                self.file_path = old_file_path
                self.file_enum = old_file_enum

        except IOError as e:
            raise MarkdownParsingError(f"Failed to read file '{file_path}': {e}")

    def validate_parsed_elements(self, elements: List[DocElement]) -> List[str]:
        """
        Validate parsed elements and return list of warnings.

        Args:
            elements: List of parsed DocElement objects.

        Returns:
            List of validation warning messages.
        """
        warnings = []

        seen_ids = set()

        for element in elements:
            # Check for duplicate IDs
            if element.id in seen_ids:
                warnings.append(f"Duplicate ID found: {element.id}")
            seen_ids.add(element.id)

            # Check for empty titles
            if not element.title.strip():
                warnings.append(f"Empty title for element: {element.id}")

            # Check for reasonable heading levels
            if element.heading_level < 1 or element.heading_level > 6:
                warnings.append(f"Invalid heading level {element.heading_level} for: {element.id}")

            # Check task status consistency
            if element.kind == Kind.TASK and element.status is None:
                warnings.append(f"Task missing status: {element.id}")
            elif element.kind != Kind.TASK and element.status is not None:
                warnings.append(f"Non-task has status: {element.id}")

        return warnings

    def get_parsing_statistics(self, elements: List[DocElement]) -> Dict[str, Any]:
        """
        Get statistics about parsed elements.

        Args:
            elements: List of parsed DocElement objects.

        Returns:
            Dictionary with parsing statistics.
        """
        if not elements:
            return {'total_elements': 0}

        # Count by kind
        kind_counts = {}
        for element in elements:
            kind_name = element.kind.value
            kind_counts[kind_name] = kind_counts.get(kind_name, 0) + 1

        # Count by heading level
        level_counts = {}
        for element in elements:
            level = element.heading_level
            level_counts[f"h{level}"] = level_counts.get(f"h{level}", 0) + 1

        # Calculate total references
        total_refs = sum(len(element.refs) for element in elements)
        avg_refs = total_refs / len(elements) if elements else 0

        # Count elements with and without content
        with_content = sum(1 for e in elements if e.body_markdown.strip())
        without_content = len(elements) - with_content

        return {
            'total_elements': len(elements),
            'by_kind': kind_counts,
            'by_heading_level': level_counts,
            'total_references': total_refs,
            'average_references_per_element': round(avg_refs, 2),
            'elements_with_content': with_content,
            'elements_without_content': without_content,
            'unique_ids': len(set(e.id for e in elements)),
        }


def parse_markdown_file(file_path: str) -> List[DocElement]:
    """
    Convenience function to parse a markdown file.

    Args:
        file_path: Path to the markdown file.

    Returns:
        List of DocElement objects.
    """
    parser = MarkdownParser(file_path)
    return parser.parse_file(file_path)


def parse_markdown_content(content: str, file_path: Optional[str] = None) -> List[DocElement]:
    """
    Convenience function to parse markdown content.

    Args:
        content: Raw markdown content.
        file_path: Optional file path for File enum detection.

    Returns:
        List of DocElement objects.
    """
    parser = MarkdownParser(file_path)
    return parser.parse_markdown(content)