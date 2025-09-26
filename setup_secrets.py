#!/usr/bin/env python3
"""
AWS Secrets Manager Setup Script for Research Gap Analysis Tool

This script helps you create and manage secrets in AWS Secrets Manager
for secure credential storage.
"""

import json
import boto3
import argparse
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_secret(secret_name: str, aws_access_key_id: str, aws_secret_access_key: str, 
                 region_name: str = 'us-east-1', description: str = None) -> bool:
    """
    Create a new secret in AWS Secrets Manager.
    
    Args:
        secret_name: Name for the secret
        aws_access_key_id: AWS access key ID to store
        aws_secret_access_key: AWS secret access key to store
        region_name: AWS region
        description: Optional description for the secret
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create Secrets Manager client
        client = boto3.client('secretsmanager', region_name=region_name)
        
        # Prepare secret value as JSON
        secret_value = {
            "AWS_ACCESS_KEY_ID": aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": aws_secret_access_key
        }
        
        # Create the secret
        response = client.create_secret(
            Name=secret_name,
            Description=description or f"AWS credentials for Research Gap Analysis Tool",
            SecretString=json.dumps(secret_value)
        )
        
        logger.info(f"✅ Secret '{secret_name}' created successfully")
        logger.info(f"   ARN: {response['ARN']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceExistsException':
            logger.error(f"❌ Secret '{secret_name}' already exists")
            return False
        else:
            logger.error(f"❌ Failed to create secret: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def update_secret(secret_name: str, aws_access_key_id: str, aws_secret_access_key: str,
                 region_name: str = 'us-east-1') -> bool:
    """
    Update an existing secret in AWS Secrets Manager.
    
    Args:
        secret_name: Name of the existing secret
        aws_access_key_id: New AWS access key ID
        aws_secret_access_key: New AWS secret access key
        region_name: AWS region
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create Secrets Manager client
        client = boto3.client('secretsmanager', region_name=region_name)
        
        # Prepare secret value as JSON
        secret_value = {
            "AWS_ACCESS_KEY_ID": aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": aws_secret_access_key
        }
        
        # Update the secret
        client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secret_value)
        )
        
        logger.info(f"✅ Secret '{secret_name}' updated successfully")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            logger.error(f"❌ Secret '{secret_name}' not found")
            return False
        else:
            logger.error(f"❌ Failed to update secret: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def get_secret_info(secret_name: str, region_name: str = 'us-east-1') -> bool:
    """
    Get information about an existing secret.
    
    Args:
        secret_name: Name of the secret
        region_name: AWS region
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create Secrets Manager client
        client = boto3.client('secretsmanager', region_name=region_name)
        
        # Get secret metadata
        response = client.describe_secret(SecretId=secret_name)
        
        print(f"\n📋 Secret Information:")
        print(f"   Name: {response['Name']}")
        print(f"   ARN: {response['ARN']}")
        print(f"   Description: {response.get('Description', 'N/A')}")
        print(f"   Created: {response['CreatedDate']}")
        print(f"   Last Modified: {response.get('LastChangedDate', 'N/A')}")
        
        # Test retrieving the secret value
        secret_response = client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(secret_response['SecretString'])
        
        print(f"   Contains keys: {list(secret_data.keys())}")
        print(f"   ✅ Secret is accessible and properly formatted")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            logger.error(f"❌ Secret '{secret_name}' not found")
            return False
        else:
            logger.error(f"❌ Failed to get secret info: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def main():
    """
    Main CLI function for managing AWS Secrets Manager secrets.
    """
    parser = argparse.ArgumentParser(
        description='Manage AWS Secrets Manager secrets for Research Gap Analysis Tool'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create secret command
    create_parser = subparsers.add_parser('create', help='Create a new secret')
    create_parser.add_argument('--name', default='research-gap-app/secrets',
                              help='Secret name (default: research-gap-app/secrets)')
    create_parser.add_argument('--access-key', required=True,
                              help='AWS Access Key ID')
    create_parser.add_argument('--secret-key', required=True,
                              help='AWS Secret Access Key')
    create_parser.add_argument('--region', default='us-east-1',
                              help='AWS region (default: us-east-1)')
    create_parser.add_argument('--description',
                              help='Description for the secret')
    
    # Update secret command
    update_parser = subparsers.add_parser('update', help='Update an existing secret')
    update_parser.add_argument('--name', default='research-gap-app/secrets',
                              help='Secret name (default: research-gap-app/secrets)')
    update_parser.add_argument('--access-key', required=True,
                              help='New AWS Access Key ID')
    update_parser.add_argument('--secret-key', required=True,
                              help='New AWS Secret Access Key')
    update_parser.add_argument('--region', default='us-east-1',
                              help='AWS region (default: us-east-1)')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get information about a secret')
    info_parser.add_argument('--name', default='research-gap-app/secrets',
                            help='Secret name (default: research-gap-app/secrets)')
    info_parser.add_argument('--region', default='us-east-1',
                            help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("=== AWS Secrets Manager Setup Tool ===\n")
    
    try:
        if args.command == 'create':
            success = create_secret(
                args.name, 
                args.access_key, 
                args.secret_key,
                args.region,
                args.description
            )
            
        elif args.command == 'update':
            success = update_secret(
                args.name,
                args.access_key,
                args.secret_key,
                args.region
            )
            
        elif args.command == 'info':
            success = get_secret_info(args.name, args.region)
        
        if success:
            print(f"\n🎉 Operation completed successfully!")
            if args.command in ['create', 'update']:
                print(f"\nNext steps:")
                print(f"1. Test the S3 loader with Secrets Manager:")
                print(f"   python s3_load.py your-bucket file-key --secret-name {args.name}")
                print(f"2. The loader will automatically use Secrets Manager by default")
        else:
            print(f"\n❌ Operation failed")
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
