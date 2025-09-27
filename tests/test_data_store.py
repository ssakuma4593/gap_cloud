#!/usr/bin/env python3
"""
Tests for In-Memory Data Store

This module contains comprehensive tests for the in-memory data storage functionality,
including unit tests for data operations and integration tests.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from scripts.data_store import InMemoryDataStore, ResearchGap, get_data_store, add_abstract, add_gap
from scripts.abstract_parser import AbstractRecord


class TestInMemoryDataStore(unittest.TestCase):
    """Test cases for InMemoryDataStore class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.store = InMemoryDataStore()
        
        # Sample abstract data
        self.sample_abstract1 = AbstractRecord(
            title="AI in Healthcare: Current Applications",
            authors=["Smith J", "Doe A"],
            year=2023,
            abstract_text="This paper reviews current applications of AI in healthcare...",
            journal="Medical AI Journal",
            doi="10.1000/ai2023",
            pmid="12345",
            pmcid="PMC12345"
        )
        
        self.sample_abstract2 = AbstractRecord(
            title="Machine Learning for Drug Discovery",
            authors=["Johnson B", "Williams C"],
            year=2022,
            abstract_text="ML approaches are transforming drug discovery processes...",
            journal="Drug Discovery Today",
            doi="10.1000/ml2022",
            pmid="67890",
            pmcid="PMC67890"
        )
        
        # Sample research gaps
        self.sample_gap1 = ResearchGap(
            gap_id="",
            abstract_id="abs_1",
            gap_text="Need for better AI interpretability in clinical settings",
            topic="AI interpretability",
            year=2023,
            keywords=["AI", "interpretability", "clinical", "transparency"],
            confidence=0.9
        )
        
        self.sample_gap2 = ResearchGap(
            gap_id="",
            abstract_id="abs_2",
            gap_text="Limited validation of ML models in drug trials",
            topic="ML validation",
            year=2022,
            keywords=["ML", "validation", "drug", "trials"],
            confidence=0.8
        )

    def test_add_and_get_abstract(self):
        """Test adding and retrieving abstracts"""
        # Add abstract
        abstract_id = self.store.add_abstract(self.sample_abstract1, "test_abs_1")
        self.assertEqual(abstract_id, "test_abs_1")
        
        # Retrieve abstract
        retrieved = self.store.get_abstract("test_abs_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, self.sample_abstract1.title)
        self.assertEqual(retrieved.year, self.sample_abstract1.year)
        
        # Test auto-generated ID
        auto_id = self.store.add_abstract(self.sample_abstract2)
        self.assertTrue(auto_id.startswith("abs_"))
        retrieved_auto = self.store.get_abstract(auto_id)
        self.assertIsNotNone(retrieved_auto)

    def test_add_and_get_gap(self):
        """Test adding and retrieving research gaps"""
        # Add gap
        gap_id = self.store.add_gap(self.sample_gap1, "test_gap_1")
        self.assertEqual(gap_id, "test_gap_1")
        self.assertEqual(self.sample_gap1.gap_id, "test_gap_1")
        
        # Retrieve gap
        retrieved = self.store.get_gap("test_gap_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.gap_text, self.sample_gap1.gap_text)
        self.assertEqual(retrieved.topic, self.sample_gap1.topic)
        
        # Test auto-generated ID
        auto_id = self.store.add_gap(self.sample_gap2)
        self.assertTrue(auto_id.startswith("gap_"))
        retrieved_auto = self.store.get_gap(auto_id)
        self.assertIsNotNone(retrieved_auto)

    def test_get_gaps_by_year(self):
        """Test retrieving gaps by year"""
        # Add gaps
        self.store.add_gap(self.sample_gap1, "gap_2023")
        self.store.add_gap(self.sample_gap2, "gap_2022")
        
        # Get gaps by year
        gaps_2023 = self.store.get_gaps_by_year(2023)
        gaps_2022 = self.store.get_gaps_by_year(2022)
        gaps_2021 = self.store.get_gaps_by_year(2021)
        
        self.assertEqual(len(gaps_2023), 1)
        self.assertEqual(len(gaps_2022), 1)
        self.assertEqual(len(gaps_2021), 0)
        
        self.assertEqual(gaps_2023[0].gap_text, self.sample_gap1.gap_text)
        self.assertEqual(gaps_2022[0].gap_text, self.sample_gap2.gap_text)

    def test_get_gaps_by_topic(self):
        """Test retrieving gaps by topic"""
        # Add gaps
        self.store.add_gap(self.sample_gap1, "gap_ai")
        self.store.add_gap(self.sample_gap2, "gap_ml")
        
        # Get gaps by topic
        ai_gaps = self.store.get_gaps_by_topic("AI interpretability")
        ml_gaps = self.store.get_gaps_by_topic("ML validation")
        other_gaps = self.store.get_gaps_by_topic("other topic")
        
        self.assertEqual(len(ai_gaps), 1)
        self.assertEqual(len(ml_gaps), 1)
        self.assertEqual(len(other_gaps), 0)

    def test_get_gaps_by_abstract(self):
        """Test retrieving gaps by abstract ID"""
        # Modify gaps to have same abstract ID
        gap1 = ResearchGap(
            gap_id="",
            abstract_id="same_abstract",
            gap_text="Gap 1",
            topic="topic1",
            year=2023,
            keywords=["key1"],
            confidence=0.9
        )
        
        gap2 = ResearchGap(
            gap_id="",
            abstract_id="same_abstract",
            gap_text="Gap 2",
            topic="topic2",
            year=2023,
            keywords=["key2"],
            confidence=0.8
        )
        
        # Add gaps
        self.store.add_gap(gap1)
        self.store.add_gap(gap2)
        
        # Get gaps by abstract
        gaps = self.store.get_gaps_by_abstract("same_abstract")
        self.assertEqual(len(gaps), 2)

    def test_keyword_frequency(self):
        """Test keyword frequency counting"""
        # Add gaps
        self.store.add_gap(self.sample_gap1)
        self.store.add_gap(self.sample_gap2)
        
        # Get overall keyword frequency
        freq = self.store.get_keyword_frequency()
        
        # Check some expected keywords
        self.assertIn("ai", freq)
        self.assertIn("ml", freq)
        self.assertIn("validation", freq)
        
        # Test filtered by year
        freq_2023 = self.store.get_keyword_frequency(year=2023)
        self.assertIn("ai", freq_2023)
        self.assertNotIn("ml", freq_2023)  # ML gap is from 2022

    def test_statistics(self):
        """Test statistics generation"""
        # Add data
        abs_id1 = self.store.add_abstract(self.sample_abstract1)
        abs_id2 = self.store.add_abstract(self.sample_abstract2)
        self.store.add_gap(self.sample_gap1)
        self.store.add_gap(self.sample_gap2)
        
        # Get statistics
        stats = self.store.get_statistics()
        
        self.assertEqual(stats['total_abstracts'], 2)
        self.assertEqual(stats['total_gaps'], 2)
        self.assertIn(2023, stats['years_covered'])
        self.assertIn(2022, stats['years_covered'])
        self.assertIn('AI interpretability', stats['topics_covered'])
        self.assertIn('ML validation', stats['topics_covered'])

    def test_clear(self):
        """Test clearing all data"""
        # Add data
        self.store.add_abstract(self.sample_abstract1)
        self.store.add_gap(self.sample_gap1)
        
        # Verify data exists
        stats = self.store.get_statistics()
        self.assertGreater(stats['total_abstracts'], 0)
        self.assertGreater(stats['total_gaps'], 0)
        
        # Clear and verify
        self.store.clear()
        stats_after = self.store.get_statistics()
        self.assertEqual(stats_after['total_abstracts'], 0)
        self.assertEqual(stats_after['total_gaps'], 0)

    def test_export_import_json(self):
        """Test JSON export and import"""
        # Add data
        abs_id = self.store.add_abstract(self.sample_abstract1, "test_abs")
        gap_id = self.store.add_gap(self.sample_gap1, "test_gap")
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            self.store.export_to_json(temp_path)
            
            # Verify file exists and has content
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn('abstracts', data)
            self.assertIn('gaps', data)
            self.assertIn('metadata', data)
            
            # Create new store and import
            new_store = InMemoryDataStore()
            new_store.import_from_json(temp_path)
            
            # Verify imported data
            imported_abstract = new_store.get_abstract("test_abs")
            imported_gap = new_store.get_gap("test_gap")
            
            self.assertIsNotNone(imported_abstract)
            self.assertIsNotNone(imported_gap)
            self.assertEqual(imported_abstract.title, self.sample_abstract1.title)
            self.assertEqual(imported_gap.gap_text, self.sample_gap1.gap_text)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_research_gap_serialization(self):
        """Test ResearchGap serialization and deserialization"""
        gap = ResearchGap(
            gap_id="test_gap",
            abstract_id="test_abs",
            gap_text="Test gap",
            topic="test topic",
            year=2023,
            keywords=["test", "gap"],
            confidence=0.95
        )
        
        # Test to_dict
        gap_dict = gap.to_dict()
        self.assertIsInstance(gap_dict, dict)
        self.assertEqual(gap_dict['gap_text'], "Test gap")
        self.assertIn('created_at', gap_dict)
        
        # Test from_dict
        reconstructed = ResearchGap.from_dict(gap_dict)
        self.assertEqual(reconstructed.gap_text, gap.gap_text)
        self.assertEqual(reconstructed.topic, gap.topic)
        self.assertEqual(reconstructed.confidence, gap.confidence)


class TestGlobalDataStore(unittest.TestCase):
    """Test global data store functions"""
    
    def setUp(self):
        """Clear global store before each test"""
        get_data_store().clear()
    
    def test_global_store_singleton(self):
        """Test that global store is a singleton"""
        store1 = get_data_store()
        store2 = get_data_store()
        self.assertIs(store1, store2)
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        # Create sample data
        abstract = AbstractRecord(
            title="Test Abstract",
            authors=["Test Author"],
            year=2023,
            abstract_text="Test content"
        )
        
        gap = ResearchGap(
            gap_id="",
            abstract_id="test_abs",
            gap_text="Test gap",
            topic="test",
            year=2023,
            keywords=["test"],
            confidence=0.8
        )
        
        # Test convenience functions
        abs_id = add_abstract(abstract, "test_abs")
        gap_id = add_gap(gap)
        
        self.assertEqual(abs_id, "test_abs")
        self.assertTrue(gap_id.startswith("gap_"))
        
        # Check statistics
        stats = get_statistics()
        self.assertEqual(stats['total_abstracts'], 1)
        self.assertEqual(stats['total_gaps'], 1)


def run_example_usage():
    """Demonstrate example usage of the data store"""
    print("=== Data Store Example Usage ===\n")
    
    # Create a new store instance for demo
    store = InMemoryDataStore()
    
    # Create sample abstract
    abstract = AbstractRecord(
        title="Artificial Intelligence in Medical Diagnosis",
        authors=["Dr. Smith", "Dr. Johnson"],
        year=2023,
        abstract_text="This study examines the use of AI in medical diagnosis...",
        journal="AI Medicine Journal",
        doi="10.1000/aimd2023"
    )
    
    # Add abstract
    abstract_id = store.add_abstract(abstract)
    print(f"✅ Added abstract: {abstract_id}")
    
    # Create research gaps
    gaps = [
        ResearchGap(
            gap_id="",
            abstract_id=abstract_id,
            gap_text="Limited validation of AI models in diverse patient populations",
            topic="AI validation",
            year=2023,
            keywords=["AI", "validation", "diversity", "patients"],
            confidence=0.9
        ),
        ResearchGap(
            gap_id="",
            abstract_id=abstract_id,
            gap_text="Lack of standardized evaluation metrics for AI diagnostic tools",
            topic="AI evaluation",
            year=2023,
            keywords=["AI", "evaluation", "metrics", "standardization"],
            confidence=0.85
        )
    ]
    
    # Add gaps
    for gap in gaps:
        gap_id = store.add_gap(gap)
        print(f"✅ Added gap: {gap_id} - '{gap.gap_text[:50]}...'")
    
    # Display statistics
    print("\n📊 Data Store Statistics:")
    stats = store.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show keyword analysis
    print("\n🔍 Keyword Analysis:")
    keywords = store.get_keyword_frequency()
    for keyword, count in keywords.most_common(5):
        print(f"  '{keyword}': {count}")
    
    print(f"\n📅 Years with data: {store.get_years_with_gaps()}")
    print(f"📚 Topics with data: {store.get_topics_with_gaps()}")


if __name__ == "__main__":
    # Run example usage
    print("Running example usage...\n")
    run_example_usage()
    
    print("\n" + "="*60)
    print("Running unit tests...\n")
    
    # Run tests
    unittest.main(argv=[''], exit=False, verbosity=2)
