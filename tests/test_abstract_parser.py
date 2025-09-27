#!/usr/bin/env python3
"""
Tests for Abstract Parser

This module contains comprehensive tests for the abstract parsing functionality,
including unit tests for individual components and integration tests with sample data.
"""

import unittest
from unittest.mock import patch
import json
from scripts.abstract_parser import AbstractParser, AbstractRecord, parse_abstract_text, parse_multiple_abstracts


class TestAbstractParser(unittest.TestCase):
    """Test cases for AbstractParser class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = AbstractParser()
        
        # Sample abstract text from the context
        self.sample_abstract1 = """1. Future Healthc J. 2019 Jun;6(2):94-98. doi: 10.7861/futurehosp.6-2-94.

The potential for artificial intelligence in healthcare.

Davenport T(1), Kalakota R(2).

Author information:
(1)Babson College, Wellesley, USA.
(2)Deloitte Consulting, New York, USA.

The complexity and rise of data in healthcare means that artificial intelligence 
(AI) will increasingly be applied within the field. Several types of AI are 
already being employed by payers and providers of care, and life sciences 
companies. The key categories of applications involve diagnosis and treatment 
recommendations, patient engagement and adherence, and administrative 
activities. Although there are many instances in which AI can perform healthcare 
tasks as well or better than humans, implementation factors will prevent 
large-scale automation of healthcare professional jobs for a considerable 
period. Ethical issues in the application of AI to healthcare are also 
discussed.

DOI: 10.7861/futurehosp.6-2-94
PMCID: PMC6616181
PMID: 31363513"""

        # Second sample abstract
        self.sample_abstract2 = """2. Clin Microbiol Infect. 2020 May;26(5):584-595. doi: 10.1016/j.cmi.2019.09.009. 
Epub 2019 Sep 17.

Machine learning for clinical decision support in infectious diseases: a 
narrative review of current applications.

Peiffer-Smadja N(1), Rawson TM(2), Ahmad R(2), Buchard A(3), Georgiou P(4), 
Lescure FX(5), Birgand G(2), Holmes AH(2).

Author information:
(1)National Institute for Health Research Health Protection Research Unit in 
Healthcare Associated Infections and Antimicrobial Resistance, Imperial College 
London, London, UK; French Institute for Medical Research (Inserm), Infection 
Antimicrobials Modelling Evolution (IAME), UMR 1137, University Paris Diderot, 
Paris, France. Electronic address: n.peiffer-smadja@ic.ac.uk.
(2)National Institute for Health Research Health Protection Research Unit in 
Healthcare Associated Infections and Antimicrobial Resistance, Imperial College 
London, London, UK.

BACKGROUND: Machine learning (ML) is a growing field in medicine. This narrative 
review describes the current body of literature on ML for clinical decision 
support in infectious diseases (ID).
OBJECTIVES: We aim to inform clinicians about the use of ML for diagnosis, 
classification, outcome prediction and antimicrobial management in ID.
SOURCES: References for this review were identified through searches of 
MEDLINE/PubMed, EMBASE, Google Scholar, biorXiv, ACM Digital Library, arXiV and 
IEEE Xplore Digital Library up to July 2019.
CONTENT: We found 60 unique ML-clinical decision support systems (ML-CDSS) 
aiming to assist ID clinicians.

