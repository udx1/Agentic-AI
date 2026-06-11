from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import truststore
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings

from chunking import KnowledgeChunk, load_chunked_documents


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV_PATH = REPO_ROOT / "backend" / ".env"
DEFAULT_EMBEDDING_PROVIDER = "openai"
DEFAULT_EMBEDDING_DIMENSION = 384
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1"
DEFAULT_NEBIUS_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"
DEFAULT_NEBIUS_BATCH_SIZE = 16
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class EmbeddingRecord:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]


class EmbeddingModel(Protocol):
    name: str
    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class HashingEmbeddingModel:
    """Small local embedder for pipeline development without external services."""

    name = "local-hashing"

    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be greater than 0")
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = TOKEN_PATTERN.findall(text.lower())

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], byteorder="big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector

        return [value / magnitude for value in vector]


def load_backend_env(path: Path = BACKEND_ENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


class LangChainOpenAIEmbeddingModel:
    """Semantic embedder backed by LangChain's OpenAIEmbeddings."""

    def __init__(self, model: str = DEFAULT_OPENAI_EMBEDDING_MODEL) -> None:
        load_backend_env()
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")

        truststore.inject_into_ssl()
        self.embeddings = OpenAIEmbeddings(
            model=model,
            check_embedding_ctx_length=False,
        )
        self.name = model
        self.dimension = 1536 if model == "text-embedding-3-small" else 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embeddings.embed_query(text)


class NebiusEmbeddingModel:
    """OpenAI-compatible embedder backed by Nebius AI Studio."""

    def __init__(
        self,
        model: str = DEFAULT_NEBIUS_EMBEDDING_MODEL,
        batch_size: int = DEFAULT_NEBIUS_BATCH_SIZE,
    ) -> None:
        load_backend_env()

        api_key = os.getenv("NEBIUS_API_KEY")
        base_url = os.getenv("NEBIUS_BASE_URL") or DEFAULT_NEBIUS_BASE_URL
        if not api_key:
            raise RuntimeError("NEBIUS_API_KEY is required for Nebius embeddings")
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")

        truststore.inject_into_ssl()
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.name = model
        self.dimension = 4096 if model == DEFAULT_NEBIUS_EMBEDDING_MODEL else 0
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = self.client.embeddings.create(model=self.name, input=batch)
            embeddings.extend(item.embedding for item in response.data)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.name, input=[text])
        return response.data[0].embedding


def get_embedding_model(provider: str = DEFAULT_EMBEDDING_PROVIDER) -> EmbeddingModel:
    normalized_provider = provider.strip().lower()
    if normalized_provider == "hashing":
        return HashingEmbeddingModel()
    if normalized_provider == "openai":
        return LangChainOpenAIEmbeddingModel()
    if normalized_provider == "nebius":
        return NebiusEmbeddingModel()
    raise ValueError(f"Unsupported embedding provider: {provider}")


def embed_chunks(
    chunks: list[KnowledgeChunk],
    embedding_model: EmbeddingModel | None = None,
    batch_size: int = 64,
) -> list[EmbeddingRecord]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")

    model = embedding_model or get_embedding_model()
    records: list[EmbeddingRecord] = []

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        texts = [chunk.page_content for chunk in batch]
        embeddings = model.embed_documents(texts)

        for chunk, embedding in zip(batch, embeddings, strict=True):
            chunk_id = chunk.metadata["chunk_id"]
            records.append(
                EmbeddingRecord(
                    id=chunk_id,
                    text=chunk.page_content,
                    embedding=embedding,
                    metadata={
                        **chunk.metadata,
                        "embedding_provider": model.name,
                        "embedding_dimension": len(embedding),
                    },
                )
            )

    return records


def load_embedded_chunks(
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    batch_size: int = 64,
) -> list[EmbeddingRecord]:
    return embed_chunks(
        load_chunked_documents(),
        embedding_model=get_embedding_model(provider),
        batch_size=batch_size,
    )
