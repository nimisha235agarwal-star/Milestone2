# Phase Folders

This directory contains the modular implementation of the RAG pipeline.

- `phase1_ingestion/`: Future location for document loaders and data preparation (if needed separate from scraping).
- `phase2_chunking_embedding/`: Location for HTML text splitters, metadata injection, and embedding logic.
- `phase3_retrieval_guardrails/`: Location for vector DB retrieval, PII scrubbing, and Intent Classification.
- `phase4_scheduler_scraping/`: Location for the web scraping service triggered by GitHub Actions.