DOI: 10.1016/j.cmi.2019.09.009
PMID: 31539636"""

        # Combined abstracts for multiple parsing test
        self.multiple_abstracts = self.sample_abstract1 + "\n\n\n" + self.sample_abstract2

    def test_extract_year(self):
        """Test year extraction"""
        # Test with journal line
        text1 = "Future Healthc J. 2019 Jun;6(2):94-98"
        year1 = self.parser.extract_year(text1)
        self.assertEqual(year1, 2019)
        
        # Test with different format
        text2 = "Published in 2020"
        year2 = self.parser.extract_year(text2)
        self.assertEqual(year2, 2020)
        
        # Test with no year
        text3 = "No year here"
        year3 = self.parser.extract_year(text3)
        self.assertIsNone(year3)

    def test_extract_journal_info(self):
        """Test journal information extraction"""
        journal, year, doi = self.parser.extract_journal_info(self.sample_abstract1)
        
        self.assertEqual(journal, "Future Healthc J")
        self.assertEqual(year, 2019)
        self.assertEqual(doi, "10.7861/futurehosp.6-2-94")

    def test_extract_title(self):
        """Test title extraction"""
        title = self.parser.extract_title(self.sample_abstract1)
        self.assertEqual(title, "The potential for artificial intelligence in healthcare.")
        
        title2 = self.parser.extract_title(self.sample_abstract2)
        self.assertEqual(title2, "Machine learning for clinical decision support in infectious diseases: a narrative review of current applications.")

    def test_extract_authors(self):
        """Test author extraction"""
        authors = self.parser.extract_authors(self.sample_abstract1)
        expected_authors = ["Davenport T", "Kalakota R"]
        self.assertEqual(authors, expected_authors)
        
        # Test with more complex author list
        authors2 = self.parser.extract_authors(self.sample_abstract2)
        expected_authors2 = ["Peiffer-Smadja N", "Rawson TM", "Ahmad R", "Buchard A", "Georgiou P", "Lescure FX", "Birgand G", "Holmes AH"]
        self.assertEqual(authors2, expected_authors2)

    def test_extract_abstract_text(self):
        """Test abstract text extraction"""
        abstract_text = self.parser.extract_abstract_text(self.sample_abstract1)
        
        # Check that it starts with expected content
        self.assertTrue(abstract_text.startswith("The complexity and rise of data"))
        self.assertTrue("artificial intelligence" in abstract_text)
        self.assertTrue("healthcare" in abstract_text)
        
        # Check that it doesn't include DOI/PMID info
        self.assertNotIn("DOI:", abstract_text)
        self.assertNotIn("PMID:", abstract_text)

    def test_extract_identifiers(self):
        """Test DOI, PMID, PMCID extraction"""
        doi, pmid, pmcid = self.parser.extract_identifiers(self.sample_abstract1)
        
        self.assertEqual(doi, "10.7861/futurehosp.6-2-94")
        self.assertEqual(pmid, "31363513")
        self.assertEqual(pmcid, "PMC6616181")

    def test_parse_single_abstract(self):
        """Test parsing a single complete abstract"""
        records = self.parser.parse_abstract(self.sample_abstract1)
        
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 1)
        
        record = records[0]
        self.assertIsInstance(record, AbstractRecord)
        
        # Check all fields
        self.assertEqual(record.title, "The potential for artificial intelligence in healthcare.")
        self.assertEqual(record.authors, ["Davenport T", "Kalakota R"])
        self.assertEqual(record.year, 2019)
        self.assertEqual(record.journal, "Future Healthc J")
        self.assertEqual(record.doi, "10.7861/futurehosp.6-2-94")
        self.assertEqual(record.pmid, "31363513")
        self.assertEqual(record.pmcid, "PMC6616181")
        self.assertTrue(record.abstract_text.startswith("The complexity and rise of data"))

    def test_parse_second_abstract(self):
        """Test parsing the second sample abstract"""
        records = self.parser.parse_abstract(self.sample_abstract2)
        
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 1)
        
        record = records[0]
        self.assertEqual(record.title, "Machine learning for clinical decision support in infectious diseases: a narrative review of current applications.")
        self.assertEqual(len(record.authors), 8)  # Should have 8 authors
        self.assertEqual(record.year, 2020)
        self.assertEqual(record.journal, "Clin Microbiol Infect")

    def test_parse_multiple_abstracts(self):
        """Test parsing multiple abstracts from one text block"""
        records = self.parser.parse_multiple_abstracts(self.multiple_abstracts)
        
        self.assertEqual(len(records), 2)
        
        # Check first record
        self.assertEqual(records[0].title, "The potential for artificial intelligence in healthcare.")
        self.assertEqual(records[0].year, 2019)
        
        # Check second record
        self.assertEqual(records[1].title, "Machine learning for clinical decision support in infectious diseases: a narrative review of current applications.")
        self.assertEqual(records[1].year, 2020)

    def test_abstract_record_serialization(self):
        """Test AbstractRecord serialization methods"""
        records = self.parser.parse_abstract(self.sample_abstract1)
        self.assertEqual(len(records), 1)
        record = records[0]
        
        # Test to_dict
        record_dict = record.to_dict()
        self.assertIsInstance(record_dict, dict)
        self.assertEqual(record_dict['title'], record.title)
        self.assertEqual(record_dict['authors'], record.authors)
        
        # Test to_json
        record_json = record.to_json()
        self.assertIsInstance(record_json, str)
        
        # Verify JSON can be parsed back
        parsed_json = json.loads(record_json)
        self.assertEqual(parsed_json['title'], record.title)

    def test_convenience_functions(self):
        """Test convenience functions"""
        # Test single abstract parsing
        records = parse_abstract_text(self.sample_abstract1)
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].title, "The potential for artificial intelligence in healthcare.")
        
        # Test multiple abstracts parsing
        multiple_records = parse_multiple_abstracts(self.multiple_abstracts)
        self.assertEqual(len(multiple_records), 2)

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test empty text
        records = self.parser.parse_abstract("")
        self.assertEqual(records, [])
        
        # Test whitespace-only text
        records = self.parser.parse_abstract("   \n  \t  ")
        self.assertEqual(records, [])
        
        # Test malformed abstract (missing title)
        malformed = """1. Journal. 2020.
        
        Author A(1).
        
        Some abstract text here.
        
        DOI: 10.1234/test"""
        records = self.parser.parse_abstract(malformed)
        # Should return empty list if parsing fails
        self.assertIsInstance(records, list)
        
    def test_include_raw_text(self):
        """Test including raw text in parsed record"""
        records = self.parser.parse_abstract(self.sample_abstract1, include_raw=True)
        self.assertEqual(len(records), 1)
        record = records[0]
        
        self.assertIsNotNone(record.raw_text)
        self.assertEqual(record.raw_text, self.sample_abstract1)
        
        # Test without raw text
        records_no_raw = self.parser.parse_abstract(self.sample_abstract1, include_raw=False)
        self.assertEqual(len(records_no_raw), 1)
        self.assertIsNone(records_no_raw[0].raw_text)

    def test_different_separators(self):
        """Test parsing with different separators"""
        # Test with triple newline separator (proper separator between abstracts)
        triple_newline_text = self.sample_abstract1 + "\n\n\n" + self.sample_abstract2
        records = self.parser.parse_multiple_abstracts(triple_newline_text, separator="\n\n\n")
        self.assertEqual(len(records), 2)

    def test_author_name_cleaning(self):
        """Test that author names are properly cleaned"""
        # Test with complex author line
        complex_author_text = """Test Journal. 2020.

