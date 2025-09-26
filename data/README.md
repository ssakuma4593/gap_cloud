# Data Directory

This directory is for storing data files used by the Gap Cloud application.

**Note**: Data files should not be committed to version control. The `.gitignore` file excludes common data file formats.

## Directory Structure

- `raw/` - Raw research data (excluded from git)
- `processed/` - Processed and cleaned data (excluded from git)
- `sample/` - Sample data for testing and development (can be committed)

## Data Sources

The application supports various data sources:
- Academic paper databases
- Research repositories
- CSV/JSON files
- PostgreSQL databases
- Cloud storage (AWS S3)