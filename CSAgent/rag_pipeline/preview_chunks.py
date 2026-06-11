from __future__ import annotations

from collections import Counter

from chunking import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, load_chunked_documents
from document_loader import compact_text
from text_normalizer import load_normalized_documents


def main() -> int:
    documents = load_normalized_documents()
    chunks = load_chunked_documents()
    doc_type_counts = Counter(chunk.metadata.get("doc_type", "unknown") for chunk in chunks)

    print("Chunk Preview")
    print("=============")
    print(f"Normalized documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")
    print(f"Chunk size: {DEFAULT_CHUNK_SIZE}")
    print(f"Chunk overlap: {DEFAULT_CHUNK_OVERLAP}")

    print("\nChunks by document type")
    for doc_type, count in sorted(doc_type_counts.items()):
        print(f"- {doc_type}: {count}")

    print("\nSample chunks")
    seen_types: set[str] = set()
    for chunk in chunks:
        doc_type = chunk.metadata.get("doc_type", "unknown")
        if doc_type in seen_types:
            continue
        seen_types.add(doc_type)
        snippet = compact_text(chunk.page_content)[:360]
        print(f"\n--- {doc_type} ---")
        print(f"metadata: {chunk.metadata}")
        print(f"content: {snippet}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
