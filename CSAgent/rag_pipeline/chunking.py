from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from document_loader import KnowledgeDocument
from text_normalizer import load_normalized_documents


DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class KnowledgeChunk:
    page_content: str
    metadata: dict[str, Any]


def create_text_splitter(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> RecursiveCharacterTextSplitter:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be 0 or greater")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_document(
    document: KnowledgeDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    source_instance: int = 1,
) -> list[KnowledgeChunk]:
    splitter = create_text_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    text_chunks = splitter.split_text(document.page_content)
    total_chunks = len(text_chunks)

    chunks: list[KnowledgeChunk] = []
    source_path = document.metadata.get("source_path", "unknown")
    doc_type = document.metadata.get("doc_type", "unknown")
    source_id = document_source_id(document.metadata, source_path)
    source_key = f"{doc_type}:{source_id}"
    if source_instance > 1:
        source_key = f"{source_key}:doc{source_instance}"

    for index, text_chunk in enumerate(text_chunks):
        chunk_id = f"{source_key}:{index + 1}"
        chunks.append(
            KnowledgeChunk(
                page_content=text_chunk,
                metadata={
                    **document.metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": index,
                    "chunk_count": total_chunks,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                },
            )
        )

    return chunks


def document_source_id(metadata: dict[str, Any], fallback: str = "unknown") -> str:
    doc_type = metadata.get("doc_type")
    if doc_type == "customer_review":
        product_id = metadata.get("product_id", fallback)
        review_id = metadata.get("review_id", fallback)
        return f"{product_id}:{review_id}"
    if doc_type == "support_ticket":
        return str(metadata.get("ticket_id", fallback))
    if doc_type == "category":
        return str(metadata.get("category_id", fallback))
    if doc_type in {"catalog_product", "faq", "setup", "troubleshooting", "compatibility"}:
        return str(metadata.get("product_id", fallback))
    if doc_type in {"shipping_policy", "returns_policy", "warranty_policy", "payments_policy"}:
        return str(metadata.get("policy", fallback))
    return str(metadata.get("product_id", fallback))


def chunk_documents(
    documents: list[KnowledgeDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    source_counts: dict[str, int] = {}

    for document in documents:
        source_path = document.metadata.get("source_path", "unknown")
        doc_type = document.metadata.get("doc_type", "unknown")
        source_id = document_source_id(document.metadata, source_path)
        source_key = f"{doc_type}:{source_id}"
        source_counts[source_key] = source_counts.get(source_key, 0) + 1

        chunks.extend(
            chunk_document(
                document,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                source_instance=source_counts[source_key],
            )
        )
    return chunks


def load_chunked_documents(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[KnowledgeChunk]:
    return chunk_documents(
        load_normalized_documents(),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
