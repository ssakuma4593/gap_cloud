#!/usr/bin/env python3
"""
S3 Data Loader for Medical Research Gap Analysis Tool

This module provides functionality to load medical research abstracts 
from AWS S3 using boto3 with proper error handling and security practices.
"""

import os
import sys
import logging
import argparse
import json
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import (
    ClientError, 
    NoCredentialsError, 
    BotoCoreError,
    EndpointConnectionError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_secret(secret_name: str = "research-gap-app/secrets", region_name: str = "us-east-1") -> Optional[Dict[str, str]]:
    """
    Retrieve secrets from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in AWS Secrets Manager
        region_name: AWS region where the secret is stored
        
    Returns:
        Optional[Dict[str, str]]: Dictionary containing the secrets, None if error occurred
    """
    try:
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        logger.info(f"Retrieving secret '{secret_name}' from region '{region_name}'")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        
        # Parse the secret string as JSON
        secret_string = get_secret_value_response['SecretString']
        secrets = json.loads(secret_string)
        
        logger.info(f"Successfully retrieved {len(secrets)} secrets from AWS Secrets Manager")
        return secrets
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'DecryptionFailureException':
            logger.error("Secrets Manager can't decrypt the protected secret text using the provided KMS key")
        elif error_code == 'InternalServiceErrorException':
            logger.error("An error occurred on the server side")
        elif error_code == 'InvalidParameterException':
            logger.error("Invalid parameter provided to Secrets Manager")
        elif error_code == 'InvalidRequestException':
            logger.error("Invalid request to Secrets Manager")
        elif error_code == 'ResourceNotFoundException':
            logger.error(f"Secret '{secret_name}' not found in Secrets Manager")
        else:
            logger.error(f"Secrets Manager error ({error_code}): {e}")
        return None
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse secret as JSON: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving secret: {e}")
        return None


class S3DataLoader:
    """
    A class to handle loading data from AWS S3 with error handling and security.
    """
    
    def __init__(self, 
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None, 
                 region_name: str = 'us-east-1',
                 use_secrets_manager: bool = True,
                 secret_name: str = "research-gap-app/secrets"):
        """
        Initialize S3 client with credentials from Secrets Manager, environment variables, or parameters.
        
        Args:
            aws_access_key_id: AWS access key (optional, uses secrets manager or env var if not provided)
            aws_secret_access_key: AWS secret key (optional, uses secrets manager or env var if not provided)
            region_name: AWS region name (defaults to us-east-1)
            use_secrets_manager: Whether to try AWS Secrets Manager first (defaults to True)
            secret_name: Name of the secret in AWS Secrets Manager
        """
        self.region_name = region_name
        self.secret_name = secret_name
        
        # Credential priority: explicit params > secrets manager > environment variables
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        # Try to get credentials from Secrets Manager if enabled and no explicit credentials provided
        if use_secrets_manager and (not self.aws_access_key_id or not self.aws_secret_access_key):
            logger.info("Attempting to retrieve credentials from AWS Secrets Manager...")
            secrets = get_secret(secret_name, region_name)
            if secrets:
                self.aws_access_key_id = self.aws_access_key_id or secrets.get('AWS_ACCESS_KEY_ID')
                self.aws_secret_access_key = self.aws_secret_access_key or secrets.get('AWS_SECRET_ACCESS_KEY')
                logger.info("Successfully loaded credentials from Secrets Manager")
            else:
                logger.warning("Failed to retrieve credentials from Secrets Manager, falling back to environment variables")
        
        # Fall back to environment variables if still no credentials
        self.aws_access_key_id = self.aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = self.aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # Initialize S3 client
        self.s3_client = self._create_s3_client()
    
    def _create_s3_client(self) -> boto3.client:
        """
        Create and configure S3 client with error handling.
        
        Returns:
            boto3.client: Configured S3 client
            
        Raises:
            NoCredentialsError: If AWS credentials are not found
        """
        try:
            if self.aws_access_key_id and self.aws_secret_access_key:
                # Use explicit credentials
                client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name
                )
            else:
                # Use default credential chain (IAM roles, ~/.aws/credentials, etc.)
                client = boto3.client('s3', region_name=self.region_name)
            
            logger.info(f"S3 client initialized successfully for region: {self.region_name}")
            return client
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to create S3 client: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test S3 connection by listing buckets.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.s3_client.list_buckets()
            logger.info("S3 connection test successful")
            return True
        except EndpointConnectionError:
            logger.error("Failed to connect to S3 endpoint. Check internet connection.")
            return False
        except NoCredentialsError:
            logger.error("Invalid AWS credentials")
            return False
        except ClientError as e:
            logger.error(f"AWS S3 client error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing S3 connection: {e}")
            return False
    
    def load_abstracts_from_s3(self, 
                              bucket_name: str, 
                              file_key: str,
                              encoding: str = 'utf-8') -> Optional[str]:
        """
        Load medical research abstracts from S3 bucket.
        
        Args:
            bucket_name: Name of the S3 bucket
            file_key: S3 object key (path to the file)
            encoding: File encoding (defaults to utf-8)
            
        Returns:
            Optional[str]: File contents as string, None if error occurred
            
        Raises:
            ClientError: If S3 operation fails
            UnicodeDecodeError: If file encoding is incorrect
        """
        try:
            logger.info(f"Loading file '{file_key}' from bucket '{bucket_name}'")
            
            # Check if bucket exists and is accessible
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    logger.error(f"Bucket '{bucket_name}' does not exist or is not accessible")
                elif error_code == '403':
                    logger.error(f"Access denied to bucket '{bucket_name}'. Check permissions.")
                else:
                    logger.error(f"Error accessing bucket '{bucket_name}': {e}")
                return None
            
            # Check if object exists
            try:
                self.s3_client.head_object(Bucket=bucket_name, Key=file_key)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    logger.error(f"File '{file_key}' not found in bucket '{bucket_name}'")
                else:
                    logger.error(f"Error accessing file '{file_key}': {e}")
                return None
            
            # Download and read the file
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
            file_content = response['Body'].read()
            
            # Decode content
            try:
                decoded_content = file_content.decode(encoding)
                logger.info(f"Successfully loaded {len(decoded_content)} characters from '{file_key}'")
                return decoded_content
                
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode file with encoding '{encoding}': {e}")
                logger.info("Trying alternative encodings...")
                
                # Try alternative encodings
                for alt_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        decoded_content = file_content.decode(alt_encoding)
                        logger.info(f"Successfully decoded with encoding '{alt_encoding}'")
                        return decoded_content
                    except UnicodeDecodeError:
                        continue
                
                logger.error("Failed to decode file with any common encoding")
                return None
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS S3 error ({error_code}): {error_message}")
            return None
            
        except BotoCoreError as e:
            logger.error(f"BotoCore error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error loading file from S3: {e}")
            return None
    
    def get_file_metadata(self, bucket_name: str, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata information about a file in S3.
        
        Args:
            bucket_name: Name of the S3 bucket
            file_key: S3 object key (path to the file)
            
        Returns:
            Optional[Dict[str, Any]]: File metadata, None if error occurred
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=file_key)
            metadata = {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
            logger.info(f"Retrieved metadata for '{file_key}': {metadata['size']} bytes")
            return metadata
            
        except ClientError as e:
            logger.error(f"Failed to get metadata for '{file_key}': {e}")
            return None


def main():
    """
    CLI test script to demonstrate S3 data loading functionality.
    """
    parser = argparse.ArgumentParser(
        description='Load and preview medical research abstracts from AWS S3'
    )
    parser.add_argument('bucket_name', help='S3 bucket name')
    parser.add_argument('file_key', help='S3 object key (file path)')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--encoding', default='utf-8', help='File encoding (default: utf-8)')
    parser.add_argument('--preview-chars', type=int, default=500, 
                       help='Number of characters to preview (default: 500)')
    parser.add_argument('--test-connection', action='store_true', 
                       help='Test S3 connection before loading data')
    parser.add_argument('--no-secrets-manager', action='store_true',
                       help='Skip AWS Secrets Manager and use environment variables only')
    parser.add_argument('--secret-name', default='research-gap-app/secrets',
                       help='Name of the secret in AWS Secrets Manager (default: research-gap-app/secrets)')
    
    args = parser.parse_args()
    
    try:
        print("=== Medical Research Gap Analysis - S3 Data Loader ===\n")
        
        # Initialize S3 loader
        loader = S3DataLoader(
            region_name=args.region,
            use_secrets_manager=not args.no_secrets_manager,
            secret_name=args.secret_name
        )
        
        # Test connection if requested
        if args.test_connection:
            print("Testing S3 connection...")
            if not loader.test_connection():
                print("❌ S3 connection test failed. Exiting.")
                sys.exit(1)
            print("✅ S3 connection test successful\n")
        
        # Get file metadata
        print(f"Getting metadata for s3://{args.bucket_name}/{args.file_key}")
        metadata = loader.get_file_metadata(args.bucket_name, args.file_key)
        if metadata:
            print(f"📊 File size: {metadata['size']:,} bytes")
            print(f"📅 Last modified: {metadata['last_modified']}")
            print(f"📄 Content type: {metadata['content_type']}\n")
        
        # Load the file
        print("Loading abstracts from S3...")
        content = loader.load_abstracts_from_s3(
            args.bucket_name, 
            args.file_key, 
            args.encoding
        )
        
        if content is None:
            print("❌ Failed to load data from S3")
            sys.exit(1)
        
        # Display preview
        print(f"✅ Successfully loaded {len(content):,} characters")
        print(f"\n=== Preview (first {args.preview_chars} characters) ===")
        print("-" * 60)
        print(content[:args.preview_chars])
        
        if len(content) > args.preview_chars:
            print("\n[... content truncated ...]")
        
        print("-" * 60)
        print(f"Total characters: {len(content):,}")
        print(f"Total lines: {content.count(chr(10)) + 1:,}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Unexpected error in main()")
        sys.exit(1)


if __name__ == "__main__":
    main()
