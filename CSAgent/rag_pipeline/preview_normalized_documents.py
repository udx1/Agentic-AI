from __future__ import annotations

from collections import Counter

from document_loader import compact_text, load_all_documents
from text_normalizer import load_normalized_documents


def main() -> int:
    raw_documents = load_all_documents()
    normalized_documents = load_normalized_documents()
    doc_type_counts = Counter(document.metadata.get("doc_type", "unknown") for document in normalized_documents)

    print("Normalized Document Preview")
    print("===========================")
    print(f"Raw documents: {len(raw_documents)}")
    print(f"Normalized documents: {len(normalized_documents)}")

    print("\nBy document type")
    for doc_type, count in sorted(doc_type_counts.items()):
        print(f"- {doc_type}: {count}")

    print("\nSample normalized documents")
    seen_types: set[str] = set()
    for document in normalized_documents:
        doc_type = document.metadata.get("doc_type", "unknown")
        if doc_type in seen_types:
            continue
        seen_types.add(doc_type)
        snippet = compact_text(document.page_content)[:420]
        print(f"\n--- {doc_type} ---")
        print(f"metadata: {document.metadata}")
        print(f"content: {snippet}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
