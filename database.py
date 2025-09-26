#!/usr/bin/env python3
"""
Database models and utilities for the Medical Research Gap Analysis Tool.

This module defines the PostgreSQL database schema using SQLAlchemy for storing
research papers and their metadata.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class ResearchPaper(Base):
    """
    SQLAlchemy model for storing research paper metadata.
    
    Schema fields as specified in the issue:
    - Title
    - Authors  
    - Year
    - Journal
    - DOI
    - DOI link (constructed as https://doi.org/{DOI})
    """
    __tablename__ = 'research_papers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False, index=True)
    authors = Column(Text, nullable=True)  # Store as comma-separated string or JSON
    year = Column(Integer, nullable=True, index=True)
    journal = Column(String(500), nullable=True, index=True)
    doi = Column(String(255), nullable=True, unique=True, index=True)
    doi_link = Column(String(300), nullable=True)  # Will be auto-generated from DOI
    
    # Additional metadata fields for tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, title: str, authors: Optional[str] = None, year: Optional[int] = None,
                 journal: Optional[str] = None, doi: Optional[str] = None):
        self.title = title
        self.authors = authors
        self.year = year
        self.journal = journal
        self.doi = doi
        
        # Auto-generate DOI link if DOI is provided
        if doi:
            self.doi_link = f"https://doi.org/{doi}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'year': self.year,
            'journal': self.journal,
            'doi': self.doi,
            'doi_link': self.doi_link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<ResearchPaper(id={self.id}, title='{self.title[:50]}...', year={self.year})>"


class DatabaseManager:
    """
    Database connection and session management for the research gap analysis tool.
    """
    
    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            database_url: PostgreSQL connection URL. If None, will be read from environment
            echo: Whether to echo SQL queries (useful for debugging)
        """
        if database_url is None:
            database_url = self._get_database_url_from_env()
        
        if not database_url:
            raise ValueError("Database URL not provided and not found in environment variables")
        
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=echo)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Database manager initialized with URL: {self._mask_password(database_url)}")
    
    def _get_database_url_from_env(self) -> Optional[str]:
        """
        Construct database URL from environment variables.
        
        Expected environment variables:
        - DATABASE_URL (full URL) OR
        - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        """
        # First try to get full DATABASE_URL
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url
        
        # Otherwise construct from individual components
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        name = os.getenv('DB_NAME', 'research_gaps')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD')
        
        if not password:
            logger.warning("No database password found in environment variables")
            return None
        
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging."""
        try:
            parsed = urlparse(url)
            if parsed.password:
                masked_url = url.replace(parsed.password, '***')
                return masked_url
            return url
        except Exception:
            return "***masked***"
    
    def create_tables(self) -> bool:
        """
        Create all database tables.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                # Use different queries for different database types
                if 'sqlite' in self.database_url.lower():
                    # SQLite version query
                    result = connection.execute(func.sqlite_version())
                    version = result.fetchone()[0]
                    logger.info(f"Database connection successful. SQLite version: {version}")
                else:
                    # PostgreSQL version query
                    result = connection.execute(func.version())
                    version = result.fetchone()[0]
                    logger.info(f"Database connection successful. PostgreSQL version: {version}")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            Session: SQLAlchemy session object
        """
        return self.SessionLocal()
    
    def close(self):
        """Close the database engine."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.info("Database connection closed")


