# Gap Cloud

A research gap visualization tool that creates interactive word clouds from identified gaps in academic research, encouraging researchers to explore and fill these gaps.

## Project Overview

Gap Cloud is designed to help researchers and academics:
- Identify research gaps in their field of study
- Visualize gaps as interactive word clouds
- Encourage collaboration and research direction
- Provide data-driven insights into underexplored research areas

## Features

- **Gap Analysis**: Automated analysis of research literature to identify gaps
- **Word Cloud Generation**: Interactive visualization of research gaps
- **Data Integration**: Support for multiple data sources including databases and cloud storage
- **Research Insights**: AI-powered analysis of research trends and opportunities

## Project Structure

```
gap_cloud/
├── app/                    # Main application code
├── scripts/               # Utility scripts and data processing
├── data/                  # Data files (excluded from git)
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Technology Stack

- **Python 3.8+**: Core programming language
- **Pandas**: Data manipulation and analysis
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Database (via psycopg2-binary)
- **OpenAI**: AI-powered text analysis
- **AWS (Boto3)**: Cloud storage and services

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL database (optional, for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ssakuma4593/gap_cloud.git
   cd gap_cloud
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (create a `.env` file)
   ```bash
   # Database configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/gap_cloud
   
   # OpenAI API key
   OPENAI_API_KEY=your_openai_api_key_here
   
   # AWS credentials (if using AWS services)
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_DEFAULT_REGION=us-east-1
   ```

### Quick Start

1. **Verify installation**
   ```bash
   python -c "import pandas, sqlalchemy, openai, boto3; print('All dependencies installed successfully!')"
   ```

2. **Run tests** (when available)
   ```bash
   python -m pytest tests/
   ```

## Development

### Project Philosophy

This project follows minimal change principles:
- Make surgical, precise modifications
- Preserve existing functionality
- Focus on the core requirements

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or collaboration opportunities, please open an issue on GitHub.
