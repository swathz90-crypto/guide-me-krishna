#!/usr/bin/env python3
"""CLI entry point for the offline Gita corpus indexer."""
import argparse
import sys

from dotenv import load_dotenv
load_dotenv()

from src.indexer import index_gita_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Index the Bhagavad Gita corpus into the vector store.")
    parser.add_argument("corpus_path", help="Path to the corpus JSON or CSV file")
    parser.add_argument("--chroma-dir", default=".chroma", help="ChromaDB persistence directory")
    args = parser.parse_args()

    from src.embedder import Embedder
    from src.vector_store import VectorStore

    embedder = Embedder()
    store = VectorStore(persist_directory=args.chroma_dir)

    try:
        count = index_gita_corpus(args.corpus_path, embedder=embedder, vector_store=store)
        print(f"Successfully indexed {count} verses.")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
