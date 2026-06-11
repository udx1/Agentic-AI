# Learning Notes

Use this file to capture short notes after each build phase.

Completed phases also have task-list docs under `docs/phase-*-tasks.md`. These were backfilled for Phases 0-6 after implementation so future sessions can review the original work as checklists, not only summaries.

## Phase 0: Project Setup

- The project is split by capability: data, docs, frontend, and backend.
- Local files come first so the app can be developed and inspected without cloud services.
- React/Vite gives a quick frontend loop for product browsing.
- FastAPI keeps the backend small, typed, and easy to extend with RAG endpoints later.
- `uv` gives the backend a reproducible Python dependency workflow through `pyproject.toml` and `uv.lock`.
- LangChain, LangGraph, and Chroma are planned for the support agent after the catalog and knowledge base exist.

## Phase 1: Data First

- The Amazon Reviews 2023 Electronics metadata includes product-page fields that map well to ecommerce UI: title, price, rating, image, features, description, details, and categories.
- The full source file is large, so the builder streams `meta_Electronics.jsonl.gz` and stops after 50 clean products.
- Cleaning criteria matter: a parsed record is not always a good storefront product.
- The normalized catalog intentionally uses frontend-friendly names like `reviewCount`.
- `reviewCount` is aggregate metadata only; individual review text will be added separately in Phase 5 for support/RAG context.
- `data/raw/electronics_sample.jsonl` keeps traceability back to the selected source records.
- `backend/scripts/validate_catalog.py` gives us a fast check before the UI depends on the data.

## Phase 2: UI Baseline

- The frontend can import local JSON directly in Vite, which keeps Phase 2 independent from the backend.
- Product cards need fixed image and text regions because catalog titles vary widely in length.
- Hash-based navigation is enough for the first product detail view without adding routing dependencies.
- The catalog copy in `frontend/src/data/products.json` was temporary and was removed in Phase 4.

## Phase 3: Frontend Logic

- Search, category filtering, and sorting are derived from the same product list, so the UI does not need duplicate data.
- Cart state lives at the app level because product cards, product details, and the cart panel all need access to it.
- The cart remains local-only for now; persistence and backend checkout behavior are outside this project scope.
- Sorting is a pure presentation concern in Phase 3 and will still work after products move behind FastAPI in Phase 4.

## Phase 4: Backend API

- FastAPI now owns catalog access, while the frontend owns presentation concerns like search, sort, and cart behavior.
- Product data and category data are separate API resources because navigation needs categories even before a product detail is opened.
- CORS is required because Vite and FastAPI run on different local ports.
- The frontend now needs the backend running at `http://127.0.0.1:8000` unless `VITE_API_BASE_URL` is set.

## Phase 5: Local Support Knowledge Base

- RAG needs documents that answer support questions, not just ecommerce product fields.
- Product documents now have front matter with `doc_type`, `product_id`, category, and subcategory for later metadata filtering.
- Real review coverage is partial because the review stream is large and selected catalog products do not all appear early in the stream.
- Every product still has complete synthetic support docs so retrieval will have useful context for setup, troubleshooting, compatibility, and policy questions.
- Store policies are global documents and should be retrievable even when no product is mentioned.

## Phase 6: RAG Pipeline

- Chunk IDs must be globally unique before writing to Chroma; customer reviews and support tickets need IDs based on their own source identifiers, not only `product_id`.
- The OpenAI key can list models, but embedding calls currently return `429 insufficient_quota`, so model visibility is not the same as usable quota.
- The local hashing embedding provider is useful for pipeline development because it is deterministic, free, and keeps the Chroma workflow moving.
- Hashing embeddings are weaker than semantic embeddings, so the backup retriever merges Chroma candidates with lexical matches and reranks by keyword overlap.
- Chroma is persisted under `data/vector_store/chroma`, but generated vector data is ignored by git and can be rebuilt from source documents.
- Nebius can be used through an OpenAI-compatible client by setting `NEBIUS_API_KEY` and `NEBIUS_BASE_URL` in `backend/.env`.
- `Qwen/Qwen3-Embedding-8B` works for embeddings and returns 4096 dimensions; the full 907-chunk Chroma build completed in about 19 minutes.
- Embedding preview and vector-store creation are separate steps: `preview_embeddings.py` embeds a small sample in memory for inspection, while `build_vector_store.py` embeds all chunks again and persists them in Chroma.
- Retrieval must use the same provider family as the persisted Chroma collection. The current Chroma store uses Nebius 4096-dimensional embeddings, so retrieval and answer previews should use `--provider nebius`.
- `preview_answers.py` is currently deterministic and extractive. It formats retrieved chunks into cited support answers without requiring a chat-completion model.
- The backend `/chat` endpoint reuses the same answer-generation layer as the preview script, which keeps CLI learning tools and API behavior aligned.
- The notebook now includes a FastAPI `TestClient` section, so API behavior can be tested without running Uvicorn.
- Phase 6 is complete; the backend now has a baseline `/chat` endpoint.
- Phase 7 was started by adding the deterministic chat baseline during the RAG wrap-up.
- The next learning focus is turning that baseline into a fuller LangGraph support-agent workflow before connecting the frontend chat UI.

## Phase 7: Support Chat Agent

- Phase 7 is complete: the API now answers support questions through a LangGraph-backed `POST /chat` workflow.
- The agent workflow makes the support flow explicit: classify intent, retrieve context, judge sufficiency, answer with citations, ask for clarification, or prepare escalation.
- Keeping the existing `/chat` request and response shape stable will make Phase 8 frontend integration simpler.
- Scope checks matter: a policy-looking question can still be outside the demo store domain. For example, an apparel question like "opened clothes" should not cite electronics return policy documents.
- The first LangGraph version is intentionally deterministic. This keeps the workflow inspectable and usable while LLM chat-completion provider decisions are still deferred.
- Escalation currently means "prepare handoff metadata and a safe response"; it does not create persistent tickets yet.
- `rag_pipeline/validate_support_agent.py` gives a repeatable eval-style check across policy, product setup, troubleshooting, comparison, clarification, escalation, and unsupported-category cases.
- Developer/debug trace mode would be a good next observability layer, but it should be exposed deliberately so the normal customer-facing response stays clean.

## Phase 8: Chat UI

- Phase 8 starts from a stable backend contract: `POST /chat` accepts a question and provider, then returns answer text, citations, and retrieved context.
- The first frontend chat UI should keep the customer-facing experience clean while leaving room for a later developer/debug trace panel.
- Citations should appear only when the backend returns grounded sources; clarification and escalation responses may intentionally have no citations.
