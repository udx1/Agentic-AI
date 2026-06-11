from __future__ import annotations

import argparse
from collections import Counter

from chunking import load_chunked_documents
from embeddings import get_embedding_model
from vector_store import DEFAULT_COLLECTION_NAME, DEFAULT_VECTOR_STORE_DIR, rebuild_vector_store


DEFAULT_BUILD_PROVIDER = "nebius"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed all chunks and build the local Chroma vector store."
    )
    parser.add_argument(
        "--provider",
        default=DEFAULT_BUILD_PROVIDER,
        choices=["hashing", "openai", "nebius"],
        help="Embedding provider to use for the full Chroma build.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chunks = load_chunked_documents()
    model = get_embedding_model(args.provider)
    doc_type_counts = Counter(chunk.metadata.get("doc_type", "unknown") for chunk in chunks)

    vector_store = rebuild_vector_store(
        provider=args.provider,
        chunks=chunks,
    )

    print("Vector Store Build")
    print("==================")
    print("Mode: full build, embeds all chunks and persists them in Chroma")
    print(f"Embedding provider: {model.name}")
    print(f"Embedding dimension: {model.dimension}")
    print(f"Collection: {DEFAULT_COLLECTION_NAME}")
    print(f"Persist directory: {DEFAULT_VECTOR_STORE_DIR}")
    print(f"Stored chunks: {vector_store._collection.count()}")

    print("\nStored chunks by document type")
    for doc_type, count in sorted(doc_type_counts.items()):
        print(f"- {doc_type}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
