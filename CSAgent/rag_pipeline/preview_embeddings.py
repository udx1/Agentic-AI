from __future__ import annotations

import argparse
from collections import Counter

from document_loader import compact_text
from embeddings import load_embedded_chunks


DEFAULT_PREVIEW_PROVIDER = "nebius"
DEFAULT_PREVIEW_LIMIT = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview embeddings for a small sample of chunked RAG documents."
    )
    parser.add_argument(
        "--provider",
        default=DEFAULT_PREVIEW_PROVIDER,
        choices=["hashing", "openai", "nebius"],
        help="Embedding provider to use.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_PREVIEW_LIMIT,
        help="Only embed the first N chunks for preview. Use 0 to embed all chunks in memory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        raise ValueError("--limit must be 0 or greater")

    if args.limit:
        from chunking import load_chunked_documents
        from embeddings import embed_chunks, get_embedding_model

        records = embed_chunks(
            load_chunked_documents()[: args.limit],
            embedding_model=get_embedding_model(args.provider),
        )
    else:
        records = load_embedded_chunks(provider=args.provider)
    doc_type_counts = Counter(record.metadata.get("doc_type", "unknown") for record in records)

    print("Embedding Preview")
    print("=================")
    print(f"Embedding provider: {args.provider}")
    print(f"Embedded chunks: {len(records)}")
    if args.limit:
        print("Preview mode: yes")
    else:
        print("Preview mode: no, embedded all chunks in memory")
    print(f"Embedding dimension: {len(records[0].embedding) if records else 0}")

    print("\nEmbeddings by document type")
    for doc_type, count in sorted(doc_type_counts.items()):
        print(f"- {doc_type}: {count}")

    if records:
        sample = records[0]
        print("\nSample embedded chunk")
        print(f"id: {sample.id}")
        print(f"metadata: {sample.metadata}")
        print(f"text: {compact_text(sample.text)[:360]}")
        print(f"embedding first 12 values: {sample.embedding[:12]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
