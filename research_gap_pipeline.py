#!/usr/bin/env python3
"""
Medical Research Gap Analysis Pipeline

This script creates a complete pipeline that:
1. Loads medical research abstracts from AWS S3 (s3_load)
2. Parses abstracts into structured data (abstract_parser)
3. Extracts themes and topics using BERTopic (theme_model)
4. Saves results to CSV files in the data directory

Usage:
    python research_gap_pipeline.py
    
The script uses the same S3 configuration as test_s3_load.py:
- Bucket: research-gap
- File: abstract-artificial-set.txt
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Import pipeline components
from scripts.s3_load import S3DataLoader
from scripts.abstract_parser import parse_abstract_text, AbstractRecord
from scripts.theme_model import (
    extract_themes_from_abstracts, 
    save_abstracts_with_topics, 
    save_topic_info_to_csv, 
    print_topic_info,
    create_topic_visualizations,
    create_visualization_summary,
    open_visualizations_in_browser
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchGapPipeline:
    """Complete pipeline for medical research gap analysis."""
    
    def __init__(self, 
                 bucket_name: str = "research-gap",
                 file_key: str = "abstract-artificial-set (1).txt",
                 output_dir: str = "data"):
        """
        Initialize the pipeline with S3 configuration.
        
        Args:
            bucket_name: S3 bucket name
            file_key: S3 file key (path to abstracts file)
            output_dir: Directory to save output CSV files
        """
        self.bucket_name = bucket_name
        self.file_key = file_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize S3 loader
        self.s3_loader = S3DataLoader(
            region_name='us-east-1',
            use_secrets_manager=True,
            secret_name='research-gap-app/secrets'
        )
        
        # Pipeline data
        self.raw_text: Optional[str] = None
        self.abstract_records: Optional[List[AbstractRecord]] = None
        self.topic_model = None
        self.topics: Optional[List[int]] = None
        self.probs = None
        self.visualization_files = None
        self.visualization_index = None
    
    def step1_load_from_s3(self) -> bool:
        """
        Step 1: Load abstracts from S3.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("="*60)
        logger.info("STEP 1: Loading abstracts from S3")
        logger.info("="*60)
        
        try:
            # Test connection
            logger.info("Testing S3 connection...")
            if not self.s3_loader.test_connection():
                logger.error("❌ S3 connection failed. Check AWS credentials.")
                return False
            logger.info("✅ S3 connection successful")
            
            # Get file metadata
            logger.info(f"Getting metadata for s3://{self.bucket_name}/{self.file_key}")
            metadata = self.s3_loader.get_file_metadata(self.bucket_name, self.file_key)
            if metadata:
                logger.info(f"📊 File size: {metadata['size']:,} bytes")
                logger.info(f"📅 Last modified: {metadata['last_modified']}")
            
            # Load file content
            logger.info("Loading file content...")
            self.raw_text = self.s3_loader.load_abstracts_from_s3(self.bucket_name, self.file_key)
            
            if not self.raw_text:
                logger.error("❌ Failed to load content from S3")
                return False
            
            logger.info(f"✅ Successfully loaded {len(self.raw_text):,} characters")
            logger.info(f"First 200 characters: {self.raw_text[:200]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading from S3: {e}")
            return False
    
    def step2_parse_abstracts(self) -> bool:
        """
        Step 2: Parse raw text into structured AbstractRecord objects.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("="*60)
        logger.info("STEP 2: Parsing abstracts into structured data")
        logger.info("="*60)
        
        if not self.raw_text:
            logger.error("❌ No raw text available. Run step1_load_from_s3() first.")
            return False
        
        try:
            logger.info("Parsing abstracts...")
            self.abstract_records = parse_abstract_text(self.raw_text)
            logger.info(f"📊 COUNT: Parsed {len(self.abstract_records)} abstracts")
            
            if not self.abstract_records:
                logger.error("❌ No abstracts were parsed from the text")
                return False
            
            logger.info(f"✅ Successfully parsed {len(self.abstract_records)} abstracts")
            
            # Show sample abstracts
            logger.info("Sample abstracts:")
            for i, record in enumerate(self.abstract_records[:3]):
                logger.info(f"  {i+1}. {record.title[:80]}...")
                logger.info(f"     Authors: {', '.join(record.authors[:3]) if record.authors else 'N/A'}")
                logger.info(f"     Year: {record.year}")
                logger.info(f"     Journal: {record.journal[:50] if record.journal else 'N/A'}...")
            
            if len(self.abstract_records) > 3:
                logger.info(f"     ... and {len(self.abstract_records) - 3} more abstracts")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error parsing abstracts: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step3_extract_themes(self) -> bool:
        """
        Step 3: Extract themes and topics using BERTopic.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("="*60)
        logger.info("STEP 3: Extracting themes with BERTopic")
        logger.info("="*60)
        
        if not self.abstract_records:
            logger.error("❌ No abstract records available. Run step2_parse_abstracts() first.")
            return False
        
        try:
            logger.info(f"Starting theme extraction for {len(self.abstract_records)} abstracts...")
            
            # Check if we have enough abstracts for meaningful topic modeling
            if len(self.abstract_records) < 10:
                logger.warning(f"Only {len(self.abstract_records)} abstracts found. BERTopic works best with 50+ abstracts.")
            
            # Extract themes using combined title and abstract text
            self.topic_model, self.topics, self.probs = extract_themes_from_abstracts(
                self.abstract_records,
                text_field='combined'  # Use both title and abstract text
            )
            
            logger.info(f"✅ Theme extraction completed!")
            logger.info(f"Found {len(set(self.topics))} unique topics")
            
            # Show topic distribution
            import numpy as np
            unique_topics, counts = np.unique(self.topics, return_counts=True)
            topic_distribution = dict(zip(unique_topics, counts))
            logger.info(f"Topic distribution: {topic_distribution}")
            
            # Print detailed topic information
            print_topic_info(
                self.topic_model, 
                self.topics, 
                [f"{r.title}. {r.abstract_text}" for r in self.abstract_records]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in theme extraction: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step4_save_results(self) -> bool:
        """
        Step 4: Save results to CSV files.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("="*60)
        logger.info("STEP 4: Saving results to CSV files")
        logger.info("="*60)
        
        if not all([self.abstract_records, self.topic_model, self.topics is not None]):
            logger.error("❌ Pipeline data incomplete. Run previous steps first.")
            return False
        
        try:
            # Save abstracts with topic assignments
            abstracts_csv = self.output_dir / 'research_gap_abstracts_with_themes.csv'
            logger.info(f"Saving abstracts with themes to: {abstracts_csv}")
            save_abstracts_with_topics(
                self.abstract_records,
                self.topics,
                self.topic_model,
                str(abstracts_csv)
            )
            
            # Save topic information
            topic_info_csv = self.output_dir / 'research_gap_topic_info.csv'
            logger.info(f"Saving topic information to: {topic_info_csv}")
            save_topic_info_to_csv(
                self.topic_model,
                self.topics,
                [f"{record.title}. {record.abstract_text}" for record in self.abstract_records],
                str(topic_info_csv)
            )
            
            # Show output file information
            logger.info("✅ Results saved successfully!")
            logger.info("Output files:")
            for csv_file in [abstracts_csv, topic_info_csv]:
                if csv_file.exists():
                    size_kb = csv_file.stat().st_size / 1024
                    logger.info(f"  📄 {csv_file.name} ({size_kb:.1f} KB)")
            
            # Also check for the additional CSV files created by save_topic_info_to_csv
            for pattern in ['*documents.csv', '*summary.csv']:
                for csv_file in self.output_dir.glob(pattern):
                    size_kb = csv_file.stat().st_size / 1024
                    logger.info(f"  📄 {csv_file.name} ({size_kb:.1f} KB)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step5_create_visualizations(self) -> bool:
        """
        Step 5: Create interactive BERTopic visualizations.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("="*60)
        logger.info("STEP 5: Creating interactive BERTopic visualizations")
        logger.info("="*60)
        
        if not all([self.abstract_records, self.topic_model, self.topics is not None]):
            logger.error("❌ Pipeline data incomplete. Run previous steps first.")
            return False
        
        try:
            # Create visualizations directory
            viz_dir = self.output_dir / 'visualizations'
            logger.info(f"Creating visualizations in: {viz_dir}")
            
            # Prepare document texts for visualization
            docs = [f"{record.title}. {record.abstract_text}" for record in self.abstract_records]
            
            # Create all visualizations
            visualization_files = create_topic_visualizations(
                self.topic_model,
                docs,
                self.topics,
                str(viz_dir)
            )
            
            if visualization_files:
                # Create index page
                index_path = create_visualization_summary(
                    visualization_files,
                    str(viz_dir)
                )
                
                logger.info("✅ Visualizations created successfully!")
                logger.info(f"📊 Created {len(visualization_files)} interactive visualizations")
                logger.info(f"🌐 Index page: {index_path}")
                logger.info("")
                logger.info("Available visualizations:")
                for name, path in visualization_files.items():
                    logger.info(f"  📈 {name}: {Path(path).name}")
                
                # Store visualization info for potential browser opening
                self.visualization_files = visualization_files
                self.visualization_index = index_path
                
                return True
            else:
                logger.warning("⚠️  No visualizations were created successfully")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error creating visualizations: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def open_visualizations(self) -> bool:
        """
        Open the visualization index page in the default web browser.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not hasattr(self, 'visualization_index'):
            logger.error("❌ No visualizations available. Run step5_create_visualizations() first.")
            return False
        
        try:
            import webbrowser
            file_url = f"file://{os.path.abspath(self.visualization_index)}"
            webbrowser.open(file_url)
            logger.info(f"🌐 Opened visualization index in browser: {self.visualization_index}")
            return True
        except Exception as e:
            logger.error(f"❌ Error opening visualizations: {e}")
            return False
    
    def run_full_pipeline(self) -> bool:
        """
        Run the complete pipeline: S3 → Parser → BERTopic → CSV
        
        Returns:
            bool: True if all steps successful, False otherwise
        """
        logger.info("🚀 Starting Medical Research Gap Analysis Pipeline")
        logger.info(f"S3 Source: s3://{self.bucket_name}/{self.file_key}")
        logger.info(f"Output Directory: {self.output_dir}")
        
        # Check environment
        if not os.getenv('AWS_ACCESS_KEY_ID') and not os.getenv('AWS_SECRET_ACCESS_KEY'):
            logger.warning("⚠️  AWS credentials not found in environment variables")
            logger.warning("   Pipeline will try AWS Secrets Manager first")
        
        # Run pipeline steps
        steps = [
            ("Load from S3", self.step1_load_from_s3),
            ("Parse Abstracts", self.step2_parse_abstracts),
            ("Extract Themes", self.step3_extract_themes),
            ("Save Results", self.step4_save_results),
            ("Create Visualizations", self.step5_create_visualizations)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n🔄 Running: {step_name}")
            if not step_func():
                logger.error(f"💥 Pipeline failed at step: {step_name}")
                return False
        
        logger.info("\n" + "="*60)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info(f"✅ Processed {len(self.abstract_records)} abstracts")
        logger.info(f"✅ Identified {len(set(self.topics))} topics")
        logger.info(f"✅ Results saved to {self.output_dir}")
        
        if hasattr(self, 'visualization_files') and self.visualization_files:
            logger.info(f"✅ Created {len(self.visualization_files)} interactive visualizations")
            logger.info(f"🌐 Open visualizations: file://{os.path.abspath(self.visualization_index)}")
        
        return True


def main():
    """Main function to run the pipeline."""
    
    # Create and run pipeline
    pipeline = ResearchGapPipeline(
        bucket_name="research-gap",
        file_key="abstract-artificial-set (1).txt",
        output_dir="data"
    )
    
    success = pipeline.run_full_pipeline()
    
    # Optionally open visualizations in browser
    if success and hasattr(pipeline, 'visualization_index'):
        logger.info("")
        logger.info("💡 To view interactive visualizations, you can:")
        logger.info(f"   1. Open: {pipeline.visualization_index}")
        logger.info("   2. Or call pipeline.open_visualizations() in Python")
        
        # Uncomment the line below to automatically open visualizations
        # pipeline.open_visualizations()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
