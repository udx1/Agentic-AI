from __future__ import annotations

import os
from pathlib import Path

import truststore
from openai import OpenAI


DEFAULT_NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1"
BACKEND_ENV_PATH = Path(__file__).resolve().parents[1] / "backend" / ".env"


def load_local_env(path: Path = BACKEND_ENV_PATH) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def main() -> int:
    load_local_env()
    truststore.inject_into_ssl()

    api_key = os.getenv("NEBIUS_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("NEBIUS_BASE_URL") or os.getenv("OPENAI_BASE_URL") or DEFAULT_NEBIUS_BASE_URL

    if not api_key:
        raise RuntimeError("NEBIUS_API_KEY or OPENAI_API_KEY is required in backend/.env")

    client = OpenAI(api_key=api_key, base_url=base_url)
    models = client.models.list()
    model_ids = sorted(model.id for model in models.data)

    print("Nebius Access Check")
    print("===================")
    print(f"Base URL: {base_url}")
    print(f"Models visible: {len(model_ids)}")
    print("Sample models:")
    for model_id in model_ids[:20]:
        print(f"- {model_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
