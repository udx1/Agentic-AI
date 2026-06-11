from __future__ import annotations

import re
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
import truststore

from document_loader import compact_text
from retrieval import (
    DEFAULT_RESULT_COUNT,
    DEFAULT_RETRIEVAL_PROVIDER,
    RetrievalResult,
    retrieve_relevant_chunks,
    tokenize,
)


DEFAULT_MAX_CONTEXTS = 4
DEFAULT_SNIPPET_SENTENCES = 2
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"
DEFAULT_CLAUDE_MAX_TOKENS = 450
DEFAULT_CLAUDE_TIMEOUT_SECONDS = 30
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+-\s+|\n+\d+\.\s+")
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV_PATH = REPO_ROOT / "backend" / ".env"

SUPPORT_SYSTEM_PROMPT = """You are the customer support assistant for a local electronics ecommerce demo.

Persona:
- Calm, concise, practical, and customer-friendly.
- Honest about local-demo limits.
- Helpful without pretending to access private account, order, payment, tracking, phone, email, CRM, or inventory systems.

Grounding rules:
- Use only the retrieved support sources and catalog context provided in the user message.
- Cite factual claims with the supplied bracketed citation numbers, such as [1].
- Do not cite sources that were not supplied.
- If the sources are insufficient, say what is missing briefly and ask one focused follow-up question.
- Do not invent policies, product specs, contact numbers, order status, warranty outcomes, or troubleshooting steps.

Style:
- Plain text only.
- Prefer short paragraphs or '-' bullets.
- No markdown headings, tables, bold text, horizontal rules, or emoji.
- Keep the answer direct enough for a chat panel."""

SUPPORT_USER_PROMPT = """Customer question:
{question}

Retrieved support sources:
{source_context}

Task:
Write the final customer-facing answer. 
Stay grounded in the retrieved sources, preserve citation numbers,
and keep the tone concise and reassuring."""

SUPPORT_ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SUPPORT_SYSTEM_PROMPT),
        ("human", SUPPORT_USER_PROMPT),
    ]
)


@dataclass(frozen=True)
class Citation:
    id: str
    label: str
    source_path: str
    doc_type: str
    product_id: str | None
    chunk_id: str


@dataclass(frozen=True)
class CitedAnswer:
    question: str
    answer: str
    citations: list[Citation]
    retrieved_results: list[RetrievalResult]


