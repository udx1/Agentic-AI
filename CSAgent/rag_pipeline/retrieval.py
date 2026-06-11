from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.documents import Document

from chunking import load_chunked_documents
from vector_store import load_vector_store


DEFAULT_RETRIEVAL_PROVIDER = "nebius"
DEFAULT_CANDIDATE_COUNT = 50
DEFAULT_RESULT_COUNT = 4
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "for",
    "how",
    "i",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "which",
    "will",
    "with",
}


@dataclass(frozen=True)
class RetrievalResult:
    document: Document
    vector_score: float
    lexical_score: int


def normalize_token(token: str) -> str:
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def tokenize(value: str) -> set[str]:
    return {
        normalize_token(token)
        for token in TOKEN_PATTERN.findall(value.lower())
        if token not in STOP_WORDS
    }


def metadata_text(document: Document) -> str:
    return " ".join(str(value) for value in document.metadata.values())


def lexical_score(query: str, document: Document) -> int:
    query_tokens = tokenize(query)
    document_tokens = tokenize(f"{metadata_text(document)} {document.page_content}")
    score = len(query_tokens & document_tokens)

    policy = str(document.metadata.get("policy", "")).lower()
    if policy and normalize_token(policy) in query_tokens:
        score += 3

    doc_type = str(document.metadata.get("doc_type", "")).lower()
    if doc_type == "store_policy" and "policy" in query_tokens:
        score += 1

    return score


def retrieve_relevant_chunks(
    query: str,
    provider: str = DEFAULT_RETRIEVAL_PROVIDER,
    k: int = DEFAULT_RESULT_COUNT,
    candidate_count: int = DEFAULT_CANDIDATE_COUNT,
) -> list[RetrievalResult]:
    vector_store = load_vector_store(provider=provider)
    vector_candidates = vector_store.similarity_search_with_score(query, k=candidate_count)
    results = [
        RetrievalResult(
            document=document,
            vector_score=score,
            lexical_score=lexical_score(query, document),
        )
        for document, score in vector_candidates
    ]

    seen_ids = {
        result.document.metadata.get("chunk_id")
        for result in results
    }
    for chunk in load_chunked_documents():
        document = Document(page_content=chunk.page_content, metadata=chunk.metadata)
        score = lexical_score(query, document)
        chunk_id = chunk.metadata.get("chunk_id")
        if score == 0 or chunk_id in seen_ids:
            continue
        results.append(
            RetrievalResult(
                document=document,
                vector_score=float("inf"),
                lexical_score=score,
            )
        )
        seen_ids.add(chunk_id)

    return sorted(results, key=lambda result: (-result.lexical_score, result.vector_score))[:k]
