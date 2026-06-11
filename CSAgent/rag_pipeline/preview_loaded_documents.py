from __future__ import annotations

from collections import Counter

from document_loader import compact_text, load_all_documents


def main() -> int:
    documents = load_all_documents()
    source_counts = Counter(document.metadata["source_type"] for document in documents)
    doc_type_counts = Counter(document.metadata.get("doc_type", "unknown") for document in documents)

    print("Loaded Document Preview")
    print("=======================")
    print(f"Total documents: {len(documents)}")

    print("\nBy source type")
    for source_type, count in sorted(source_counts.items()):
        print(f"- {source_type}: {count}")

    print("\nBy document type")
    for doc_type, count in sorted(doc_type_counts.items()):
        print(f"- {doc_type}: {count}")

    print("\nSample documents")
    seen_types: set[str] = set()
    for document in documents:
        doc_type = document.metadata.get("doc_type", "unknown")
        if doc_type in seen_types:
            continue
        seen_types.add(doc_type)
        snippet = compact_text(document.page_content)[:260]
        print(f"\n--- {doc_type} ---")
        print(f"metadata: {document.metadata}")
        print(f"content: {snippet}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
