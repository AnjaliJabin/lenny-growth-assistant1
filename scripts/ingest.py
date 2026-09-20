#!/usr/bin/env python3
"""
Ingest Lenny's Podcast transcripts and build the FAISS vector index.
Usage: python scripts/ingest.py
Place .txt transcript files in data/transcripts/ before running.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.services.retrieval import retrieval_service
from backend.app.core.logging import get_logger

logger = get_logger("ingest")

if __name__ == "__main__":
    logger.info('"Starting ingestion..."')
    retrieval_service.build_index()
    logger.info('"Ingestion complete"')
