"""
Indexer data structures for Project1 document management.

This module implements T:0010, creating efficient lookup maps for elements
and references as specified in C:Indexer.
"""

from typing import Dict, List, Set, Optional, Tuple, Iterator
from dataclasses import dataclass, field
from pathlib import Path
import re
import time
from collections import defaultdict

from doc_element import DocElement, Kind, File, Status


@dataclass
class IndexStatistics:
    """Statistics about the document index."""
    total_elements: int = 0
    elements_by_kind: Dict[str, int] = field(default_factory=dict)
    elements_by_file: Dict[str, int] = field(default_factory=dict)
    total_references: int = 0
    total_backlinks: int = 0
    orphaned_references: int = 0  # References to non-existent elements
    elements_without_refs: int = 0
    search_index_size: int = 0
    last_updated: float = field(default_factory=time.time)


@dataclass
class SearchMatch:
    """Represents a search result match."""
    element_id: str
    element_title: str
    match_type: str  # 'id_exact', 'id_partial', 'title_exact', 'title_partial'
    match_score: float  # 0.0 to 1.0, higher is better match
    matched_text: str  # The text that was matched


class IndexError(Exception):
    """Exception raised when indexing operations fail."""
    pass


class DocumentIndex:
    """
    Main document index providing fast lookups and search capabilities.

    Implements the core data structures needed for C:Indexer functionality.
    """

    def __init__(self):
        """Initialize empty document index."""
        # Core element storage
        self._elements: Dict[str, DocElement] = {}  # id -> DocElement

        # File-based mappings
        self._file_elements: Dict[str, Set[str]] = defaultdict(set)  # file -> {element_ids}

        # Reference graph structures
        self._references: Dict[str, Set[str]] = defaultdict(set)  # element_id -> {referenced_ids}
        self._backlinks: Dict[str, Set[str]] = defaultdict(set)   # element_id -> {referencing_ids}

        # Search index structures
        self._title_index: Dict[str, Set[str]] = defaultdict(set)  # normalized_word -> {element_ids}
        self._id_index: Dict[str, str] = {}  # normalized_id -> actual_id
        self._partial_id_index: Dict[str, Set[str]] = defaultdict(set)  # partial_id -> {element_ids}

        # Index metadata
        self._last_updated = time.time()

    def add_element(self, element: DocElement) -> None:
        """
        Add an element to the index.

        Args:
            element: DocElement to add to the index.

        Raises:
            IndexError: If element cannot be added.
        """
        try:
            element_id = element.id

            # Remove existing element if present (for updates)
            if element_id in self._elements:
                self.remove_element(element_id)

            # Add to core storage
            self._elements[element_id] = element

            # Add to file mapping
            file_key = element.file.value
            self._file_elements[file_key].add(element_id)

            # Build reference mappings
            self._add_element_references(element)

            # Update search indices
            self._add_to_search_index(element)

            self._last_updated = time.time()

        except Exception as e:
            raise IndexError(f"Failed to add element {element.id}: {e}")

    def remove_element(self, element_id: str) -> bool:
        """
        Remove an element from the index.

        Args:
            element_id: ID of element to remove.

        Returns:
            True if element was removed, False if not found.
        """
        if element_id not in self._elements:
            return False

        try:
            element = self._elements[element_id]

            # Remove from core storage
            del self._elements[element_id]

            # Remove from file mapping
            file_key = element.file.value
            self._file_elements[file_key].discard(element_id)
            if not self._file_elements[file_key]:
                del self._file_elements[file_key]

            # Remove reference mappings
            self._remove_element_references(element_id)

            # Remove from search indices
            self._remove_from_search_index(element)

            self._last_updated = time.time()
            return True

        except Exception as e:
            raise IndexError(f"Failed to remove element {element_id}: {e}")

    def get_element(self, element_id: str) -> Optional[DocElement]:
        """
        Get element by ID with O(1) lookup.

        Args:
            element_id: Element ID to lookup.

        Returns:
            DocElement if found, None otherwise.
        """
        return self._elements.get(element_id)

    def has_element(self, element_id: str) -> bool:
        """
        Check if element exists in index.

        Args:
            element_id: Element ID to check.

        Returns:
            True if element exists, False otherwise.
        """
        return element_id in self._elements

    def get_elements_by_file(self, file: File) -> List[DocElement]:
        """
        Get all elements from a specific file.

        Args:
            file: File enum to get elements for.

        Returns:
            List of DocElements from the file.
        """
        file_key = file.value
        element_ids = self._file_elements.get(file_key, set())
        return [self._elements[eid] for eid in element_ids if eid in self._elements]

    def get_all_elements(self) -> List[DocElement]:
        """
        Get all elements in the index.

        Returns:
            List of all DocElements.
        """
        return list(self._elements.values())

    def get_references(self, element_id: str) -> List[str]:
        """
        Get all IDs referenced by an element.

        Args:
            element_id: ID of element to get references for.

        Returns:
            List of referenced element IDs.
        """
        return list(self._references.get(element_id, set()))

    def get_backlinks(self, element_id: str) -> List[str]:
        """
        Get all IDs that reference an element.

        Args:
            element_id: ID of element to get backlinks for.

        Returns:
            List of element IDs that reference this element.
        """
        return list(self._backlinks.get(element_id, set()))

    def get_reference_graph(self) -> Dict[str, List[str]]:
        """
        Get complete reference graph.

        Returns:
            Dictionary mapping element_id -> list of referenced IDs.
        """
        return {eid: list(refs) for eid, refs in self._references.items() if refs}

    def search(self, query: str, limit: int = 10) -> List[SearchMatch]:
        """
        Search for elements by ID or title with partial matching support.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of SearchMatch objects sorted by relevance.
        """
        if not query.strip():
            return []

        query_normalized = self._normalize_for_search(query.strip())
        matches = []

        # Exact ID match (highest priority)
        exact_id = self._id_index.get(query_normalized)
        if exact_id and exact_id in self._elements:
            element = self._elements[exact_id]
            matches.append(SearchMatch(
                element_id=exact_id,
                element_title=element.title,
                match_type='id_exact',
                match_score=1.0,
                matched_text=exact_id
            ))

        # Partial ID matches
        for partial_id, element_ids in self._partial_id_index.items():
            if query_normalized in partial_id and query_normalized != partial_id:
                for element_id in element_ids:
                    if element_id in self._elements and element_id != exact_id:
                        element = self._elements[element_id]
                        # Score based on how much of the ID matches
                        score = len(query_normalized) / len(partial_id)
                        matches.append(SearchMatch(
                            element_id=element_id,
                            element_title=element.title,
                            match_type='id_partial',
                            match_score=score * 0.9,  # Slightly lower than exact
                            matched_text=element_id
                        ))

        # Title word matches
        query_words = query_normalized.split()
        for word in query_words:
            if word in self._title_index:
                for element_id in self._title_index[word]:
                    if element_id in self._elements:
                        element = self._elements[element_id]

                        # Check if this is exact title match
                        element_title_norm = self._normalize_for_search(element.title)
                        if element_title_norm == query_normalized:
                            score = 0.95
                            match_type = 'title_exact'
                        else:
                            # Score based on word coverage
                            title_words = element_title_norm.split()
                            matching_words = sum(1 for w in query_words if w in title_words)
                            score = matching_words / max(len(query_words), len(title_words))
                            match_type = 'title_partial'

                        # Avoid duplicates from multiple word matches
                        if not any(m.element_id == element_id for m in matches):
                            matches.append(SearchMatch(
                                element_id=element_id,
                                element_title=element.title,
                                match_type=match_type,
                                match_score=score * 0.8,  # Lower than ID matches
                                matched_text=element.title
                            ))

        # Sort by score (descending) and return limited results
        matches.sort(key=lambda m: m.match_score, reverse=True)
        return matches[:limit]

    def get_statistics(self) -> IndexStatistics:
        """
        Get comprehensive statistics about the index.

        Returns:
            IndexStatistics with current index state.
        """
        # Count elements by kind
        kind_counts = defaultdict(int)
        for element in self._elements.values():
            kind_counts[element.kind.value] += 1

        # Count elements by file
        file_counts = defaultdict(int)
        for element in self._elements.values():
            file_counts[element.file.value] += 1

        # Count references and orphans
        total_refs = sum(len(refs) for refs in self._references.values())
        total_backlinks = sum(len(backlinks) for backlinks in self._backlinks.values())

        # Find orphaned references (references to non-existent elements)
        orphaned = 0
        for refs in self._references.values():
            orphaned += sum(1 for ref_id in refs if ref_id not in self._elements)

        # Count elements without any references
        no_refs = sum(1 for element_id in self._elements if not self._references.get(element_id))

        return IndexStatistics(
            total_elements=len(self._elements),
            elements_by_kind=dict(kind_counts),
            elements_by_file=dict(file_counts),
            total_references=total_refs,
            total_backlinks=total_backlinks,
            orphaned_references=orphaned,
            elements_without_refs=no_refs,
            search_index_size=len(self._title_index),
            last_updated=self._last_updated
        )

    def validate_references(self) -> Dict[str, List[str]]:
        """
        Validate all references and return issues.

        Returns:
            Dictionary with 'broken_references' and 'missing_backlinks' lists.
        """
        issues = {
            'broken_references': [],
            'missing_backlinks': []
        }

        # Check for broken references
        for element_id, refs in self._references.items():
            for ref_id in refs:
                if ref_id not in self._elements:
                    issues['broken_references'].append(f"{element_id} -> {ref_id}")

        # Check for missing backlinks (references not properly tracked)
        for element_id, refs in self._references.items():
            for ref_id in refs:
                if ref_id in self._elements:
                    if element_id not in self._backlinks.get(ref_id, set()):
                        issues['missing_backlinks'].append(f"{ref_id} <- {element_id}")

        return issues

    def get_elements_by_kind(self, kind: Kind) -> List[DocElement]:
        """
        Get all elements of a specific kind.

        Args:
            kind: Kind enum to filter by.

        Returns:
            List of DocElements of the specified kind.
        """
        return [element for element in self._elements.values() if element.kind == kind]

    def find_circular_references(self) -> List[List[str]]:
        """
        Find circular reference chains in the reference graph.

        Returns:
            List of circular reference chains (each chain is a list of element IDs).
        """
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(element_id: str, path: List[str]) -> None:
            if element_id in rec_stack:
                # Found a cycle
                cycle_start = path.index(element_id)
                cycles.append(path[cycle_start:] + [element_id])
                return

            if element_id in visited:
                return

            visited.add(element_id)
            rec_stack.add(element_id)

            for ref_id in self._references.get(element_id, set()):
                if ref_id in self._elements:  # Only follow valid references
                    dfs(ref_id, path + [element_id])

            rec_stack.remove(element_id)

        for element_id in self._elements:
            if element_id not in visited:
                dfs(element_id, [])

        return cycles

    def _add_element_references(self, element: DocElement) -> None:
        """Add element's references to the reference graph."""
        element_id = element.id

        # Clear existing references for this element
        old_refs = self._references.get(element_id, set())
        for old_ref in old_refs:
            self._backlinks[old_ref].discard(element_id)

        # Add new references
        new_refs = set(element.refs)
        self._references[element_id] = new_refs

        # Update backlinks
        for ref_id in new_refs:
            self._backlinks[ref_id].add(element_id)

    def _remove_element_references(self, element_id: str) -> None:
        """Remove element's references from the reference graph."""
        # Remove outgoing references
        refs = self._references.get(element_id, set())
        for ref_id in refs:
            self._backlinks[ref_id].discard(element_id)
            if not self._backlinks[ref_id]:
                del self._backlinks[ref_id]

        if element_id in self._references:
            del self._references[element_id]

        # Remove incoming references (backlinks to this element)
        if element_id in self._backlinks:
            for referencing_id in self._backlinks[element_id]:
                self._references[referencing_id].discard(element_id)
            del self._backlinks[element_id]

    def _add_to_search_index(self, element: DocElement) -> None:
        """Add element to search indices."""
        element_id = element.id

        # Add to ID index
        id_normalized = self._normalize_for_search(element_id)
        self._id_index[id_normalized] = element_id

        # Add to partial ID index (for prefix matching)
        for i in range(2, len(element_id) + 1):  # Start from 2 chars
            partial = element_id[:i].lower()
            self._partial_id_index[partial].add(element_id)

        # Add to title index
        title_words = self._normalize_for_search(element.title).split()
        for word in title_words:
            if word:  # Skip empty words
                self._title_index[word].add(element_id)

    def _remove_from_search_index(self, element: DocElement) -> None:
        """Remove element from search indices."""
        element_id = element.id

        # Remove from ID index
        id_normalized = self._normalize_for_search(element_id)
        if id_normalized in self._id_index:
            del self._id_index[id_normalized]

        # Remove from partial ID index
        for i in range(2, len(element_id) + 1):
            partial = element_id[:i].lower()
            self._partial_id_index[partial].discard(element_id)
            if not self._partial_id_index[partial]:
                del self._partial_id_index[partial]

        # Remove from title index
        title_words = self._normalize_for_search(element.title).split()
        for word in title_words:
            if word and word in self._title_index:
                self._title_index[word].discard(element_id)
                if not self._title_index[word]:
                    del self._title_index[word]

    def _normalize_for_search(self, text: str) -> str:
        """Normalize text for search index."""
        # Convert to lowercase and remove special characters except colons (for IDs)
        normalized = re.sub(r'[^\w\s:]', ' ', text.lower())
        # Collapse multiple whitespace
        normalized = ' '.join(normalized.split())
        return normalized

    def clear(self) -> None:
        """Clear all index data."""
        self._elements.clear()
        self._file_elements.clear()
        self._references.clear()
        self._backlinks.clear()
        self._title_index.clear()
        self._id_index.clear()
        self._partial_id_index.clear()
        self._last_updated = time.time()

    def get_element_count(self) -> int:
        """Get total number of indexed elements."""
        return len(self._elements)

    def get_reference_count(self) -> int:
        """Get total number of references in the graph."""
        return sum(len(refs) for refs in self._references.values())

    def export_reference_graph(self) -> Dict[str, any]:
        """
        Export reference graph in a serializable format.

        Returns:
            Dictionary with complete reference graph data.
        """
        return {
            'elements': {eid: {
                'id': element.id,
                'title': element.title,
                'kind': element.kind.value,
                'file': element.file.value
            } for eid, element in self._elements.items()},

            'references': {eid: list(refs) for eid, refs in self._references.items() if refs},
            'backlinks': {eid: list(backlinks) for eid, backlinks in self._backlinks.items() if backlinks},

            'statistics': self.get_statistics().to_dict() if hasattr(self.get_statistics(), 'to_dict') else {
                'total_elements': len(self._elements),
                'total_references': self.get_reference_count(),
                'last_updated': self._last_updated
            }
        }


def create_index() -> DocumentIndex:
    """
    Convenience function to create a new document index.

    Returns:
        New DocumentIndex instance.
    """
    return DocumentIndex()