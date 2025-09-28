#!/usr/bin/env python3
"""
Abstract Parser for Medical Research Gap Analysis Tool

This module provides functionality to parse raw medical research abstract text
into structured records with fields: title, authors, year, abstract text.

Input Format Assumptions:
1. Abstracts follow PubMed format with journal citation first
2. Title appears after DOI/journal info and before authors
3. Authors are listed with numbered affiliations in parentheses
4. Year appears in the journal citation line
5. Abstract text follows author information section
6. Sections are separated by blank lines or specific delimiters
7. DOI and PMID appear at the end

Example Input Format:
```
1. Future Healthc J. 2019 Jun;6(2):94-98. doi: 10.7861/futurehosp.6-2-94.

The potential for artificial intelligence in healthcare.

Davenport T(1), Kalakota R(2).

Author information:
(1)Babson College, Wellesley, USA.
(2)Deloitte Consulting, New York, USA.

The complexity and rise of data in healthcare means that artificial intelligence 
(AI) will increasingly be applied within the field...

DOI: 10.7861/futurehosp.6-2-94
PMCID: PMC6616181
PMID: 31363513
```
"""

import re
import logging
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AbstractRecord:
    """
    Structured representation of a medical research abstract.
    
    Attributes:
        title: Title of the research paper
        authors: List of author names
        year: Publication year
        abstract_text: Main abstract content
        journal: Journal name (optional)
        doi: Digital Object Identifier (optional)
        pmid: PubMed ID (optional)
        pmcid: PubMed Central ID (optional)
        raw_text: Original raw text (optional, for debugging)
    """
    title: str
    authors: List[str]
    year: Optional[int]
    abstract_text: str
    journal: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    raw_text: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert record to dictionary format."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert record to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AbstractParser:
    """
    Parser for medical research abstracts in PubMed format.
    """
    
    def __init__(self):
        """Initialize the parser with regex patterns."""
        # Pattern to match journal citation with year
        self.journal_pattern = re.compile(
            r'^\d+\.\s*(.+?)\.\s*(\d{4})\s*.*?(?:doi:|DOI:)?\s*([\d\./\-\w]+)?',
            re.MULTILINE
        )
        
        # Pattern to match title (usually follows journal info and precedes authors)
        self.title_pattern = re.compile(
            r'^([A-Z].*?[.!?])$',
            re.MULTILINE
        )
        
        # Pattern to match authors with affiliations
        self.authors_pattern = re.compile(
            r'^([A-Za-z\s,\-\']+(?:\(\d+\)(?:,\s*)?)*)\.$',
            re.MULTILINE
        )
        
        # Pattern to extract individual author names
        self.author_extract_pattern = re.compile(
            r'([A-Za-z\-\']+\s+[A-Z]+(?:\([^)]+\))?)'
        )
        
        # Pattern to match DOI
        self.doi_pattern = re.compile(
            r'DOI:\s*([\d\./\-\w]+)',
            re.IGNORECASE
        )
        
        # Pattern to match PMID
        self.pmid_pattern = re.compile(
            r'PMID:\s*(\d+)',
            re.IGNORECASE
        )
        
        # Pattern to match PMCID
        self.pmcid_pattern = re.compile(
            r'PMCID:\s*(PMC\d+)',
            re.IGNORECASE
        )
        
        # Pattern to match year
        self.year_pattern = re.compile(r'\b(19|20)\d{2}\b')

    def extract_year(self, text: str) -> Optional[int]:
        """
        Extract publication year from text.
        
        Args:
            text: Text to search for year
            
        Returns:
            Optional[int]: Publication year or None if not found
        """
        # Use a pattern to match full 4-digit years
        year_matches = re.findall(r'\b((?:19|20)\d{2})\b', text)
        if year_matches:
            # Return the first valid year found
            for match in year_matches:
                year = int(match)
                if 1900 <= year <= 2030:  # Reasonable range for publication years
                    return year
        return None

    def extract_journal_info(self, text: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Extract journal name, year, and DOI from journal citation line.
        
        Args:
            text: Raw abstract text
            
        Returns:
            Tuple[Optional[str], Optional[int], Optional[str]]: (journal, year, doi)
        """
        lines = text.strip().split('\n')
        first_line = lines[0] if lines else ""
        
        # Extract journal name (everything before year)
        journal_match = re.search(r'^\d+\.\s*(.+?)\.\s*(\d{4})', first_line)
        if journal_match:
            journal = journal_match.group(1).strip()
            year = int(journal_match.group(2))
            
            # Look for DOI in the same line
            doi_match = re.search(r'doi:\s*([\d\./\-\w]+)', first_line, re.IGNORECASE)
            doi = doi_match.group(1).rstrip('.') if doi_match else None
            
            return journal, year, doi
        
        return None, self.extract_year(first_line), None

    def extract_title(self, text: str) -> Optional[str]:
        """
        Extract title from abstract text.
        
        Args:
            text: Raw abstract text
            
        Returns:
            Optional[str]: Title or None if not found
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Skip the first lines (journal citation and any epub info) and look for the title
        title_lines = []
        start_collecting = False
        
        for i, line in enumerate(lines):
            # Skip journal citation line and epub/publication info
            if (i == 0 or 
                line.startswith(('Epub', 'doi:', 'DOI:')) or
                re.match(r'^\d+\.\s+.*\d{4}', line)):
                continue
                
            # Start collecting when we find a substantial line that's not author info
            if (line and 
                not re.search(r'[A-Za-z]+\s+[A-Z]+\(\d+\)', line) and  # Not author line
                not line.startswith(('Author information:', 'DOI:', 'PMID:', 'PMCID:')) and
                len(line) > 5):  # Reasonable minimum length
                
                start_collecting = True
                title_lines.append(line)
                
                # Check if we've reached the end of title
                # Look ahead to see if next non-empty line contains author info
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].strip():
                        if re.search(r'[A-Za-z]+\s+[A-Z]+\(\d+\)', lines[j]):
                            # Found author info, title ends here
                            if title_lines:
                                return ' '.join(title_lines)
                        break
                        
            elif start_collecting and re.search(r'[A-Za-z]+\s+[A-Z]+\(\d+\)', line):
                # Hit author info, stop collecting
                break
            elif start_collecting and line.startswith('Author information:'):
                # Hit author information section, stop collecting
                break
        
        if title_lines:
            return ' '.join(title_lines)
        
        return None

    def extract_authors(self, text: str) -> List[str]:
        """
        Extract author names from abstract text.
        
        Args:
            text: Raw abstract text
            
        Returns:
            List[str]: List of author names
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        authors = []
        author_lines = []
        
        # Find all author lines (may span multiple lines)
        for i, line in enumerate(lines):
            # Look for author line (contains names with affiliation numbers)
            if re.search(r'[A-Za-z]+\s+[A-Z]+\(\d+\)', line) and not line.startswith('Author information:'):
                author_lines.append(line)
                
                # Check if the next line also contains authors (continues the author list)
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # If next line also has author pattern or ends author list, include it
                    if (re.search(r'[A-Za-z]+\s+[A-Z]+\(\d+\)', next_line) and 
                        not next_line.startswith('Author information:')):
                        continue  # Will be picked up in next iteration
                    elif next_line.endswith('.') and not next_line.startswith('Author information:'):
                        # This might be the continuation/end of author list
                        if any(name_part in next_line for name_part in [',', 'FX', 'AH', 'TM']):
                            author_lines.append(next_line)
                
                break  # Found the author section, process it
        
        if author_lines:
            # Combine all author lines and extract names
            combined_authors = ' '.join(author_lines)
            # Remove affiliations and split by comma
            author_line = re.sub(r'\(\d+\)', '', combined_authors).rstrip('.')
            author_names = [name.strip() for name in author_line.split(',') if name.strip()]
            
            # Clean up author names and validate
            for name in author_names:
                name = name.strip()
                # Check if it looks like a proper name (at least first and last name)
                if len(name.split()) >= 2 and not any(char.isdigit() for char in name):
                    authors.append(name)
        
        return authors

    def extract_abstract_text(self, text: str) -> str:
        """
        Extract the main abstract content from the text.
        
        Args:
            text: Raw abstract text
            
        Returns:
            str: Abstract content
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Find the start of abstract content
        abstract_start = -1
        for i, line in enumerate(lines):
            # Abstract typically starts after author information
            if (line.startswith('Author information:') or 
                (re.search(r'[A-Za-z]+\s+[A-Z]+\(\d+\)', line) and not line.startswith('Author information:'))):
                # Look for the next substantial paragraph
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    if (len(next_line) > 50 and  # Substantial content
                        not next_line.startswith(('DOI:', 'PMID:', 'PMCID:', 'Author information:', '(')) and
                        not re.match(r'^\([^)]*\)', next_line)):  # Not affiliation info
                        abstract_start = j
                        break
                break
        
        if abstract_start == -1:
            # If no clear structure found, try to find first substantial paragraph
            for i, line in enumerate(lines[2:], 2):  # Skip first two lines
                if (len(line) > 50 and
                    not line.startswith(('DOI:', 'PMID:', 'PMCID:')) and
                    not re.search(r'\(\d+\)', line)):
                    abstract_start = i
                    break
        
        if abstract_start == -1:
            return ""
        
        # Find the end of abstract content (before DOI/PMID section)
        abstract_end = len(lines)
        for i in range(abstract_start, len(lines)):
            if lines[i].startswith(('DOI:', 'PMID:', 'PMCID:', 'Copyright')):
                abstract_end = i
                break
        
        # Join the abstract lines
        abstract_lines = lines[abstract_start:abstract_end]
        return ' '.join(abstract_lines).strip()

    def extract_identifiers(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract DOI, PMID, and PMCID from text.
        
        Args:
            text: Raw abstract text
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: (doi, pmid, pmcid)
        """
        doi_match = self.doi_pattern.search(text)
        pmid_match = self.pmid_pattern.search(text)
        pmcid_match = self.pmcid_pattern.search(text)
        
        doi = doi_match.group(1).rstrip('.') if doi_match else None
        pmid = pmid_match.group(1).rstrip('.') if pmid_match else None
        pmcid = pmcid_match.group(1).rstrip('.') if pmcid_match else None
        
        return doi, pmid, pmcid

    def parse_abstract(self, raw_text: str, include_raw: bool = False) -> List[AbstractRecord]:
        """
        Parse abstract(s) from raw text into structured format.
        
        Args:
            raw_text: Raw abstract text in PubMed format (single or multiple abstracts)
            include_raw: Whether to include raw text in the record
            
        Returns:
            List[AbstractRecord]: List of successfully parsed abstract records
        """
        if not raw_text or not raw_text.strip():
            logger.warning("Empty or whitespace-only text provided")
            return []
        
        # Check if this contains multiple abstracts (look for multiple numbered citations)
        citation_pattern = re.compile(r'^\d+\.\s+.*?\d{4}', re.MULTILINE)
        citations = citation_pattern.findall(raw_text)
        
        if len(citations) > 1:
            # Multiple abstracts - use the existing multiple parsing logic with auto-detection
            logger.info(f"Detected multiple abstracts ({len(citations)} citations) - using multiple parsing")
            return self.parse_multiple_abstracts(raw_text, "\n\n\n", include_raw)
        else:
            # Single abstract - parse it
            try:
                # Extract components
                journal, year, journal_doi = self.extract_journal_info(raw_text)
                title = self.extract_title(raw_text)
                authors = self.extract_authors(raw_text)
                abstract_text = self.extract_abstract_text(raw_text)
                doi, pmid, pmcid = self.extract_identifiers(raw_text)
                
                # Use DOI from journal line if not found elsewhere
                if not doi:
                    doi = journal_doi
                
                # Validate required fields
                if not title:
                    logger.warning("Could not extract title from abstract")
                    return []
                
                if not abstract_text:
                    logger.warning("Could not extract abstract text")
                    return []
                
                # Create record
                record = AbstractRecord(
                    title=title,
                    authors=authors,
                    year=year,
                    abstract_text=abstract_text,
                    journal=journal,
                    doi=doi,
                    pmid=pmid,
                    pmcid=pmcid,
                    raw_text=raw_text if include_raw else None
                )
                
                logger.info(f"Successfully parsed abstract: '{title[:50]}...'")
                return [record]
                
            except Exception as e:
                logger.error(f"Error parsing abstract: {e}")
                return []

    def parse_single_abstract(self, raw_text: str, include_raw: bool = False) -> Optional[AbstractRecord]:
        """
        Parse a single abstract from raw text (internal helper method).
        
        Args:
            raw_text: Raw abstract text in PubMed format
            include_raw: Whether to include raw text in the record
            
        Returns:
            Optional[AbstractRecord]: Parsed abstract record or None if parsing failed
        """
        if not raw_text or not raw_text.strip():
            return None
        
        try:
            # Extract components
            journal, year, journal_doi = self.extract_journal_info(raw_text)
            title = self.extract_title(raw_text)
            authors = self.extract_authors(raw_text)
            abstract_text = self.extract_abstract_text(raw_text)
            doi, pmid, pmcid = self.extract_identifiers(raw_text)
            
            # Use DOI from journal line if not found elsewhere
            if not doi:
                doi = journal_doi
            
            # Validate required fields
            if not title or not abstract_text:
                return None
            
            # Create record
            record = AbstractRecord(
                title=title,
                authors=authors,
                year=year,
                abstract_text=abstract_text,
                journal=journal,
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                raw_text=raw_text if include_raw else None
            )
            
            return record
            
        except Exception as e:
            logger.error(f"Error parsing abstract: {e}")
            return None

    def parse_multiple_abstracts(self, 
                                raw_text: str, 
                                separator: str = "\n\n\n",
                                include_raw: bool = False) -> List[AbstractRecord]:
        """
        Parse multiple abstracts from a single text block.
        
        Args:
            raw_text: Raw text containing multiple abstracts
            separator: Separator between abstracts (default: triple newline, but will auto-detect numbered citations)
            include_raw: Whether to include raw text in records
            
        Returns:
            List[AbstractRecord]: List of successfully parsed abstracts
        """
        if not raw_text or not raw_text.strip():
            logger.warning("Empty or whitespace-only text provided")
            return []
        
        # Check for numbered citations pattern (better for PubMed format)
        citation_pattern = re.compile(r'^\d+\.\s+.*?\d{4}', re.MULTILINE)
        citations = citation_pattern.findall(raw_text)
        
        if len(citations) > 1:
            logger.info(f"Detected {len(citations)} numbered citations - using citation-based splitting")
            # Split by numbered citations at the beginning of lines
            split_pattern = re.compile(r'\n(?=\d+\.\s)')
            abstract_texts = split_pattern.split(raw_text)
        else:
            logger.info("No multiple citations detected - using separator-based splitting")
            # Fall back to separator-based splitting
            abstract_texts = raw_text.split(separator)
        
        records = []
        
        for i, abstract_text in enumerate(abstract_texts, 1):
            abstract_text = abstract_text.strip()
            if not abstract_text:
                continue
                
            logger.info(f"Parsing abstract {i} of {len(abstract_texts)}")
            record = self.parse_single_abstract(abstract_text, include_raw)
            
            if record:
                records.append(record)
            else:
                logger.warning(f"Failed to parse abstract {i}")
                # Debug: show first 200 characters of failed abstract
                logger.debug(f"Failed abstract text (first 200 chars): {abstract_text[:200]}...")
        
        logger.info(f"Successfully parsed {len(records)} out of {len(abstract_texts)} abstracts")
        return records


def parse_abstract_text(raw_text: str, include_raw: bool = False) -> List[AbstractRecord]:
    """
    Convenience function to parse abstract(s).
    
    Args:
        raw_text: Raw abstract text in PubMed format (single or multiple abstracts)
        include_raw: Whether to include raw text in the record
        
    Returns:
        List[AbstractRecord]: List of successfully parsed abstract records
    """
    parser = AbstractParser()
    return parser.parse_abstract(raw_text, include_raw)


def parse_multiple_abstracts(raw_text: str, 
                           separator: str = "\n\n\n",
                           include_raw: bool = False) -> List[AbstractRecord]:
    """
    Convenience function to parse multiple abstracts.
    
    Args:
        raw_text: Raw text containing multiple abstracts
        separator: Separator between abstracts
        include_raw: Whether to include raw text in records
        
    Returns:
        List[AbstractRecord]: List of successfully parsed abstracts
    """
    parser = AbstractParser()
    return parser.parse_multiple_abstracts(raw_text, separator, include_raw)


# Example usage and testing
if __name__ == "__main__":
    # Sample abstract text from the context
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

    print("=== Abstract Parser Example Usage ===\n")
    
    # Parse abstract(s)
    parser = AbstractParser()
    records = parser.parse_abstract(sample_text, include_raw=True)
    
    if records:
        print(f"Successfully parsed {len(records)} abstract(s):")
        for i, record in enumerate(records, 1):
            print(f"\n--- Abstract {i} ---")
            print(f"Title: {record.title}")
            print(f"Authors: {record.authors}")
            print(f"Year: {record.year}")
            print(f"Journal: {record.journal}")
            print(f"DOI: {record.doi}")
            print(f"PMID: {record.pmid}")
            print(f"PMCID: {record.pmcid}")
            print(f"Abstract (first 100 chars): {record.abstract_text[:100]}...")
            if i == 1:  # Show JSON for first record only
                print(f"\nJSON representation:\n{record.to_json()}")
    else:
        print("Failed to parse any abstracts")