Test title.

Smith JA(1), Brown-Wilson M(2), O'Connor P(3), van der Berg H(4).

Author information:
(1)University A.

Abstract text here.

DOI: 10.1234/test"""
        
        records = self.parser.parse_abstract(complex_author_text)
        if records and len(records) > 0:
            expected_authors = ["Smith JA", "Brown-Wilson M", "O'Connor P", "van der Berg H"]
            self.assertEqual(records[0].authors, expected_authors)


class TestAbstractParserIntegration(unittest.TestCase):
    """Integration tests for the complete parsing workflow"""
    
    def test_end_to_end_workflow(self):
        """Test the complete workflow from raw text to structured data"""
        # Sample text with multiple abstracts
        sample_text = """1. Future Healthc J. 2019 Jun;6(2):94-98. doi: 10.7861/futurehosp.6-2-94.

The potential for artificial intelligence in healthcare.

Davenport T(1), Kalakota R(2).

Author information:
(1)Babson College, Wellesley, USA.
(2)Deloitte Consulting, New York, USA.

The complexity and rise of data in healthcare means that artificial intelligence 
(AI) will increasingly be applied within the field. Several types of AI are 
already being employed by payers and providers of care, and life sciences 
companies.

DOI: 10.7861/futurehosp.6-2-94
PMCID: PMC6616181
PMID: 31363513


