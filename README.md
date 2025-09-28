# Medical Research Gap Analysis Tool
<img width="899" height="994" alt="Screenshot 2025-09-27 at 10 23 13 PM" src="https://github.com/user-attachments/assets/78bc6007-e5bf-4cf0-9d35-e4efdd2316bf" />
<img width="660" height="676" alt="Screenshot 2025-09-27 at 10 24 21 PM" src="https://github.com/user-attachments/assets/4315d374-d458-49c7-a9e5-3df533fb87a7" />



A Python-based tool for analyzing research gaps in medical literature using AWS S3, BERTopic, and in-memory storage.

## Overview

This tool loads medical research abstracts from AWS S3, uses BERTopic for topic modeling and research gap analysis, stores the data in memory, and provides interactive visualizations through word clouds organized by year and topic.

## Features

- **S3 Data Loading**: Secure loading of medical research abstracts from AWS S3
- **Advanced Topic Modeling**: Uses BERTopic with enhanced stop word filtering for medical domain
- **Interactive Visualizations**: 5 types of interactive HTML visualizations
  - **Topic Overview**: Interactive scatter plot with hover details and zoom
  - **Topic Keywords**: Interactive bar charts showing keyword relevance scores
  - **Similarity Heatmap**: Interactive heatmap showing topic relationships
  - **Document Distribution**: Visualization of document-topic assignments
  - **Topic Hierarchy**: Hierarchical view of topic relationships
- **Enhanced Text Processing**: 200+ medical/research stop words for better topic extraction
- **Complete Pipeline**: Automated 5-step process from S3 to visualizations
- **CSV Export**: Structured topic assignments and analysis results
- **Security First**: Environment variable-based credential management
- **Modular Design**: Clean separation of concerns across components

## Quick Start

### Prerequisites
- AWS Account with S3 access
- Python 3.8+ (no database required - uses in-memory storage)

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

#### Complete Research Gap Analysis Pipeline

Run the full pipeline to analyze medical research abstracts and generate interactive visualizations:

```bash
# Run complete pipeline: S3 → Parsing → BERTopic → Visualizations
python research_gap_pipeline.py
```

This will:
1. Load abstracts from S3 (bucket: `research-gap`, file: `abstract-artificial-set.txt`)
2. Parse multiple abstracts using numbered citation detection
3. Extract themes using BERTopic with medical stop word filtering
4. Export results to CSV files in `data/` directory
5. Generate interactive HTML visualizations in `data/visualizations/`

#### Individual Component Usage

```bash
# Test S3 connection and load abstracts
python scripts/s3_load.py your-bucket-name path/to/abstracts.txt --test-connection

# Preview first 500 characters
python scripts/s3_load.py your-bucket-name path/to/abstracts.txt --preview-chars 500
```

#### Python API Usage

```python
# Complete pipeline usage
from research_gap_pipeline import ResearchGapPipeline

pipeline = ResearchGapPipeline(
    bucket_name="research-gap",
    file_key="abstract-artificial-set.txt",
    output_dir="data"
)

# Run full analysis
success = pipeline.run_full_pipeline()

# Open visualizations in browser
if success:
    pipeline.open_visualizations()
```

```python
# Individual component usage
from scripts.s3_load import S3DataLoader
from scripts.abstract_parser import parse_abstract_text
from scripts.theme_model import extract_themes, create_topic_visualizations

# Load and parse abstracts
loader = S3DataLoader(region_name='us-east-1')
raw_text = loader.load_abstracts_from_s3('your-bucket', 'abstracts.txt')
abstracts = parse_abstract_text(raw_text)

# Extract themes and create visualizations
docs = [f"{abs.title}. {abs.abstract_text}" for abs in abstracts]
topic_model, topics, probs = extract_themes(docs)
viz_files = create_topic_visualizations(topic_model, docs, topics, "visualizations/")
```

## Project Structure

### Core Pipeline
- `research_gap_pipeline.py` - **Main pipeline orchestrator** with 5-step process
- `scripts/theme_model.py` - **BERTopic analysis** with interactive visualizations
- `scripts/abstract_parser.py` - **Medical abstract parsing** with numbered citation support
- `scripts/s3_load.py` - **AWS S3 data loading** with error handling

### Data & Output
- `data/` - **Output directory** containing:
  - `research_gap_abstracts_with_themes.csv` - Abstracts with topic assignments
  - `research_gap_topic_info_documents.csv` - Document-level topic data
  - `research_gap_topic_info_summary.csv` - Topic summary with keywords
  - `visualizations/` - **Interactive HTML visualizations**:
    - `index.html` - Navigation page for all visualizations
    - `topics_overview.html` - Interactive topic scatter plot
    - `topics_barchart.html` - Keyword relevance bar charts
    - `topics_heatmap.html` - **Topic similarity heatmap**
    - `documents_overview.html` - Document distribution visualization
    - `topics_hierarchy.html` - Topic relationship hierarchy

### Configuration & Testing
- `scripts/data_store.py` - In-memory data storage implementation
- `scripts/setup_secrets.py` - AWS Secrets Manager configuration
- `tests/` - Test suite for all components
- `requirements.txt` - Python dependencies including visualization packages
- `.env.example` - Environment variable template

## Security

- All AWS credentials are managed via environment variables
- No hardcoded secrets in codebase
- Secure credential chain support (IAM roles, AWS profiles)

## Output & Visualizations

After running the pipeline, you'll get:

### CSV Files
- **Abstracts with Topics**: Each abstract labeled with its dominant topic and keywords
- **Topic Summary**: Overview of all discovered topics with keyword relevance scores
- **Document Analysis**: Detailed document-topic relationships

### Interactive Visualizations
Navigate to `data/visualizations/index.html` or run `pipeline.open_visualizations()` to explore:

1. **📊 Topic Overview**: Interactive scatter plot showing topic relationships in 2D space
2. **� Keyword Bar Charts**: Interactive bars showing most relevant terms per topic  
3. **🔥 Similarity Heatmap**: Interactive heatmap revealing which topics are most similar
4. **� Document Distribution**: How documents cluster around different topics
5. **🌳 Topic Hierarchy**: Tree-like view of how topics relate at different levels

All visualizations support zooming, hovering for details, and interactive exploration.

### Sample Topic Results

The enhanced BERTopic analysis now identifies meaningful medical research themes like:

- **Cognitive Robotics & AI**: `cognitive; robot; robots; humans; neuroscience; brain; agents`
- **Cardiovascular Medicine**: `cardiovascular; ecg; heart; cardiac; cardiology; mortality`
- **Drug Discovery**: `drug; discovery; molecular; graph; chemical; pharmaceutical`
- **Ophthalmology**: `ophthalmology; eye; glaucoma; singapore; dr; images; oct`
- **Dental AI**: `dental; dentistry; oral; radiographs; images; segmentation`
- **Medical Imaging**: `radiology; imaging; radiologists; diagnostic; reports`

The similarity heatmap reveals relationships between these topics, helping identify research gaps and cross-disciplinary opportunities.

## Development Status

Development progress with delivered features:

1. ✅ **S3 Data Loading** - Secure AWS integration with connection testing
2. ✅ **Abstract Parsing** - Multi-abstract parsing with numbered citation detection  
3. ✅ **BERTopic Integration** - Advanced topic modeling with medical stop words
4. ✅ **Interactive Visualizations** - 5 types of HTML visualizations including heatmaps
5. ✅ **Complete Pipeline** - End-to-end automation from S3 to visualizations
6. 🔄 **Advanced Analytics** - Research gap identification and trend analysis

## Contributing

Please ensure all code follows security best practices and includes appropriate error handling and logging.
