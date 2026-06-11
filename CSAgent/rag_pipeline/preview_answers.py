from __future__ import annotations

import argparse

from answer_generation import generate_cited_answer
from retrieval import DEFAULT_RETRIEVAL_PROVIDER


SAMPLE_QUESTIONS = [
    "What is the return policy for opened electronics?",
    "How do I troubleshoot a device that will not power on?",
    "Which product information mentions Bluetooth compatibility?",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview grounded support answers with citations.")
    parser.add_argument(
        "--provider",
        default=DEFAULT_RETRIEVAL_PROVIDER,
        choices=["hashing", "openai", "nebius"],
        help="Embedding provider that matches the persisted Chroma collection.",
    )
    parser.add_argument(
        "--question",
        action="append",
        help="Question to answer. Can be passed multiple times.",
    )
    return parser.parse_args()


def print_answer(question: str, provider: str) -> None:
    cited_answer = generate_cited_answer(question=question, provider=provider)

    print(f"\nQuestion: {question}")
    print(cited_answer.answer)
    if not cited_answer.citations:
        return

    print("\nCitations:")
    for citation in cited_answer.citations:
        print(
            f"[{citation.id}] {citation.label} | "
            f"{citation.source_path} | {citation.chunk_id}"
        )


def main() -> int:
    args = parse_args()
    questions = args.question or SAMPLE_QUESTIONS

    print("Grounded Answer Preview")
    print("=======================")
    print(f"Embedding provider: {args.provider}")

    for question in questions:
        print_answer(question, args.provider)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
