#!/usr/bin/env python3
"""
Theme Model for Medical Research Gap Analysis Tool

This module provides functionality to extract themes and topics from medical
research abstracts using BERTopic, a topic modeling technique that leverages
transformer models and clustering algorithms.

The main function extract_themes() takes a list of document texts and returns:
- A fitted BERTopic model
- Topic assignments for each document
- Topic probabilities for each document

Additional functionality includes:
- Printing topic information to console
- Saving topic information to CSV files
- Integration with abstract parser output
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from pathlib import Path

# BERTopic and related imports
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer

# Import local modules
from scripts.abstract_parser import AbstractRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_enhanced_stop_words() -> List[str]:
    """
    Get an enhanced list of stop words including medical research common terms.
    
    Returns:
        List[str]: Extended stop words list
    """
    # Start with sklearn's English stop words
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    
    # Common English stopwords plus medical/research specific ones
    additional_stopwords = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
        "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
        "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", 
        "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", 
        "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", 
        "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", 
        "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", 
        "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", 
        "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", 
        "the", "their", "theirs", "them", "themselves", "then", "there", "there's", 
        "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", 
        "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", 
        "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", 
        "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", 
        "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", 
        "you've", "your", "yours", "yourself", "yourselves",
        # Research/academic terms
        "prove", "paper", "show", "result", "results", "consider", "using", "use", "used", "given", "thus",
        "therefore", "hence", "obtain", "propose", "method", "methods", "approach", "approaches",
        "introduce", "study", "studies", "analyze", "present", "develop", "data", "set", "model", "models",
        "equation", "function", "theorem", "lemma", "define", "definition", "analysis", "research",
        "example", "problem", "solution", "property", "application", "system", "network", "learning", "classification", 
        "optimization", "performance", "experimental", "evaluation", "dataset", "findings", "finding",
        "training", "testing", "validation", "accuracy", "precision", "recall", "patient", "patients",
        "clinical", "medical", "medicine", "healthcare", "health", "treatment", "therapy", "diagnosis",
        "disease", "condition", "outcome", "outcomes", "effectiveness", "efficacy", "significant", "significantly",
        "associated", "correlation", "relationship", "compared", "comparison", "group", "groups", "control",
        "trial", "trials", "randomized", "participants", "subjects", "population", "sample", "samples",
        "measured", "measurement", "assessed", "assessment", "evaluated", "examined", "investigated",
        "observed", "found", "showed", "demonstrated", "indicated", "suggested", "revealed", "identified",
        "determined", "concluded", "conclusion", "conclusions", "background", "objective", "objectives",
        "aim", "aims", "goal", "goals", "purpose", "conducted", "performed", "implemented", "applied"
    }
    
    # Combine with sklearn stop words
    combined_stops = list(ENGLISH_STOP_WORDS.union(additional_stopwords))
    
    logger.info(f"Using {len(combined_stops)} stop words for text preprocessing")
    return combined_stops


def extract_themes(docs: List[str]) -> Tuple[BERTopic, List[int], np.ndarray]:
    """
    Extract themes from documents using BERTopic.
    
    Args:
        docs: List of document texts to analyze
        
    Returns:
        Tuple containing:
        - topic_model: Fitted BERTopic model
        - topics: List of topic assignments for each document
        - probs: Array of topic probabilities for each document
    """
    logger.info(f"Starting theme extraction on {len(docs)} documents")
    
    # Handle small document sets
    if len(docs) < 5:
        logger.warning(f"Only {len(docs)} documents provided. BERTopic works best with 20+ documents.")
        logger.info("Using simplified configuration for small document sets.")
        
        # Configure BERTopic for small datasets
        # Reduce minimum cluster size and use smaller embeddings
        umap_model = UMAP(
            n_neighbors=min(2, len(docs)-1),  # Must be smaller than number of documents
            n_components=min(2, len(docs)-1),  # Reduce dimensionality for small datasets
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )
        
        hdbscan_model = HDBSCAN(
            min_cluster_size=2,  # Minimum cluster size
            min_samples=1,       # Minimum samples in cluster
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )
        
        # Use enhanced vectorizer for small datasets with medical stop words
        custom_stop_words = _get_enhanced_stop_words()
        vectorizer_model = CountVectorizer(
            ngram_range=(1, 3),  # Include trigrams for medical terms
            stop_words=custom_stop_words,
            min_df=1,  # Allow words that appear in at least 1 document
            max_df=0.95,  # Remove words that appear in >95% of documents
            max_features=200,
            token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b'  # Only alphabetic tokens, minimum 2 chars
        )
        
        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            verbose=True
        )
    else:
        # Enhanced configuration for larger datasets
        custom_stop_words = _get_enhanced_stop_words()
        vectorizer_model = CountVectorizer(
            ngram_range=(1, 3),  # Include trigrams for medical terms
            stop_words=custom_stop_words,
            min_df=2,  # Word must appear in at least 2 documents
            max_df=0.85,  # Remove words that appear in >85% of documents
            max_features=1000,
            token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b'  # Only alphabetic tokens, minimum 2 chars
        )
        
        topic_model = BERTopic(
            vectorizer_model=vectorizer_model,
            verbose=True
        )
    
    logger.info("Fitting BERTopic model...")
    
    try:
        topics, probs = topic_model.fit_transform(docs)
    except Exception as e:
        logger.error(f"BERTopic fitting failed: {e}")
        # Fallback: assign all documents to single topic
        logger.warning("Falling back to single topic assignment")
        topics = [0] * len(docs)
        probs = np.ones((len(docs), 1))  # All documents have probability 1.0 for topic 0
        
        # Create a minimal topic model for compatibility
        topic_model = BERTopic(verbose=False)
        # Set up minimal topic info for fallback
        topic_model.topic_representations_ = {
            0: [("document", 1.0), ("text", 0.8), ("medical", 0.6), ("research", 0.5), ("analysis", 0.4)]
        }
        topic_model.topics_ = topics
    
    logger.info(f"Completed theme extraction. Found {len(set(topics))} topics")
    return topic_model, topics, probs


def print_topic_info(topic_model: BERTopic, topics: List[int], docs: List[str]) -> None:
    """
    Print topic information to console in a readable format.
    
    Args:
        topic_model: Fitted BERTopic model
        topics: Topic assignments for each document
        docs: Original document texts
    """
    print("\n" + "="*80)
    print("TOPIC EXTRACTION RESULTS")
    print("="*80)
    
    # Get topic info
    topic_info = topic_model.get_topic_info()
    
    print(f"\nTotal number of topics found: {len(topic_info)}")
    print(f"Total number of documents: {len(docs)}")
    
    # Print overview of topics
    print("\nTOPIC OVERVIEW:")
    print("-" * 50)
    for idx, row in topic_info.iterrows():
        topic_id = row['Topic']
        count = row['Count']
        
        # Get top words for this topic
        if topic_id == -1:
            topic_words = "Outliers/Noise"
        else:
            top_words = topic_model.get_topic(topic_id)
            topic_words = ", ".join([word for word, _ in top_words[:5]])
        
        print(f"Topic {topic_id:2d}: {count:4d} docs | {topic_words}")
    
    # Print detailed topic information
    print("\nDETAILED TOPIC INFORMATION:")
    print("-" * 50)
    
    for topic_id in sorted(topic_info['Topic'].unique()):
        if topic_id == -1:  # Skip outliers for detailed view
            continue
            
        print(f"\nTopic {topic_id}:")
        topic_words = topic_model.get_topic(topic_id)
        
        # Print top words with scores
        print("  Top words:")
        for word, score in topic_words[:10]:
            print(f"    {word:<15} (score: {score:.4f})")
        
        # Print sample documents from this topic
        topic_docs = [docs[i] for i, t in enumerate(topics) if t == topic_id]
        if topic_docs:
            print("  Sample document:")
            sample_doc = topic_docs[0][:200] + "..." if len(topic_docs[0]) > 200 else topic_docs[0]
            print(f"    {sample_doc}")


def save_topic_info_to_csv(topic_model: BERTopic, 
                          topics: List[int], 
                          docs: List[str],
                          output_path: str = "themes.csv") -> None:
    """
    Save topic information to a CSV file.
    
    Args:
        topic_model: Fitted BERTopic model
        topics: Topic assignments for each document
        docs: Original document texts
        output_path: Path to save the CSV file
    """
    logger.info(f"Saving topic information to {output_path}")
    
    # Create document-level data
    doc_data = []
    for i, (doc, topic_id) in enumerate(zip(docs, topics)):
        doc_data.append({
            'document_id': i,
            'topic_id': topic_id,
            'document_text': doc,
            'document_length': len(doc)
        })
    
    # Convert to DataFrame
    doc_df = pd.DataFrame(doc_data)
    
    # Get topic information
    topic_info = topic_model.get_topic_info()
    
    # Create topic summary data
    topic_summary = []
    for _, row in topic_info.iterrows():
        topic_id = row['Topic']
        count = row['Count']
        
        if topic_id == -1:
            top_words = "Outliers/Noise"
            word_scores = ""
        else:
            topic_words = topic_model.get_topic(topic_id)
            top_words = "; ".join([word for word, _ in topic_words[:10]])
            word_scores = "; ".join([f"{word}:{score:.4f}" for word, score in topic_words[:10]])
        
        topic_summary.append({
            'topic_id': topic_id,
            'document_count': count,
            'top_words': top_words,
            'word_scores': word_scores
        })
    
    topic_summary_df = pd.DataFrame(topic_summary)
    
    # Save to CSV files
    base_path = Path(output_path)
    doc_path = base_path.parent / f"{base_path.stem}_documents.csv"
    summary_path = base_path.parent / f"{base_path.stem}_summary.csv"
    
    doc_df.to_csv(doc_path, index=False)
    topic_summary_df.to_csv(summary_path, index=False)
    
    logger.info(f"Saved document-level data to: {doc_path}")
    logger.info(f"Saved topic summary to: {summary_path}")


def extract_themes_from_abstracts(abstract_records: List[AbstractRecord],
                                 text_field: str = 'abstract_text') -> Tuple[BERTopic, List[int], np.ndarray]:
    """
    Extract themes from AbstractRecord objects.
    
    Args:
        abstract_records: List of AbstractRecord objects from abstract_parser
        text_field: Field to use for text extraction ('abstract_text', 'title', or 'combined')
        
    Returns:
        Tuple containing:
        - topic_model: Fitted BERTopic model
        - topics: List of topic assignments for each document
        - probs: Array of topic probabilities for each document
    """
    logger.info(f"Extracting themes from {len(abstract_records)} abstract records using field: {text_field}")
    
    # Extract text based on specified field
    docs = []
    for record in abstract_records:
        if text_field == 'abstract_text':
            text = record.abstract_text
        elif text_field == 'title':
            text = record.title
        elif text_field == 'combined':
            text = f"{record.title}. {record.abstract_text}"
        else:
            raise ValueError(f"Invalid text_field: {text_field}. Must be 'abstract_text', 'title', or 'combined'")
        
        docs.append(text)
    
    return extract_themes(docs)


def save_abstracts_with_topics(abstract_records: List[AbstractRecord],
                              topics: List[int],
                              topic_model: BERTopic,
                              output_path: str = "abstracts_with_themes.csv") -> None:
    """
    Save abstract records with their assigned topics to CSV.
    
    Args:
        abstract_records: List of AbstractRecord objects
        topics: Topic assignments for each abstract
        topic_model: Fitted BERTopic model
        output_path: Path to save the CSV file
    """
    logger.info(f"Saving abstracts with topic assignments to {output_path}")
    
    # Convert abstracts to records with topic information
    data = []
    for record, topic_id in zip(abstract_records, topics):
        # Get top words for this topic
        if topic_id == -1:
            topic_words = "Outliers/Noise"
        else:
            top_words = topic_model.get_topic(topic_id)
            topic_words = "; ".join([word for word, _ in top_words[:5]])
        
        data.append({
            'title': record.title,
            'authors': "; ".join(record.authors) if record.authors else "",
            'year': record.year,
            'journal': record.journal,
            'topic_id': topic_id,
            'topic_keywords': topic_words,
            'abstract_text': record.abstract_text,
            'doi': record.doi,
            'pmid': record.pmid
        })
    
    # Save to CSV
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(data)} abstracts with topic assignments to: {output_path}")


def create_topic_visualizations(topic_model: BERTopic, 
                               docs: List[str],
                               topics: List[int],
                               output_dir: str = "visualizations") -> Dict[str, str]:
    """
    Create interactive BERTopic visualizations and save as HTML files.
    
    Args:
        topic_model: Fitted BERTopic model
        docs: Original document texts used for training
        topics: Topic assignments for each document
        output_dir: Directory to save visualization HTML files
        
    Returns:
        Dictionary with visualization names as keys and file paths as values
    """
    import os
    
    logger.info("Creating BERTopic interactive visualizations...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    visualization_files = {}
    
    try:
        # 1. Topic visualization - interactive scatter plot with hover info
        logger.info("Creating topic overview visualization...")
        topics_fig = topic_model.visualize_topics()
        topics_html = output_path / "topics_overview.html"
        topics_fig.write_html(str(topics_html))
        visualization_files["topics_overview"] = str(topics_html)
        logger.info(f"✅ Saved topics overview to: {topics_html}")
        
    except Exception as e:
        logger.warning(f"Failed to create topics overview: {e}")
    
    try:
        # 2. Bar chart visualization - keywords per topic
        logger.info("Creating topic bar charts...")
        
        # Get unique topics (excluding outliers if present)
        unique_topics = sorted([t for t in set(topics) if t != -1])
        
        # Create bar chart for top topics
        top_topics = unique_topics[:10] if len(unique_topics) > 10 else unique_topics
        
        if top_topics:
            barchart_fig = topic_model.visualize_barchart(topics=top_topics)
            barchart_html = output_path / "topics_barchart.html"
            barchart_fig.write_html(str(barchart_html))
            visualization_files["barchart"] = str(barchart_html)
            logger.info(f"✅ Saved topic bar chart to: {barchart_html}")
        else:
            logger.warning("No valid topics found for bar chart visualization")
            
    except Exception as e:
        logger.warning(f"Failed to create bar chart: {e}")
    
    try:
        # 3. Heatmap visualization - similarity between topics
        logger.info("Creating topic similarity heatmap...")
        
        # Only create heatmap if we have multiple topics
        unique_topics = [t for t in set(topics) if t != -1]
        if len(unique_topics) > 1:
            heatmap_fig = topic_model.visualize_heatmap()
            heatmap_html = output_path / "topics_heatmap.html"
            heatmap_fig.write_html(str(heatmap_html))
            visualization_files["heatmap"] = str(heatmap_html)
            logger.info(f"✅ Saved topic heatmap to: {heatmap_html}")
        else:
            logger.warning("Not enough topics for heatmap visualization (need 2+)")
            
    except Exception as e:
        logger.warning(f"Failed to create heatmap: {e}")
    
    try:
        # 4. Document visualization - how documents relate to topics
        logger.info("Creating document visualization...")
        documents_fig = topic_model.visualize_documents(docs)
        documents_html = output_path / "documents_overview.html"
        documents_fig.write_html(str(documents_html))
        visualization_files["documents"] = str(documents_html)
        logger.info(f"✅ Saved documents overview to: {documents_html}")
        
    except Exception as e:
        logger.warning(f"Failed to create documents visualization: {e}")
    
    try:
        # 5. Hierarchy visualization - topic relationships
        logger.info("Creating topic hierarchy visualization...")
        
        if len(set(topics)) > 2:  # Need multiple topics for hierarchy
            hierarchy_fig = topic_model.visualize_hierarchy()
            hierarchy_html = output_path / "topics_hierarchy.html"
            hierarchy_fig.write_html(str(hierarchy_html))
            visualization_files["hierarchy"] = str(hierarchy_html)
            logger.info(f"✅ Saved topic hierarchy to: {hierarchy_html}")
        else:
            logger.warning("Not enough topics for hierarchy visualization")
            
    except Exception as e:
        logger.warning(f"Failed to create hierarchy visualization: {e}")
    
    # Summary
    logger.info(f"✅ Created {len(visualization_files)} visualizations in {output_dir}/")
    for name, path in visualization_files.items():
        file_size = Path(path).stat().st_size / 1024  # KB
        logger.info(f"  📊 {name}: {Path(path).name} ({file_size:.1f} KB)")
    
    return visualization_files


def open_visualizations_in_browser(visualization_files: Dict[str, str]) -> None:
    """
    Open all visualization HTML files in the default web browser.
    
    Args:
        visualization_files: Dictionary with visualization names and file paths
    """
    import webbrowser
    
    logger.info("Opening visualizations in web browser...")
    
    for name, file_path in visualization_files.items():
        try:
            # Convert to file:// URL for proper browser opening
            file_url = f"file://{os.path.abspath(file_path)}"
            webbrowser.open(file_url)
            logger.info(f"✅ Opened {name} visualization")
        except Exception as e:
            logger.warning(f"Failed to open {name}: {e}")


def create_visualization_summary(visualization_files: Dict[str, str], 
                                output_dir: str = "visualizations") -> str:
    """
    Create an HTML index page linking to all visualizations.
    
    Args:
        visualization_files: Dictionary with visualization names and file paths
        output_dir: Directory containing visualizations
        
    Returns:
        Path to the index HTML file
    """
    logger.info("Creating visualization index page...")
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>BERTopic Visualizations - Research Gap Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .viz-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .viz-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: #fafafa; transition: transform 0.2s; }
        .viz-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .viz-card h3 { color: #2c3e50; margin-top: 0; }
        .viz-card p { color: #666; margin: 10px 0; }
        .viz-link { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px; }
        .viz-link:hover { background: #2980b9; }
        .description { background: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 BERTopic Visualizations</h1>
        <div class="description">
            <p><strong>Medical Research Gap Analysis</strong> - Interactive visualizations of topics extracted from research abstracts using BERTopic.</p>
            <p>Click on any visualization below to explore the results interactively.</p>
        </div>
        
        <div class="viz-grid">
"""
    
    # Add cards for each visualization
    viz_descriptions = {
        "topics_overview": {
            "title": "Topics Overview",
            "description": "Interactive scatter plot showing topic relationships. Hover over points to see topic details, zoom in/out to explore clusters."
        },
        "barchart": {
            "title": "Topic Keywords",
            "description": "Interactive bar charts showing the most important keywords for each topic with their relevance scores."
        },
        "heatmap": {
            "title": "Topic Similarity",
            "description": "Interactive heatmap showing similarity relationships between different topics."
        },
        "documents": {
            "title": "Document Distribution",
            "description": "Visualization showing how documents are distributed across topics and their relationships."
        },
        "hierarchy": {
            "title": "Topic Hierarchy",
            "description": "Hierarchical view of topics showing how they relate to each other at different levels."
        }
    }
    
    for viz_name, file_path in visualization_files.items():
        file_name = Path(file_path).name
        
        # Get description or use default
        viz_info = viz_descriptions.get(file_name.replace('.html', ''), {
            "title": viz_name.replace('_', ' ').title(),
            "description": f"Interactive visualization: {viz_name}"
        })
        
        html_content += f"""
            <div class="viz-card">
                <h3>📊 {viz_info['title']}</h3>
                <p>{viz_info['description']}</p>
                <a href="{file_name}" class="viz-link" target="_blank">Open Visualization</a>
            </div>
        """
    
    html_content += """
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666; font-size: 0.9em;">
            <p>Generated by BERTopic Theme Analysis Pipeline</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save index file
    index_path = Path(output_dir) / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"✅ Created visualization index at: {index_path}")
    return str(index_path)


if __name__ == "__main__":
    """
    Example usage of the theme extraction functionality.
    """
    # This would typically be called from another script
    print("Theme Model - Medical Research Gap Analysis Tool")
    print("This module is designed to be imported and used by other scripts.")
    print("See tests/test_theme_model.py for usage examples.")
