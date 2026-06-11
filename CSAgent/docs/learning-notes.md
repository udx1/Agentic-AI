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

- Phase 8 is complete: the React frontend now exposes the LangGraph support agent through a floating support chat panel.
- Keeping the public `/chat` response shape stable paid off. The frontend could add chat behavior while the backend continued to evolve internally from deterministic answer generation to graph-based routing.
- Normal customer support mode should stay clean. Citations, retrieved snippets, and debug traces are useful for evaluation, but they make the customer UI feel noisy when shown by default.
- URL-gated modes are useful for local demos: `?_m=e` unlocks eval/developer evidence, while the default mode remains customer-facing.
- Product-aware starter prompts on detail pages help turn the chat from a generic box into contextual support.
- Frontend evidence rendering must match backend field names exactly. The current evidence fields are `label`, `docType`, and `snippet`.
- Some questions are better answered from structured catalog data than vector retrieval. Availability and ranking questions now use `data/catalog/products.json` directly.
- Deterministic catalog logic needs domain nuance. Plain watch/tracker queries should not return accessory-only bands, while explicit watch-band queries should.
- Support contact requests should not invent phone numbers. The safe behavior is to explain the local demo limitation and offer self-service help or ticket preparation.
- Developer/debug controls should be deliberately hidden in normal mode. They are valuable for evaluation, but not part of the customer-facing experience.

## Phase 9: Ticket Persistence And Support Workflow

- Phase 9 is complete: confirmed handoffs can now become persisted local support tickets.
- Runtime tickets live in `data/support/runtime_tickets.json`, separate from seed tickets in `data/support/tickets.json`. This keeps generated demo data and user-created local workflow data from overwriting each other.
- The ticket schema is explicit in `backend/app/ticket_schema.py`, and persistence behavior is isolated in `backend/app/ticket_repository.py`.
- Local JSON persistence is enough for this learning project, but it should be treated as local-only. A production system would need authentication, authorization, a database, transactional writes, audit history, notifications, and operator assignment.
- Ticket ID generation has to scan both seed and runtime tickets so new runtime IDs continue after the existing dataset. The current runtime sequence starts at `TICKET-0026`.
- Idempotency matters even in a local demo. `idempotencyKey` and `ticketRequestId` prevent duplicated tickets when a UI retry or repeated render resubmits the same handoff.
- Chat-to-ticket creation should require explicit confirmation. Normal support answers should never create tickets as a side effect.
- Handoff metadata needs to be customer-safe: issue type, priority, summary, product hints, escalation reason, and conversation excerpt are useful; private account/order/payment data should not be invented.
- Deterministic priority rules are helpful for testing and explainability. Safety language becomes `urgent`; payment and damaged/missing delivery issues become `high`; contact requests remain `normal`.
- Seed tickets are read-only. The support console can inspect them, but updates apply only to runtime tickets.
- The internal support console is opened with `?_m=s#/support/tickets`. This is a local mode gate, not real security.
- Ticket APIs now cover the core workflow: `POST /tickets`, `GET /tickets`, `GET /tickets/{ticket_id}`, and `PATCH /tickets/{ticket_id}`.
- The support console should feel like an operator tool, not a marketing page: dense, scannable, filterable, and visually consistent with the existing ecommerce UI.

## Validation And Test Reporting

- The latest execution check passed on 2026-06-11.
- `rag_pipeline/validate_support_agent.py` currently validates 19 support-agent cases across policy, product setup, troubleshooting, comparison, catalog availability, catalog ranking, clarification, escalation, handoff metadata, and unsupported categories.
- `rag_pipeline/validate_ticket_workflow.py` validates ticket CRUD, ID generation, filtering, runtime updates, seed-ticket update blocking, and idempotent chat handoff creation.
- `frontend` production build passes with `npm run build`.
- FastAPI `TestClient` currently emits a Starlette deprecation warning about `httpx`; it is a maintenance warning, not a failing test.
- `data/support/support_eval_queries.json` defines 20 first-contact-resolution eval cases. These are test data right now; the eval runner is still a next-step item.
- `docs/test-case-report.csv` summarizes the current test inventory: 19 support-agent validation cases, 12 ticket workflow checks, 1 frontend build check, and 20 FCR eval cases.
- The test report distinguishes executable checks from defined eval data. Executed checks are marked `Passed`; FCR dataset rows are marked `Defined` until the eval runner exists.

## Current Provider Lessons

- The current working RAG stack is Chroma plus Nebius embeddings. Retrieval must use the same embedding provider family as the persisted Chroma collection.
- Nebius `Qwen/Qwen3-Embedding-8B` returns 4096-dimensional embeddings, and the current 907-chunk Chroma collection was built with Nebius.
- The local deterministic hashing provider remains useful as a backup, but the Chroma collection must be rebuilt with `--provider hashing` before retrieval can use it.
- OpenAI model visibility is not enough to prove execution readiness. The key can list `text-embedding-3-small`, but embedding calls still fail with `429 insufficient_quota`.
- Claude through Anthropic is the chat-completion provider for natural final answers after retrieval and context sufficiency checks when `CLAUDE_API_KEY` or `ANTHROPIC_API_KEY` is configured.
- The deterministic answer formatter should remain as the fallback when the chat-completion provider is unavailable or when a predictable validation path is needed.

## LLM Prompt Persona Notes

- The final-answer LLM path now uses LangChain `ChatPromptTemplate` in `rag_pipeline/answer_generation.py`.
- The prompt is split into a reusable system persona and a human message template. This is easier to inspect, test, and evolve than one large hand-built string.
- The system persona describes the assistant as calm, concise, practical, customer-friendly, and honest about local-demo limits.
- The grounding rules explicitly forbid inventing policies, product specs, contact numbers, order status, warranty outcomes, payment details, tracking details, or troubleshooting steps.
- The user prompt injects two variables: `{question}` and `{source_context}`. Source context is assembled from retrieved chunks and preserves citation IDs like `[1]`.
- The Anthropic API call is still made through the existing lightweight HTTP adapter, but the request body is now populated from LangChain-generated chat messages.
- This keeps the learning goal focused on prompt design and message structure without adding a new provider package yet.
- Local validation still passes without a Claude key because the deterministic answer formatter remains the fallback.

## Current Next Learning Focus

- Add product-manual-style documents or manual excerpts as a first-class knowledge type.
- Build the first-contact-resolution eval runner around `data/support/support_eval_queries.json`.
- Expand LLM answer validation once a Claude/Anthropic key is available.
- Keep normal support mode citation-free while eval mode continues to expose citations, retrieved context, and debug metadata.