def load_backend_env(path: Path = BACKEND_ENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def source_label(document: Document, index: int) -> str:
    metadata = document.metadata
    doc_type = str(metadata.get("doc_type", "source")).replace("_", " ")
    title = metadata.get("title")
    policy = metadata.get("policy")
    product_id = metadata.get("product_id")
    ticket_id = metadata.get("ticket_id")

    if title:
        return f"{index}. {title} ({doc_type})"
    if policy:
        return f"{index}. {str(policy).title()} policy"
    if ticket_id:
        return f"{index}. Support ticket {ticket_id}"
    if product_id:
        return f"{index}. Product {product_id} ({doc_type})"
    return f"{index}. {doc_type.title()}"


def build_citation(document: Document, index: int) -> Citation:
    metadata = document.metadata
    return Citation(
        id=str(index),
        label=source_label(document, index),
        source_path=str(metadata.get("source_path", "unknown")),
        doc_type=str(metadata.get("doc_type", "unknown")),
        product_id=(
            str(metadata["product_id"])
            if metadata.get("product_id") is not None
            else None
        ),
        chunk_id=str(metadata.get("chunk_id", "unknown")),
    )


def split_context_sentences(text: str) -> list[str]:
    line_items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^[-*]\s*", "", line)
        line = re.sub(r"^\d+\.\s*", "", line)
        if line:
            line_items.append(compact_text(line))

    if line_items:
        return line_items

    cleaned = compact_text(text.replace("#", " "))
    return [sentence.strip(" -") for sentence in SENTENCE_PATTERN.split(cleaned) if sentence.strip(" -")]


def sentence_score(question_tokens: set[str], sentence: str) -> int:
    return len(question_tokens & tokenize(sentence))


def best_context_snippet(
    question: str,
    document: Document,
    max_sentences: int = DEFAULT_SNIPPET_SENTENCES,
) -> str:
    question_tokens = tokenize(question)
    sentences = split_context_sentences(document.page_content)
    if not sentences:
        return compact_text(document.page_content)[:320]

    ranked = sorted(
        enumerate(sentences),
        key=lambda item: (-sentence_score(question_tokens, item[1]), item[0]),
    )
    selected_indexes = sorted(index for index, _ in ranked[:max_sentences])
    selected = [sentences[index] for index in selected_indexes]
    return compact_text(" ".join(selected))


def has_enough_context(results: list[RetrievalResult]) -> bool:
    return any(result.lexical_score > 0 for result in results)


def generate_cited_answer(
    question: str,
    provider: str = DEFAULT_RETRIEVAL_PROVIDER,
    k: int = DEFAULT_RESULT_COUNT,
) -> CitedAnswer:
    results = retrieve_relevant_chunks(question, provider=provider, k=k)
    return build_cited_answer_from_results(question=question, results=results)


def build_cited_answer_from_results(
    question: str,
    results: list[RetrievalResult],
) -> CitedAnswer:
    top_lexical_score = max(
        (result.lexical_score for result in results),
        default=0,
    )
    minimum_lexical_score = max(1, top_lexical_score - 2)
    selected_results = [
        result for result in results if result.lexical_score >= minimum_lexical_score
    ][:DEFAULT_MAX_CONTEXTS]
    citations = [
        build_citation(result.document, index)
        for index, result in enumerate(selected_results, start=1)
    ]

    if not selected_results or not has_enough_context(selected_results):
        answer = (
            "I do not have enough matching support context to answer that confidently. "
            "Please share the product name, product ID, or the policy area you want help with."
        )
        return CitedAnswer(
            question=question,
            answer=answer,
            citations=[],
            retrieved_results=results,
        )

    evidence_lines = []
    for citation, result in zip(citations, selected_results, strict=True):
        snippet = best_context_snippet(question, result.document)
        if snippet:
            evidence_lines.append(f"- {snippet} [{citation.id}]")

    deterministic_answer = "\n".join(
        [
            "Based on the retrieved support context:",
            *evidence_lines,
            "",
            "Use the cited sources below to inspect the exact supporting documents.",
        ]
    )
    answer = generate_claude_answer_from_context(
        question=question,
        citations=citations,
        retrieved_results=selected_results,
    ) or deterministic_answer
    return CitedAnswer(
        question=question,
        answer=answer,
        citations=citations,
        retrieved_results=results,
    )


def source_context_block(
    question: str,
    citation: Citation,
    result: RetrievalResult,
) -> str:
    snippet = best_context_snippet(question, result.document, max_sentences=4)
    return "\n".join(
        [
            f"[{citation.id}] {citation.label}",
            f"Document type: {citation.doc_type}",
            f"Product ID: {citation.product_id or 'none'}",
            f"Source path: {citation.source_path}",
            f"Snippet: {snippet}",
        ]
    )


def build_source_context(
    question: str,
    citations: list[Citation],
    retrieved_results: list[RetrievalResult],
) -> str:
    return "\n\n".join(
        source_context_block(question, citation, result)
        for citation, result in zip(citations, retrieved_results, strict=True)
    )


def build_support_answer_prompt_messages(
    question: str,
    citations: list[Citation],
    retrieved_results: list[RetrievalResult],
):
    source_context = build_source_context(
        question=question,
        citations=citations,
        retrieved_results=retrieved_results,
    )
    return SUPPORT_ANSWER_PROMPT.invoke(
        {
            "question": question,
            "source_context": source_context,
        }
    ).to_messages()


def generate_claude_answer_from_context(
    question: str,
    citations: list[Citation],
    retrieved_results: list[RetrievalResult],
) -> str | None:
    load_backend_env()
    api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not citations or not retrieved_results:
        return None

    prompt_messages = build_support_answer_prompt_messages(
        question=question,
        citations=citations,
        retrieved_results=retrieved_results,
    )
    system_prompt = "\n\n".join(
        str(message.content)
        for message in prompt_messages
        if message.type == "system"
    )
    anthropic_messages = [
        {
            "role": "user" if message.type == "human" else message.type,
            "content": str(message.content),
        }
        for message in prompt_messages
        if message.type != "system"
    ]

    request_body = {
        "model": os.getenv("CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL),
        "max_tokens": int(os.getenv("CLAUDE_MAX_TOKENS", str(DEFAULT_CLAUDE_MAX_TOKENS))),
        "temperature": 0.2,
        "system": system_prompt,
        "messages": anthropic_messages,
    }

    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        truststore.inject_into_ssl()
        with urllib.request.urlopen(
            request,
            timeout=int(os.getenv("CLAUDE_TIMEOUT_SECONDS", str(DEFAULT_CLAUDE_TIMEOUT_SECONDS))),
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    text_parts = [
        block.get("text", "")
        for block in payload.get("content", [])
        if block.get("type") == "text" and block.get("text")
    ]
    answer = "\n".join(text_parts).strip()
    return answer or None
