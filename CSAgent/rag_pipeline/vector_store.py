from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma

from chunking import KnowledgeChunk, load_chunked_documents
from document_loader import REPO_ROOT
from embeddings import EmbeddingModel, get_embedding_model


DEFAULT_COLLECTION_NAME = "csagent_support_knowledge"
DEFAULT_VECTOR_STORE_DIR = REPO_ROOT / "data" / "vector_store" / "chroma"


def sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    sanitized: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, str | int | float | bool):
            sanitized[key] = value
        else:
            sanitized[key] = str(value)
    return sanitized


def create_vector_store(
    embedding_model: EmbeddingModel,
    persist_directory: Path = DEFAULT_VECTOR_STORE_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Chroma:
    persist_directory.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=str(persist_directory),
    )


def rebuild_vector_store(
    provider: str = "hashing",
    chunks: list[KnowledgeChunk] | None = None,
    persist_directory: Path = DEFAULT_VECTOR_STORE_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Chroma:
    if persist_directory.exists():
        shutil.rmtree(persist_directory)

    embedding_model = get_embedding_model(provider)
    vector_store = create_vector_store(
        embedding_model=embedding_model,
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
    chunked_documents = chunks or load_chunked_documents()

    vector_store.add_texts(
        texts=[chunk.page_content for chunk in chunked_documents],
        metadatas=[sanitize_metadata(chunk.metadata) for chunk in chunked_documents],
        ids=[chunk.metadata["chunk_id"] for chunk in chunked_documents],
    )
    return vector_store


def load_vector_store(
    provider: str = "hashing",
    persist_directory: Path = DEFAULT_VECTOR_STORE_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Chroma:
    return create_vector_store(
        embedding_model=get_embedding_model(provider),
        persist_directory=persist_directory,
        collection_name=collection_name,
    )

