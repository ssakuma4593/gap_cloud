#!/usr/bin/env python3
"""
Database initialization script for the Medical Research Gap Analysis Tool.

This script sets up the PostgreSQL database schema and provides utilities
for database management.
"""

import os
import sys
import argparse
import logging
from typing import Optional

from database import DatabaseManager, ResearchPaperRepository, ResearchPaper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_environment_variables():
    """Load environment variables from .env file if available."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.info("python-dotenv not available, using system environment variables only")


def initialize_database(database_url: Optional[str] = None, echo: bool = False) -> bool:
    """
    Initialize the database schema.
    
    Args:
        database_url: PostgreSQL connection URL
        echo: Whether to echo SQL queries
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize database manager
        db_manager = DatabaseManager(database_url=database_url, echo=echo)
        
        # Test connection
        print("Testing database connection...")
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return False
        print("✅ Database connection successful")
        
        # Create tables
        print("Creating database tables...")
        if not db_manager.create_tables():
            print("❌ Failed to create database tables")
            return False
        print("✅ Database tables created successfully")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"❌ Database initialization failed: {e}")
        return False


def seed_sample_data(database_url: Optional[str] = None) -> bool:
    """
    Seed the database with sample research paper data.
    
    Args:
        database_url: PostgreSQL connection URL
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db_manager = DatabaseManager(database_url=database_url)
        repository = ResearchPaperRepository(db_manager)
        
        # Sample research papers
        sample_papers = [
            {
                'title': 'Machine Learning Approaches for Medical Diagnosis: A Systematic Review',
                'authors': 'Smith, J., Johnson, A., Williams, R.',
                'year': 2023,
                'journal': 'Journal of Medical AI',
                'doi': '10.1234/jmai.2023.001'
            },
            {
                'title': 'Deep Learning in Radiology: Current Applications and Future Directions',
                'authors': 'Chen, L., Davis, M., Thompson, K.',
                'year': 2023,
                'journal': 'Radiology and AI',
                'doi': '10.1234/radai.2023.045'
            },
            {
                'title': 'Natural Language Processing for Clinical Text Analysis',
                'authors': 'Garcia, E., Wilson, P., Brown, S.',
                'year': 2022,
                'journal': 'Clinical Informatics Review',
                'doi': '10.1234/cir.2022.078'
            },
            {
                'title': 'Federated Learning in Healthcare: Privacy-Preserving Machine Learning',
                'authors': 'Anderson, T., Lee, H., Martinez, C.',
                'year': 2022,
                'journal': 'Healthcare Technology',
                'doi': '10.1234/ht.2022.156'
            }
        ]
        
        print("Seeding sample data...")
        created_count = 0
        
        for paper_data in sample_papers:
            # Check if paper already exists (by DOI)
            existing = repository.get_paper_by_doi(paper_data['doi'])
            if existing:
                print(f"Paper with DOI {paper_data['doi']} already exists, skipping...")
                continue
            
            paper = repository.create_paper(**paper_data)
            if paper:
                created_count += 1
                print(f"✅ Created paper: {paper.title[:50]}...")
            else:
                print(f"❌ Failed to create paper: {paper_data['title'][:50]}...")
        
        print(f"✅ Seeded {created_count} sample papers")
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to seed sample data: {e}")
        print(f"❌ Failed to seed sample data: {e}")
        return False


def check_database_status(database_url: Optional[str] = None) -> bool:
    """
    Check database status and display information.
    
    Args:
        database_url: PostgreSQL connection URL
        
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        db_manager = DatabaseManager(database_url=database_url)
        repository = ResearchPaperRepository(db_manager)
        
        # Test connection
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return False
        
        # Get paper count
        total_papers = repository.count_papers()
        print(f"📊 Database Status:")
        print(f"   Total papers: {total_papers}")
        
        if total_papers > 0:
            # Get sample papers
            sample_papers = repository.list_papers(limit=5)
            print(f"   Sample papers:")
            for paper in sample_papers:
                print(f"   - [{paper.year}] {paper.title[:50]}...")
                print(f"     DOI: {paper.doi or 'N/A'}")
        
        db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to check database status: {e}")
        print(f"❌ Failed to check database status: {e}")
        return False


def main():
    """Main CLI function for database management."""
    parser = argparse.ArgumentParser(
        description='Database management for Medical Research Gap Analysis Tool'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize database schema')
    init_parser.add_argument('--database-url', help='PostgreSQL connection URL')
    init_parser.add_argument('--echo', action='store_true', help='Echo SQL queries')
    
    # Seed command
    seed_parser = subparsers.add_parser('seed', help='Seed database with sample data')
    seed_parser.add_argument('--database-url', help='PostgreSQL connection URL')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check database status')
    status_parser.add_argument('--database-url', help='PostgreSQL connection URL')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset database (drop and recreate tables)')
    reset_parser.add_argument('--database-url', help='PostgreSQL connection URL')
    reset_parser.add_argument('--confirm', action='store_true', 
                             help='Confirm you want to delete all data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load environment variables
    load_environment_variables()
    
    try:
        if args.command == 'init':
            print("=== Database Initialization ===")
            success = initialize_database(
                database_url=args.database_url,
                echo=args.echo
            )
            sys.exit(0 if success else 1)
            
        elif args.command == 'seed':
            print("=== Database Seeding ===")
            success = seed_sample_data(database_url=args.database_url)
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            print("=== Database Status ===")
            success = check_database_status(database_url=args.database_url)
            sys.exit(0 if success else 1)
            
        elif args.command == 'reset':
            if not args.confirm:
                print("❌ Database reset requires --confirm flag to prevent accidental data loss")
                print("This operation will DELETE ALL DATA in the database!")
                sys.exit(1)
            
            print("=== Database Reset ===")
            print("⚠️  WARNING: This will delete all existing data!")
            
            # Initialize database manager
            db_manager = DatabaseManager(database_url=args.database_url)
            
            # Drop all tables
            print("Dropping existing tables...")
            from database import Base
            Base.metadata.drop_all(bind=db_manager.engine)
            print("✅ Tables dropped")
            
            # Recreate tables
            success = initialize_database(database_url=args.database_url)
            db_manager.close()
            
            if success:
                print("✅ Database reset completed")
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()