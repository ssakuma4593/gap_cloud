#!/usr/bin/env python3
"""
Simple test script for S3 data loader functionality.
Demonstrates basic usage patterns for the S3DataLoader class.
"""

import os
import sys
from s3_load import S3DataLoader

def test_s3_loader():
    """
    Basic test function for S3DataLoader.
    This is a simple example - replace bucket and file parameters with your actual values.
    """
    
    print("=== S3DataLoader Test Script ===\n")
    
    # Actual configuration for your S3 bucket and file
    BUCKET_NAME = "research-gap"  # Your S3 bucket for research data
    FILE_KEY = "abstract-artificial-set.txt"  # Your actual abstracts file
    
    print("⚠️  Note: This is a test script. Please update BUCKET_NAME and FILE_KEY")
    print("    with your actual S3 bucket and file path before running.\n")
    
    try:
        # Initialize the S3 loader (will try Secrets Manager first, then env vars)
        print("1. Initializing S3 loader with Secrets Manager support...")
        loader = S3DataLoader(
            region_name='us-east-1',
            use_secrets_manager=True,
            secret_name='research-gap-app/secrets'
        )
        
        # Test connection
        print("2. Testing S3 connection...")
        if not loader.test_connection():
            print("❌ Connection test failed")
            return False
        print("✅ Connection successful")
        
        # Get file metadata (optional)
        print(f"3. Getting metadata for {FILE_KEY}...")
        metadata = loader.get_file_metadata(BUCKET_NAME, FILE_KEY)
        if metadata:
            print(f"   📊 File size: {metadata['size']:,} bytes")
            print(f"   📅 Last modified: {metadata['last_modified']}")
        
        # Load the actual file
        print("4. Loading file content...")
        content = loader.load_abstracts_from_s3(BUCKET_NAME, FILE_KEY)
        
        if content:
            print(f"✅ Successfully loaded {len(content):,} characters")
            print(f"\n=== First 500 characters ===")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            return True
        else:
            print("❌ Failed to load content")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    # Check if environment variables are set
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("⚠️  Warning: AWS credentials not found in environment variables")
        print("   Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("   You can copy .env.example to .env and update with your credentials\n")
    
    success = test_s3_loader()
    sys.exit(0 if success else 1)
