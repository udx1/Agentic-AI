from __future__ import annotations

from pathlib import Path


BACKEND_ENV_PATH = Path(__file__).resolve().parents[1] / "backend" / ".env"
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")


def clean_value(value: str) -> str:
    return value.strip().strip("\"'")


def main() -> int:
    print("Env Shape Check")
    print("===============")
    print(f"Path: {BACKEND_ENV_PATH}")
    print(f"Exists: {BACKEND_ENV_PATH.exists()}")

    if not BACKEND_ENV_PATH.exists():
        return 0

    for raw_line in BACKEND_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = clean_value(value)

        if any(marker in key.upper() for marker in SECRET_MARKERS):
            state = "set" if value else "empty"
            print(f"{key}: {state}, length={len(value)}")
        else:
            print(f"{key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

