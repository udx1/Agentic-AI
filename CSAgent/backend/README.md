# Backend

Stack: FastAPI managed with `uv`.

This folder holds the Python API and later RAG services.

## Setup

Install dependencies:

```powershell
uv sync
```

Run the local API:

```powershell
uv run uvicorn app.main:app --reload
```

Health check:

```text
GET /health
```

Catalog endpoints:

```text
GET /products
GET /products/{id}
GET /products/{id}/reviews
GET /categories
```

Expected responsibilities:

- Product and category API endpoints
- Chat endpoint
- Ticket endpoints
- RAG pipeline orchestration
- LangGraph support workflow

## Data Scripts

Build the Phase 1 product catalog:

```powershell
uv run python scripts/build_catalog.py
```

If local certificate validation fails for the official dataset source:

```powershell
uv run python scripts/build_catalog.py --insecure-source
```

Validate the generated catalog:

```powershell
uv run python scripts/validate_catalog.py
```

Build Phase 5 review samples:

```powershell
uv run python scripts/build_reviews.py --insecure-source --scan-limit 5000000
```

Build the local support knowledge base:

```powershell
uv run python scripts/build_support_kb.py
```

Validate the support knowledge base:

```powershell
uv run python scripts/validate_support_kb.py
```
