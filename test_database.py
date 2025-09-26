#!/usr/bin/env python3
"""
Test script for database functionality.
This tests the database models and operations without requiring a live PostgreSQL connection.
"""

import os
import sys
import tempfile
import logging
from database import DatabaseManager, ResearchPaperRepository, ResearchPaper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_models():
    """Test database models using SQLite in-memory database."""
    print("=== Database Models Test ===\n")
    
    try:
        # Use SQLite in-memory database for testing
        database_url = "sqlite:///:memory:"
        
        print("1. Initializing database manager with SQLite...")
        db_manager = DatabaseManager(database_url=database_url, echo=False)
        
        print("2. Testing database connection...")
        if not db_manager.test_connection():
            print("❌ Connection test failed")
            return False
        print("✅ Connection successful")
        
        print("3. Creating database tables...")
        if not db_manager.create_tables():
            print("❌ Failed to create tables")
            return False
        print("✅ Tables created successfully")
        
        print("4. Testing ResearchPaper model...")
        repository = ResearchPaperRepository(db_manager)
        
        # Test creating a paper
        print("   Creating sample research paper...")
        paper = repository.create_paper(
            title="Machine Learning in Medical Diagnosis: A Comprehensive Review",
            authors="Smith, J., Johnson, A., Williams, R.",
            year=2023,
            journal="Journal of Medical AI",
            doi="10.1234/jmai.2023.001"
        )
        
        if not paper:
            print("❌ Failed to create paper")
            return False
        
        print(f"✅ Created paper with ID: {paper.id}")
        print(f"   Title: {paper.title}")
        print(f"   Authors: {paper.authors}")
        print(f"   Year: {paper.year}")
        print(f"   Journal: {paper.journal}")
        print(f"   DOI: {paper.doi}")
        print(f"   DOI Link: {paper.doi_link}")
        
        # Test retrieving paper by ID
        print("5. Testing paper retrieval by ID...")
        retrieved_paper = repository.get_paper_by_id(paper.id)
        if not retrieved_paper:
            print("❌ Failed to retrieve paper by ID")
            return False
        print(f"✅ Retrieved paper: {retrieved_paper.title[:50]}...")
        
        # Test retrieving paper by DOI
        print("6. Testing paper retrieval by DOI...")
        doi_paper = repository.get_paper_by_doi(paper.doi)
        if not doi_paper:
            print("❌ Failed to retrieve paper by DOI")
            return False
        print(f"✅ Retrieved paper by DOI: {doi_paper.title[:50]}...")
        
        # Test creating multiple papers
        print("7. Creating additional papers...")
        papers_data = [
            {
                'title': 'Deep Learning in Radiology: Current Applications',
                'authors': 'Chen, L., Davis, M.',
                'year': 2023,
                'journal': 'Radiology and AI',
                'doi': '10.1234/radai.2023.045'
            },
            {
                'title': 'Natural Language Processing for Clinical Text',
                'authors': 'Garcia, E., Wilson, P.',
                'year': 2022,
                'journal': 'Clinical Informatics Review',
                'doi': '10.1234/cir.2022.078'
            }
        ]
        
        created_papers = []
        for paper_data in papers_data:
            created_paper = repository.create_paper(**paper_data)
            if created_paper:
                created_papers.append(created_paper)
                print(f"✅ Created: {created_paper.title[:50]}...")
            else:
                print(f"❌ Failed to create paper: {paper_data['title'][:50]}...")
        
        # Test listing papers
        print("8. Testing paper listing...")
        all_papers = repository.list_papers(limit=10)
        print(f"✅ Retrieved {len(all_papers)} papers")
        
        for p in all_papers:
            print(f"   - [{p.year}] {p.title[:50]}...")
        
        # Test filtering by year
        print("9. Testing filtering by year...")
        papers_2023 = repository.list_papers(year=2023)
        papers_2022 = repository.list_papers(year=2022)
        print(f"✅ Papers from 2023: {len(papers_2023)}")
        print(f"✅ Papers from 2022: {len(papers_2022)}")
        
        # Test counting papers
        print("10. Testing paper counting...")
        total_count = repository.count_papers()
        count_2023 = repository.count_papers(year=2023)
        print(f"✅ Total papers: {total_count}")
        print(f"✅ Papers from 2023: {count_2023}")
        
        # Test updating a paper
        print("11. Testing paper updates...")
        updated_paper = repository.update_paper(
            paper.id, 
            title="Updated Title: Machine Learning in Medical Diagnosis",
            year=2024
        )
        if updated_paper:
            print(f"✅ Updated paper: {updated_paper.title}")
            print(f"   New year: {updated_paper.year}")
        else:
            print("❌ Failed to update paper")
        
        # Test to_dict method
        print("12. Testing dictionary conversion...")
        paper_dict = paper.to_dict()
        print(f"✅ Paper as dict: {list(paper_dict.keys())}")
        
        # Test deleting a paper
        print("13. Testing paper deletion...")
        if len(created_papers) > 0:
            delete_paper_id = created_papers[0].id
            if repository.delete_paper(delete_paper_id):
                print(f"✅ Deleted paper with ID: {delete_paper_id}")
                
                # Verify deletion
                deleted_paper = repository.get_paper_by_id(delete_paper_id)
                if deleted_paper is None:
                    print("✅ Paper deletion verified")
                else:
                    print("❌ Paper was not actually deleted")
            else:
                print("❌ Failed to delete paper")
        
        db_manager.close()
        print("\n✅ All database tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        print(f"❌ Database test failed: {e}")
        return False


def test_doi_link_generation():
    """Test DOI link auto-generation."""
    print("\n=== DOI Link Generation Test ===\n")
    
    try:
        # Test with different DOI formats
        test_cases = [
            "10.1234/example.2023.001",
            "10.1016/j.cell.2023.04.012",
            "10.1038/nature12373",
            None  # Test without DOI
        ]
        
        for doi in test_cases:
            paper = ResearchPaper(
                title="Test Paper",
                authors="Test Author",
                year=2023,
                journal="Test Journal",
                doi=doi
            )
            
            expected_link = f"https://doi.org/{doi}" if doi else None
            actual_link = paper.doi_link
            
            print(f"DOI: {doi or 'None'}")
            print(f"Expected link: {expected_link or 'None'}")
            print(f"Actual link: {actual_link or 'None'}")
            
            if expected_link == actual_link:
                print("✅ DOI link generation correct\n")
            else:
                print("❌ DOI link generation incorrect\n")
                return False
        
        print("✅ All DOI link tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"DOI link test failed: {e}")
        print(f"❌ DOI link test failed: {e}")
        return False


def main():
    """Run all database tests."""
    print("=== Medical Research Gap Analysis - Database Tests ===\n")
    
    # Check if required modules are available
    try:
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        print("❌ SQLAlchemy not installed. Run: pip install -r requirements.txt")
        sys.exit(1)
    
    success = True
    
    # Run model tests
    if not test_database_models():
        success = False
    
    # Run DOI link tests
    if not test_doi_link_generation():
        success = False
    
    if success:
        print("\n🎉 All tests passed successfully!")
        print("\nNext steps:")
        print("1. Set up a PostgreSQL database")
        print("2. Configure DATABASE_URL in your .env file")
        print("3. Run: python init_database.py init")
        print("4. Run: python init_database.py seed")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()