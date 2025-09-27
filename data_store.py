#!/usr/bin/env python3
"""
In-Memory Data Store for Medical Research Gap Analysis Tool

This module provides functionality to store and retrieve parsed abstracts and
extracted research gaps in memory using Python data structures. Designed for
small to medium datasets that can fit comfortably in RAM.

Features:
- Fast in-memory storage and retrieval
- Data export/import capabilities for persistence
- Query methods for analysis and visualization
- Thread-safe operations for concurrent access
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
from collections import defaultdict, Counter
from abstract_parser import AbstractRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResearchGap:
    """
    Represents an extracted research gap from a medical abstract.
    
    Attributes:
        gap_id: Unique identifier for the gap
        abstract_id: ID of the source abstract
        gap_text: Description of the research gap
        topic: Research topic/area
        year: Publication year
        keywords: Relevant keywords extracted from the gap
        confidence: Confidence score of the extraction (0.0-1.0)
        created_at: Timestamp when gap was extracted
    """
    gap_id: str
    abstract_id: str
    gap_text: str
    topic: Optional[str] = None
    year: Optional[int] = None
    keywords: List[str] = None
    confidence: float = 0.0
    created_at: datetime = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'ResearchGap':
        """Create from dictionary format."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class InMemoryDataStore:
    """
    Thread-safe in-memory data store for abstracts and research gaps.
    """
    
    def __init__(self):
        """Initialize the data store."""
        self._abstracts: Dict[str, AbstractRecord] = {}
        self._gaps: Dict[str, ResearchGap] = {}
        self._lock = threading.RLock()
        self._next_gap_id = 1
        
        # Indexes for fast queries
        self._gaps_by_year: Dict[int, Set[str]] = defaultdict(set)
        self._gaps_by_topic: Dict[str, Set[str]] = defaultdict(set)
        self._gaps_by_abstract: Dict[str, Set[str]] = defaultdict(set)
        
        logger.info("Initialized in-memory data store")

    def add_abstract(self, abstract: AbstractRecord, abstract_id: Optional[str] = None) -> str:
        """
        Add an abstract to the store.
        
        Args:
            abstract: Parsed abstract record
            abstract_id: Optional custom ID, auto-generated if not provided
            
        Returns:
            str: The abstract ID
        """
        with self._lock:
            if abstract_id is None:
                # Generate ID from title hash or use timestamp
                import hashlib
                title_hash = hashlib.md5(abstract.title.encode()).hexdigest()[:8]
                abstract_id = f"abs_{title_hash}"
            
            self._abstracts[abstract_id] = abstract
            logger.info(f"Added abstract: {abstract_id} - '{abstract.title[:50]}...'")
            return abstract_id

    def add_gap(self, gap: ResearchGap, gap_id: Optional[str] = None) -> str:
        """
        Add a research gap to the store.
        
        Args:
            gap: Research gap data
            gap_id: Optional custom ID, auto-generated if not provided
            
        Returns:
            str: The gap ID
        """
        with self._lock:
            if gap_id is None:
                gap_id = f"gap_{self._next_gap_id:06d}"
                self._next_gap_id += 1
            
            gap.gap_id = gap_id
            self._gaps[gap_id] = gap
            
            # Update indexes
            if gap.year:
                self._gaps_by_year[gap.year].add(gap_id)
            if gap.topic:
                self._gaps_by_topic[gap.topic].add(gap_id)
            if gap.abstract_id:
                self._gaps_by_abstract[gap.abstract_id].add(gap_id)
            
            logger.info(f"Added research gap: {gap_id}")
            return gap_id

    def get_abstract(self, abstract_id: str) -> Optional[AbstractRecord]:
        """Get an abstract by ID."""
        with self._lock:
            return self._abstracts.get(abstract_id)

    def get_gap(self, gap_id: str) -> Optional[ResearchGap]:
        """Get a research gap by ID."""
        with self._lock:
            return self._gaps.get(gap_id)

    def get_all_abstracts(self) -> Dict[str, AbstractRecord]:
        """Get all abstracts."""
        with self._lock:
            return dict(self._abstracts)

    def get_all_gaps(self) -> Dict[str, ResearchGap]:
        """Get all research gaps."""
        with self._lock:
            return dict(self._gaps)

    def get_gaps_by_year(self, year: int) -> List[ResearchGap]:
        """Get all gaps for a specific year."""
        with self._lock:
            gap_ids = self._gaps_by_year.get(year, set())
            return [self._gaps[gap_id] for gap_id in gap_ids if gap_id in self._gaps]

    def get_gaps_by_topic(self, topic: str) -> List[ResearchGap]:
        """Get all gaps for a specific topic."""
        with self._lock:
            gap_ids = self._gaps_by_topic.get(topic, set())
            return [self._gaps[gap_id] for gap_id in gap_ids if gap_id in self._gaps]

    def get_gaps_by_abstract(self, abstract_id: str) -> List[ResearchGap]:
        """Get all gaps extracted from a specific abstract."""
        with self._lock:
            gap_ids = self._gaps_by_abstract.get(abstract_id, set())
            return [self._gaps[gap_id] for gap_id in gap_ids if gap_id in self._gaps]

    def get_years_with_gaps(self) -> List[int]:
        """Get all years that have research gaps."""
        with self._lock:
            return sorted([year for year, gaps in self._gaps_by_year.items() if gaps])

    def get_topics_with_gaps(self) -> List[str]:
        """Get all topics that have research gaps."""
        with self._lock:
            return sorted([topic for topic, gaps in self._gaps_by_topic.items() if gaps])

    def get_keyword_frequency(self, year: Optional[int] = None, topic: Optional[str] = None) -> Counter:
        """
        Get keyword frequency counts, optionally filtered by year or topic.
        
        Args:
            year: Optional year filter
            topic: Optional topic filter
            
        Returns:
            Counter: Keywords and their frequencies
        """
        with self._lock:
            gaps_to_analyze = []
            
            if year and topic:
                # Get intersection of gaps by year and topic
                year_gaps = self._gaps_by_year.get(year, set())
                topic_gaps = self._gaps_by_topic.get(topic, set())
                gap_ids = year_gaps.intersection(topic_gaps)
                gaps_to_analyze = [self._gaps[gap_id] for gap_id in gap_ids if gap_id in self._gaps]
            elif year:
                gaps_to_analyze = self.get_gaps_by_year(year)
            elif topic:
                gaps_to_analyze = self.get_gaps_by_topic(topic)
            else:
                gaps_to_analyze = list(self._gaps.values())
            
            # Count keywords
            keyword_counts = Counter()
            for gap in gaps_to_analyze:
                for keyword in gap.keywords:
                    keyword_counts[keyword.lower()] += 1
            
            return keyword_counts

    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics about the data store."""
        with self._lock:
            stats = {
                'total_abstracts': len(self._abstracts),
                'total_gaps': len(self._gaps),
                'years_covered': list(self._gaps_by_year.keys()),
                'topics_covered': list(self._gaps_by_topic.keys()),
                'gaps_per_year': {year: len(gaps) for year, gaps in self._gaps_by_year.items()},
                'gaps_per_topic': {topic: len(gaps) for topic, gaps in self._gaps_by_topic.items()},
                'average_gaps_per_abstract': len(self._gaps) / max(len(self._abstracts), 1)
            }
            return stats

    def clear(self):
        """Clear all data from the store."""
        with self._lock:
            self._abstracts.clear()
            self._gaps.clear()
            self._gaps_by_year.clear()
            self._gaps_by_topic.clear()
            self._gaps_by_abstract.clear()
            self._next_gap_id = 1
            logger.info("Cleared all data from store")

    def export_to_json(self, filepath: str):
        """
        Export all data to a JSON file for persistence.
        
        Args:
            filepath: Path to save the JSON file
        """
        with self._lock:
            data = {
                'abstracts': {aid: abstract.to_dict() for aid, abstract in self._abstracts.items()},
                'gaps': {gid: gap.to_dict() for gid, gap in self._gaps.items()},
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'next_gap_id': self._next_gap_id
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported data to {filepath}")

    def import_from_json(self, filepath: str):
        """
        Import data from a JSON file.
        
        Args:
            filepath: Path to the JSON file to import
        """
        with self._lock:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing data
            self.clear()
            
            # Import abstracts
            abstracts_data = data.get('abstracts', {})
            for abstract_id, abstract_dict in abstracts_data.items():
                # Reconstruct AbstractRecord
                abstract = AbstractRecord(**abstract_dict)
                self._abstracts[abstract_id] = abstract
            
            # Import gaps
            gaps_data = data.get('gaps', {})
            for gap_id, gap_dict in gaps_data.items():
                gap = ResearchGap.from_dict(gap_dict)
                self._gaps[gap_id] = gap
                
                # Rebuild indexes
                if gap.year:
                    self._gaps_by_year[gap.year].add(gap_id)
                if gap.topic:
                    self._gaps_by_topic[gap.topic].add(gap_id)
                if gap.abstract_id:
                    self._gaps_by_abstract[gap.abstract_id].add(gap_id)
            
            # Import metadata
            metadata = data.get('metadata', {})
            self._next_gap_id = metadata.get('next_gap_id', 1)
            
            logger.info(f"Imported data from {filepath}: "
                       f"{len(self._abstracts)} abstracts, {len(self._gaps)} gaps")


# Global data store instance
_global_store = None
_store_lock = threading.Lock()


def get_data_store() -> InMemoryDataStore:
    """Get the global data store instance (singleton pattern)."""
    global _global_store
    if _global_store is None:
        with _store_lock:
            if _global_store is None:
                _global_store = InMemoryDataStore()
    return _global_store


# Convenience functions
def add_abstract(abstract: AbstractRecord, abstract_id: Optional[str] = None) -> str:
    """Add an abstract to the global data store."""
    return get_data_store().add_abstract(abstract, abstract_id)


def add_gap(gap: ResearchGap, gap_id: Optional[str] = None) -> str:
    """Add a research gap to the global data store."""
    return get_data_store().add_gap(gap, gap_id)


def get_statistics() -> Dict[str, Any]:
    """Get statistics from the global data store."""
    return get_data_store().get_statistics()


def export_data(filepath: str):
    """Export data from the global data store."""
    get_data_store().export_to_json(filepath)


def import_data(filepath: str):
    """Import data to the global data store."""
    get_data_store().import_from_json(filepath)


if __name__ == "__main__":
    # Example usage
    print("=== In-Memory Data Store Example ===\n")
    
    # Create sample data
    from abstract_parser import AbstractRecord
    
    # Sample abstract
    sample_abstract = AbstractRecord(
        title="Sample Medical Research Paper",
        authors=["Smith J", "Doe A"],
        year=2023,
        abstract_text="This is a sample abstract about medical research with some gaps.",
        journal="Sample Journal",
        doi="10.1000/sample",
        pmid="12345",
        pmcid="PMC12345"
    )
    
    # Add to store
    store = get_data_store()
    abstract_id = store.add_abstract(sample_abstract)
    
    # Create sample research gap
    gap = ResearchGap(
        gap_id="",  # Will be auto-generated
        abstract_id=abstract_id,
        gap_text="Limited understanding of treatment effectiveness in elderly patients",
        topic="geriatric medicine",
        year=2023,
        keywords=["treatment", "effectiveness", "elderly", "patients"],
        confidence=0.85
    )
    
    gap_id = store.add_gap(gap)
    
    # Display statistics
    stats = store.get_statistics()
    print("Data Store Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nSample gap: {gap.gap_text}")
    print(f"Keywords: {gap.keywords}")
    
    # Export example
    export_path = "/tmp/sample_data.json"
    try:
        store.export_to_json(export_path)
        print(f"\nData exported to: {export_path}")
    except Exception as e:
        print(f"Export failed: {e}")