3. Test J. 2021;15(3):123-130. doi: 10.1234/test.2021.

A test article for parsing validation.

Test A(1), Example B(2).

Author information:
(1)Test University.
(2)Example Institute.

This is a test abstract to validate the parsing functionality. It contains 
multiple sentences and should be extracted correctly.

DOI: 10.1234/test.2021
PMID: 12345678"""

        # Parse multiple abstracts
        parser = AbstractParser()
        records = parser.parse_multiple_abstracts(sample_text)
        
        # Should have 2 valid records
        self.assertEqual(len(records), 2)
        
        # Validate first record
        first_record = records[0]
        self.assertEqual(first_record.title, "The potential for artificial intelligence in healthcare.")
        self.assertEqual(first_record.year, 2019)
        self.assertEqual(len(first_record.authors), 2)
        
        # Validate second record
        second_record = records[1]
        self.assertEqual(second_record.title, "A test article for parsing validation.")
        self.assertEqual(second_record.year, 2021)
        self.assertEqual(len(second_record.authors), 2)
        
        # Test JSON serialization of results
        for record in records:
            json_str = record.to_json()
            self.assertIsInstance(json_str, str)
            # Verify it's valid JSON
            parsed = json.loads(json_str)
            self.assertIn('title', parsed)
            self.assertIn('authors', parsed)
            self.assertIn('year', parsed)


def run_example_usage():
    """Demonstrate example usage of the parser"""
    print("=== Abstract Parser Example Usage ===\n")
    
    # Sample abstract text
    sample_text = """1. Future Healthc J. 2019 Jun;6(2):94-98. doi: 10.7861/futurehosp.6-2-94.

The potential for artificial intelligence in healthcare.

Davenport T(1), Kalakota R(2).

Author information:
(1)Babson College, Wellesley, USA.
(2)Deloitte Consulting, New York, USA.

The complexity and rise of data in healthcare means that artificial intelligence 
(AI) will increasingly be applied within the field. Several types of AI are 
already being employed by payers and providers of care, and life sciences 
companies. The key categories of applications involve diagnosis and treatment 
recommendations, patient engagement and adherence, and administrative 
activities. Although there are many instances in which AI can perform healthcare 
tasks as well or better than humans, implementation factors will prevent 
large-scale automation of healthcare professional jobs for a considerable 
period. Ethical issues in the application of AI to healthcare are also 
discussed.

DOI: 10.7861/futurehosp.6-2-94
PMCID: PMC6616181
PMID: 31363513"""

    # Parse using convenience function
    records = parse_abstract_text(sample_text)
    
    if records:
        record = records[0]  # Get first (and only) record
        print("✅ Successfully parsed abstract!")
        print(f"📄 Title: {record.title}")
        print(f"👥 Authors: {', '.join(record.authors)}")
        print(f"📅 Year: {record.year}")
        print(f"📰 Journal: {record.journal}")
        print(f"🔗 DOI: {record.doi}")
        print(f"🆔 PMID: {record.pmid}")
        print(f"🆔 PMCID: {record.pmcid}")
        print(f"📝 Abstract preview: {record.abstract_text[:150]}...")
        print("\n" + "="*60)
        print("JSON representation:")
        print(record.to_json())
    else:
        print("❌ Failed to parse abstract")


if __name__ == "__main__":
    # Run example usage
    print("Running example usage...\n")
    run_example_usage()
    
    print("\n" + "="*60)
    print("Running unit tests...\n")
    
    # Run tests
    unittest.main(argv=[''], exit=False, verbosity=2)
