#!/bin/bash
set -e

CHROMA_DIR="${CHROMA_DIR:-.chroma}"

echo "==> Starting Guide Me Krishna"
echo "==> PORT=${PORT:-8000}"
echo "==> CHROMA_DIR=$CHROMA_DIR"

# Index corpus if ChromaDB is empty
python -c "
import os, sys
sys.path.insert(0, '/app')
from src.vector_store import VectorStore
vs = VectorStore(persist_directory=os.getenv('CHROMA_DIR', '.chroma'))
count = vs.count()
print(f'ChromaDB documents: {count}')
sys.exit(0 if count > 0 else 1)
" && echo "==> ChromaDB already indexed" || {
  echo "==> Indexing corpus..."
  python scripts/run_indexer.py data/gita_corpus.json --chroma-dir "$CHROMA_DIR"
  echo "==> Indexing complete"
}

echo "==> Starting uvicorn on port ${PORT:-8000}"
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
