from __future__ import annotations

import os

import truststore
from openai import OpenAI

from check_nebius_access import DEFAULT_NEBIUS_BASE_URL, load_local_env


DEFAULT_NEBIUS_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"


def main() -> int:
    load_local_env()
    truststore.inject_into_ssl()

    api_key = os.getenv("NEBIUS_API_KEY")
    base_url = os.getenv("NEBIUS_BASE_URL") or DEFAULT_NEBIUS_BASE_URL

    if not api_key:
        raise RuntimeError("NEBIUS_API_KEY is required in backend/.env")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.embeddings.create(
        model=os.getenv("NEBIUS_EMBEDDING_MODEL", DEFAULT_NEBIUS_EMBEDDING_MODEL),
        input=["Return policy for opened electronics."],
    )
    embedding = response.data[0].embedding

    print("Nebius Embedding Check")
    print("======================")
    print(f"Base URL: {base_url}")
    print(f"Model: {response.model}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 8 values: {embedding[:8]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
