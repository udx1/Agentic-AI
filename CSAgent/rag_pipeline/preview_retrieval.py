from __future__ import annotations

import argparse

from document_loader import compact_text
from retrieval import DEFAULT_RESULT_COUNT, DEFAULT_RETRIEVAL_PROVIDER, retrieve_relevant_chunks


SAMPLE_QUERIES = [
    "What is the return policy for opened electronics?",
    "How do I troubleshoot a device that will not power on?",
    "Which product information mentions Bluetooth compatibility?",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview retrieval from the local Chroma store.")
    parser.add_argument(
        "--provider",
        default=DEFAULT_RETRIEVAL_PROVIDER,
        choices=["hashing", "openai", "nebius"],
        help="Embedding provider that matches the persisted Chroma collection.",
    )
    return parser.parse_args()


def print_result(query: str, results: list) -> None:
    print(f"\nQuery: {query}")
    for index, result in enumerate(results, start=1):
        document = result.document
        metadata = document.metadata
        source = metadata.get("source_path", "unknown")
        doc_type = metadata.get("doc_type", "unknown")
        chunk_id = metadata.get("chunk_id", "unknown")
        snippet = compact_text(document.page_content)[:260]
        print(
            f"{index}. {doc_type} | vector={result.vector_score:.4f} "
            f"| lexical={result.lexical_score} | {chunk_id}"
        )
        print(f"   source: {source}")
        print(f"   text: {snippet}")


def main() -> int:
    args = parse_args()

    print("Retrieval Preview")
    print("=================")
    print(f"Embedding provider: {args.provider}")

    for query in SAMPLE_QUERIES:
        results = retrieve_relevant_chunks(
            query,
            provider=args.provider,
            k=DEFAULT_RESULT_COUNT,
        )
        print_result(query, results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
