This project involves building a Python-based research gap analysis and visualization tool that:

    Loads medical research abstracts from AWS S3.

    Parses abstracts into structured data (title, authors, year, text).

    Uses OpenAI GPT (or similar LLM) to extract summaries of research gaps from abstracts.

    Stores extracted gaps and metadata in a PostgreSQL database.

    Supports an interactive frontend (Dash or Streamlit) showing word clouds of gaps by year and topic.

    Emphasizes secure handling of credentials via environment variables.

    Implements modular code organized into scripts for loading data, gap extraction, and database ingestion.

    Will be developed incrementally with clear PR-based deliverables.

When answering questions or generating code, please consider:

    Best practices for data engineering, API integration, and visualization.

    Maintaining security (e.g., avoid exposing secrets).

    Writing clear, reusable, and documented Python code.

    Providing explanations and context appropriate to an experienced developer audience.

    Designing for scalability and easy future enhancement.