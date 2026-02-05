"""
Reference detection for Project1 document parsing.

This module implements reference detection within markdown body content as
specified in T:0006, finding both inline and explicit references to other elements.
"""

import re
from dataclasses import dataclass
from typing import List, Set, Dict, Optional, Tuple
from enum import Enum


@dataclass
class Reference:
    """
    Represents a detected reference to another element.
    """
    target_id: str               # ID being referenced (e.g., "C:WorkspaceManager")
    reference_type: str          # Type of reference ("inline", "explicit")
    context: str                 # Surrounding text context
    line_number: int             # Line number where reference was found (0-based)
    position_in_line: int        # Character position in line (0-based)

    def __post_init__(self):
        """Validate reference data."""
        if not self.target_id:
            raise ValueError("Reference target_id cannot be empty")

        if self.reference_type not in ["inline", "explicit"]:
            raise ValueError(f"Invalid reference type: {self.reference_type}")


class ReferenceDetectionError(Exception):
    """Exception raised when reference detection fails."""
    pass


class ReferenceDetector:
    """
    Detects references to other elements within markdown body content.
    """

    # Pattern to match valid ID formats (from T:0004)
    ID_PATTERN = re.compile(
        r'\b(R:|C:|D:|I:|M:|UI:|T:|TP:)([A-Za-z0-9][A-Za-z0-9_-]*)\b',
        re.IGNORECASE
    )

    # Pattern to find explicit "References:" sections
    REFERENCES_SECTION_PATTERN = re.compile(
        r'^#{1,6}\s*References?:\s*$',  # Any heading level "References:" or "Reference:"
        re.MULTILINE | re.IGNORECASE
    )

    # Pattern to extract references from explicit sections
    EXPLICIT_REF_PATTERN = re.compile(
        r'^\s*[-*]\s+(.+)$',  # List items starting with - or *
        re.MULTILINE
    )

    def __init__(self, known_ids: Optional[Set[str]] = None):
        """
        Initialize reference detector.

        Args:
            known_ids: Set of valid IDs for validation (optional).
        """
        self.known_ids = known_ids or set()

    def _is_valid_id_suffix(self, suffix: str, prefix: str) -> bool:
        """Check if ID suffix is valid for the given prefix."""
        if not suffix:
            return False

        # For task (T:) and test (TP:) IDs, allow numeric suffixes
        # For other IDs, must start with letter
        if prefix in ["T:", "TP:"]:
            # Tasks and tests can start with numbers (e.g., T:0001, TP:0001)
            return suffix[0].isalnum()
        else:
            # Other IDs must start with letter
            return suffix[0].isalpha()

    def _is_valid_id(self, prefix: str, suffix: str) -> bool:
        """Check if the ID combination is valid."""
        valid_prefixes = {"R:", "C:", "D:", "I:", "M:", "UI:", "T:", "TP:"}
        return prefix in valid_prefixes and self._is_valid_id_suffix(suffix, prefix)

    def detect_references_in_text(self, body_text: str) -> List[Reference]:
        """
        Detect all references within body text.

        Args:
            body_text: The body content to scan for references.

        Returns:
            List of detected references.

        Raises:
            ReferenceDetectionError: If detection fails.
        """
        try:
            references = []

            # Find explicit references first (they take priority)
            explicit_refs = self._find_explicit_references(body_text)
            references.extend(explicit_refs)

            # Find inline references
            inline_refs = self._find_inline_references(body_text)
            references.extend(inline_refs)

            # Deduplicate references while preserving order (explicit refs win)
            seen_ids = set()
            unique_references = []

            for ref in references:
                if ref.target_id not in seen_ids:
                    seen_ids.add(ref.target_id)
                    unique_references.append(ref)

            return unique_references

        except Exception as e:
            raise ReferenceDetectionError(f"Failed to detect references: {e}")

    def _find_inline_references(self, body_text: str) -> List[Reference]:
        """Find inline ID references within body text."""
        references = []
        lines = body_text.split('\n')

        for line_num, line in enumerate(lines):
            # Find all ID patterns in this line
            for match in self.ID_PATTERN.finditer(line):
                prefix, suffix = match.groups()
                # Normalize prefix to uppercase for consistency
                normalized_prefix = prefix.upper()

                # Validate the ID format
                if not self._is_valid_id(normalized_prefix, suffix):
                    continue  # Skip invalid IDs

                full_id = normalized_prefix + suffix

                # Create context (surrounding text)
                start_pos = max(0, match.start() - 20)
                end_pos = min(len(line), match.end() + 20)
                context = line[start_pos:end_pos].strip()

                references.append(Reference(
                    target_id=full_id,
                    reference_type="inline",
                    context=context,
                    line_number=line_num,
                    position_in_line=match.start()
                ))

        return references

    def _find_explicit_references(self, body_text: str) -> List[Reference]:
        """Find references in explicit 'References:' sections."""
        references = []

        # Find "References:" section headers
        ref_sections = list(self.REFERENCES_SECTION_PATTERN.finditer(body_text))

        if not ref_sections:
            return references

        lines = body_text.split('\n')

        for section_match in ref_sections:
            # Find the line number of the "References:" header
            header_pos = section_match.start()
            header_line_num = body_text[:header_pos].count('\n')

            # Scan lines after the header for list items
            section_references = self._parse_references_section(
                lines, header_line_num + 1
            )
            references.extend(section_references)

        return references

    def _parse_references_section(self, lines: List[str], start_line: int) -> List[Reference]:
        """Parse references from a References: section."""
        references = []

        for line_num in range(start_line, len(lines)):
            line = lines[line_num]

            # Stop if we hit another heading or empty section
            if line.strip().startswith('#') or (
                not line.strip() and
                line_num + 1 < len(lines) and
                lines[line_num + 1].strip().startswith('#')
            ):
                break

            # Look for list items
            list_match = self.EXPLICIT_REF_PATTERN.match(line)
            if list_match:
                list_content = list_match.group(1).strip()

                # Extract IDs from list content
                for id_match in self.ID_PATTERN.finditer(list_content):
                    prefix, suffix = id_match.groups()
                    # Normalize prefix to uppercase for consistency
                    normalized_prefix = prefix.upper()

                    # Validate the ID format
                    if not self._is_valid_id(normalized_prefix, suffix):
                        continue  # Skip invalid IDs

                    full_id = normalized_prefix + suffix

                    references.append(Reference(
                        target_id=full_id,
                        reference_type="explicit",
                        context=list_content,
                        line_number=line_num,
                        position_in_line=id_match.start() + len(line) - len(line.lstrip())
                    ))

        return references

    def validate_references(self, references: List[Reference]) -> Dict[str, List[str]]:
        """
        Validate references against known IDs.

        Args:
            references: List of references to validate.

        Returns:
            Dict with 'valid' and 'invalid' keys containing lists of IDs.
        """
        valid_ids = []
        invalid_ids = []

        for ref in references:
            if ref.target_id in self.known_ids:
                valid_ids.append(ref.target_id)
            else:
                invalid_ids.append(ref.target_id)

        return {
            'valid': valid_ids,
            'invalid': invalid_ids
        }

    def extract_reference_ids(self, references: List[Reference]) -> List[str]:
        """
        Extract unique reference IDs from reference list.

        Args:
            references: List of detected references.

        Returns:
            List of unique referenced IDs.
        """
        seen_ids = set()
        unique_ids = []

        for ref in references:
            if ref.target_id not in seen_ids:
                seen_ids.add(ref.target_id)
                unique_ids.append(ref.target_id)

        return unique_ids

    def get_reference_statistics(self, references: List[Reference]) -> Dict[str, int]:
        """
        Get statistics about detected references.

        Args:
            references: List of references to analyze.

        Returns:
            Dict with reference statistics.
        """
        stats = {
            'total_references': len(references),
            'unique_targets': len(set(ref.target_id for ref in references)),
            'inline_references': len([r for r in references if r.reference_type == "inline"]),
            'explicit_references': len([r for r in references if r.reference_type == "explicit"])
        }

        # Count by prefix
        prefix_counts = {}
        for ref in references:
            prefix = ref.target_id.split(':')[0] + ':'
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        stats['by_prefix'] = prefix_counts

        return stats

    def find_broken_references(self, references: List[Reference]) -> List[Reference]:
        """
        Find references that point to unknown IDs.

        Args:
            references: List of references to check.

        Returns:
            List of references with invalid target IDs.
        """
        if not self.known_ids:
            return []  # Can't validate without known IDs

        broken_refs = []
        for ref in references:
            if ref.target_id not in self.known_ids:
                broken_refs.append(ref)

        return broken_refs

    def group_references_by_target(self, references: List[Reference]) -> Dict[str, List[Reference]]:
        """
        Group references by their target ID.

        Args:
            references: List of references to group.

        Returns:
            Dict mapping target IDs to lists of references.
        """
        grouped = {}

        for ref in references:
            if ref.target_id not in grouped:
                grouped[ref.target_id] = []
            grouped[ref.target_id].append(ref)

        return grouped

    def find_reference_patterns(self, references: List[Reference]) -> Dict[str, List[str]]:
        """
        Analyze common reference patterns in context.

        Args:
            references: List of references to analyze.

        Returns:
            Dict mapping patterns to example contexts.
        """
        patterns = {
            'implements': [],
            'uses': [],
            'extends': [],
            'calls': [],
            'references': [],
            'see': [],
            'based_on': [],
            'other': []
        }

        for ref in references:
            context_lower = ref.context.lower()

            # Use word boundaries for more precise matching
            if 'implement' in context_lower:
                patterns['implements'].append(ref.context)
            elif 'call' in context_lower:  # Check 'call' before 'use' to avoid conflicts
                patterns['calls'].append(ref.context)
            elif 'use' in context_lower or 'using' in context_lower:
                patterns['uses'].append(ref.context)
            elif 'extend' in context_lower:
                patterns['extends'].append(ref.context)
            elif 'reference' in context_lower:
                patterns['references'].append(ref.context)
            elif 'see' in context_lower:
                patterns['see'].append(ref.context)
            elif 'based' in context_lower:
                patterns['based_on'].append(ref.context)
            else:
                patterns['other'].append(ref.context)

        # Remove empty lists and limit examples
        return {
            pattern: examples[:3]  # Limit to 3 examples each
            for pattern, examples in patterns.items()
            if examples
        }


def detect_references(body_text: str, known_ids: Optional[Set[str]] = None) -> List[Reference]:
    """
    Convenience function to detect references in body text.

    Args:
        body_text: Text content to scan for references.
        known_ids: Optional set of known IDs for validation.

    Returns:
        List of detected references.
    """
    detector = ReferenceDetector(known_ids)
    return detector.detect_references_in_text(body_text)


def extract_reference_ids(body_text: str, known_ids: Optional[Set[str]] = None) -> List[str]:
    """
    Convenience function to extract unique reference IDs from text.

    Args:
        body_text: Text content to scan for references.
        known_ids: Optional set of known IDs for validation.

    Returns:
        List of unique referenced IDs.
    """
    detector = ReferenceDetector(known_ids)
    references = detector.detect_references_in_text(body_text)
    return detector.extract_reference_ids(references)