# Medical Research Gap Analysis Tool

A Python-based tool for analyzing research gaps in medical literature using AWS S3, OpenAI GPT, and PostgreSQL.

## Overview

This tool loads medical research abstracts from AWS S3, uses LLMs to extract research gaps, stores the data in PostgreSQL, and provides interactive visualizations through word clouds organized by year and topic.

## Features

- **S3 Data Loading**: Secure loading of medical research abstracts from AWS S3
- **LLM Integration**: Uses OpenAI GPT for intelligent gap extraction
- **Database Storage**: PostgreSQL backend for structured data storage
- **Interactive Visualization**: Dash/Streamlit frontend with word clouds
- **Security First**: Environment variable-based credential management
- **Modular Design**: Clean separation of concerns across components

## Quick Start

### Prerequisites

- Python 3.8+
- AWS Account with S3 access
- PostgreSQL database
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gap_cloud
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### Usage

#### Loading Data from S3

```bash
# Test S3 connection and load abstracts
python s3_load.py your-bucket-name path/to/abstracts.txt --test-connection

# Preview first 500 characters
python s3_load.py your-bucket-name path/to/abstracts.txt --preview-chars 500
```

#### Python API Usage

```python
from s3_load import S3DataLoader

# Initialize loader
loader = S3DataLoader(region_name='us-east-1')

# Load abstracts
content = loader.load_abstracts_from_s3('your-bucket', 'abstracts.txt')
print(f"Loaded {len(content)} characters")
```

## Project Structure

- `s3_load.py` - AWS S3 data loading with error handling
- `test_s3_load.py` - Simple test script for S3 functionality
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template

## Security

- All AWS credentials are managed via environment variables
- No hardcoded secrets in codebase
- Secure credential chain support (IAM roles, AWS profiles)

## Development

This project follows incremental development with PR-based deliverables:

1. ✅ S3 data loading implementation
2. 🔄 Abstract parsing and structuring
3. 🔄 LLM integration for gap extraction
4. 🔄 PostgreSQL database setup
5. 🔄 Interactive frontend development

## Contributing

Please ensure all code follows security best practices and includes appropriate error handling and logging.
