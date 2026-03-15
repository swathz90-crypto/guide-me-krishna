#!/bin/bash
set -e

CHROMA_DIR="${CHROMA_DIR:-.chroma}"

# If ChromaDB is empty, index the corpus first
python -c "
import os, sys
from src.vector_store import VectorStore
vs = VectorStore(persist_directory=os.getenv('CHROMA_DIR', '.chroma'))
count = vs.count()
print(f'ChromaDB has {count} documents')
sys.exit(0 if count > 0 else 1)
" || python scripts/run_indexer.py data/gita_corpus.json --chroma-dir "$CHROMA_DIR"

# Start the server
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