class ResearchPaperRepository:
    """
    Repository class for research paper database operations.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_paper(self, title: str, authors: Optional[str] = None, 
                    year: Optional[int] = None, journal: Optional[str] = None,
                    doi: Optional[str] = None) -> Optional[ResearchPaper]:
        """
        Create a new research paper record.
        
        Args:
            title: Paper title
            authors: Authors (comma-separated string)
            year: Publication year
            journal: Journal name
            doi: DOI identifier
            
        Returns:
            Optional[ResearchPaper]: Created paper record or None if failed
        """
        session = self.db_manager.get_session()
        try:
            paper = ResearchPaper(
                title=title,
                authors=authors,
                year=year,
                journal=journal,
                doi=doi
            )
            
            session.add(paper)
            session.commit()
            session.refresh(paper)
            
            logger.info(f"Created research paper: {paper.id}")
            return paper
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create research paper: {e}")
            return None
        finally:
            session.close()
    
    def get_paper_by_id(self, paper_id: int) -> Optional[ResearchPaper]:
        """Get research paper by ID."""
        session = self.db_manager.get_session()
        try:
            paper = session.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
            return paper
        except Exception as e:
            logger.error(f"Failed to get paper by ID {paper_id}: {e}")
            return None
        finally:
            session.close()
    
    def get_paper_by_doi(self, doi: str) -> Optional[ResearchPaper]:
        """Get research paper by DOI."""
        session = self.db_manager.get_session()
        try:
            paper = session.query(ResearchPaper).filter(ResearchPaper.doi == doi).first()
            return paper
        except Exception as e:
            logger.error(f"Failed to get paper by DOI {doi}: {e}")
            return None
        finally:
            session.close()
    
    def list_papers(self, limit: int = 100, offset: int = 0, 
                   year: Optional[int] = None, journal: Optional[str] = None) -> List[ResearchPaper]:
        """
        List research papers with optional filtering.
        
        Args:
            limit: Maximum number of papers to return
            offset: Number of papers to skip
            year: Filter by publication year
            journal: Filter by journal name
            
        Returns:
            List[ResearchPaper]: List of papers
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(ResearchPaper)
            
            if year:
                query = query.filter(ResearchPaper.year == year)
            if journal:
                query = query.filter(ResearchPaper.journal.ilike(f"%{journal}%"))
            
            papers = query.offset(offset).limit(limit).all()
            return papers
            
        except Exception as e:
            logger.error(f"Failed to list papers: {e}")
            return []
        finally:
            session.close()
    
    def update_paper(self, paper_id: int, **kwargs) -> Optional[ResearchPaper]:
        """
        Update research paper fields.
        
        Args:
            paper_id: Paper ID to update
            **kwargs: Fields to update
            
        Returns:
            Optional[ResearchPaper]: Updated paper or None if failed
        """
        session = self.db_manager.get_session()
        try:
            paper = session.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
            if not paper:
                logger.warning(f"Paper with ID {paper_id} not found")
                return None
            
            # Update provided fields
            for key, value in kwargs.items():
                if hasattr(paper, key):
                    setattr(paper, key, value)
            
            # Auto-update DOI link if DOI was updated
            if 'doi' in kwargs and kwargs['doi']:
                paper.doi_link = f"https://doi.org/{kwargs['doi']}"
            
            session.commit()
            session.refresh(paper)
            
            logger.info(f"Updated research paper: {paper.id}")
            return paper
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update paper {paper_id}: {e}")
            return None
        finally:
            session.close()
    
    def delete_paper(self, paper_id: int) -> bool:
        """
        Delete research paper by ID.
        
        Args:
            paper_id: Paper ID to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        session = self.db_manager.get_session()
        try:
            paper = session.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
            if not paper:
                logger.warning(f"Paper with ID {paper_id} not found")
                return False
            
            session.delete(paper)
            session.commit()
            
            logger.info(f"Deleted research paper: {paper_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete paper {paper_id}: {e}")
            return False
        finally:
            session.close()
    
    def count_papers(self, year: Optional[int] = None, journal: Optional[str] = None) -> int:
        """
        Count research papers with optional filtering.
        
        Args:
            year: Filter by publication year
            journal: Filter by journal name
            
        Returns:
            int: Number of papers matching criteria
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(ResearchPaper)
            
            if year:
                query = query.filter(ResearchPaper.year == year)
            if journal:
                query = query.filter(ResearchPaper.journal.ilike(f"%{journal}%"))
            
            count = query.count()
            return count
            
        except Exception as e:
            logger.error(f"Failed to count papers: {e}")
            return 0
        finally:
            session.close()