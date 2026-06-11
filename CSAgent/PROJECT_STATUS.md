# Project Status

Last checked: 2026-06-11

## Current Goal

Build a local-first ecommerce site using a 50-product subset from the UCSD Amazon Electronics dataset, then extend it with a RAG-based customer support chat agent and local ticket workflow.

## Current Status

Phases 0 through 9 are complete.

The app now includes:

- React/Vite ecommerce frontend with catalog browsing, product detail pages, search, sorting, category filtering, cart behavior, and a floating support chat panel.
- FastAPI backend with catalog endpoints, LangGraph-backed `POST /chat`, and local support ticket APIs.
- RAG pipeline using LangChain, Chroma, and Nebius embeddings for the current local vector store.
- Deterministic support-agent workflow for intent classification, retrieval planning, context sufficiency checks, catalog answers, clarification, escalation, ticket handoff, and fallback answer formatting.
- Local ticket persistence for confirmed handoffs, plus a lightweight internal ticket console.

Current active phase:

```text
Phase 9: Ticket persistence and support workflow extensions is complete.
Post-Phase-9 RAG enhancement work has started with LLM prompt/persona final-answer generation.
```

## Latest Execution Check

Run from the repo on 2026-06-11:

```powershell
cd backend
uv run python ../rag_pipeline/validate_support_agent.py
uv run python ../rag_pipeline/validate_ticket_workflow.py

cd ../frontend
npm run build
```

Results:

- `validate_support_agent.py`: passed 19 support-agent cases.
- `validate_ticket_workflow.py`: passed CRUD, ID generation, filtering, updates, and idempotent chat handoff validation.
- `npm run build`: passed; Vite production build completed.

Known warning:

- FastAPI `TestClient` emits a Starlette deprecation warning about `httpx`; it does not currently block validation.

## Running Locally

See `docs/local-runbook.md` for start, stop, URL, and quick validation commands.

Key URLs:

Eval/developer evidence mode:

```text
http://127.0.0.1:5173/?_m=e
```

Internal support-ticket console:

```text
http://127.0.0.1:5173/?_m=s#/support/tickets
```

## Current API Surface

Catalog:

- `GET /health`
- `GET /products`
- `GET /products/{id}`
- `GET /categories`

Support chat:

- `POST /chat`
- Request body includes `question`, `provider`, optional `debug`, optional `createTicket`, and optional `ticketRequestId`.
- Default working provider is `nebius`.
- Response preserves the public shape with `question`, `answer`, `provider`, `citations`, and `retrievedContext`.
- Handoff responses can include `handoff`; confirmed ticket creation returns `createdTicket`.

Tickets:

- `POST /tickets`
- `GET /tickets`
- `GET /tickets/{ticket_id}`
- `PATCH /tickets/{ticket_id}`

Runtime tickets are stored in `data/support/runtime_tickets.json`. Seed tickets remain read-only in `data/support/tickets.json`.

## Phase Summary

### Phase 0: Setup

Complete. Created the project structure, backend `uv` project, starter FastAPI app, and planning docs.

### Phase 1: Data Layer

Complete. Built a normalized 50-product Electronics catalog from the UCSD/McAuley Lab Amazon Reviews 2023 metadata.

Key files:

- `backend/scripts/build_catalog.py`
- `backend/scripts/validate_catalog.py`
- `data/catalog/products.json`
- `data/catalog/categories.json`
- `docs/data-source.md`
- `docs/catalog-schema.md`

### Phase 2: UI Baseline

Complete. Created the React/Vite frontend with product listing, reusable cards, product detail views, responsive layout, and local build verification.

### Phase 3: Frontend Logic

Complete. Added search, category filtering, sorting, and local cart behavior.

### Phase 4: Backend API

Complete. Added FastAPI product/category models and endpoints, CORS, and frontend API integration.

### Phase 5: Support Knowledge Base

Complete. Built product KB documents, store policy docs, review samples, and synthetic seed tickets.

Current KB inventory:

- 50 selected products.
- 145 review samples.
- 250 product KB markdown files.
- 4 store policy markdown files.
- 20 original synthetic seed tickets, with current source inventory reporting 25 support-ticket documents.

### Phase 6: RAG Pipeline

Complete. Added document loading, normalization, chunking, embeddings, Chroma vector-store utilities, hybrid retrieval, answer generation, preview scripts, and the first backend chat endpoint.

Current vector-store status:

- Vector database: Chroma.
- Collection: `csagent_support_knowledge`.
- Persist directory: `data/vector_store/chroma`.
- Stored chunks: 907.
- Current collection embedding provider: Nebius.
- Nebius model: `Qwen/Qwen3-Embedding-8B`.
- Embedding dimension: 4096.

### Phase 7: LangGraph Support Agent

Complete. `POST /chat` now uses `run_support_agent(...)` from `rag_pipeline/support_agent.py`.

The agent handles:

- Store policy questions.
- Product questions.
- Troubleshooting.
- Compatibility.
- Comparisons.
- Review summaries.
- Catalog availability.
- Catalog ranking.
- Clarification requests.
- Escalation/handoff candidates.
- Unsupported categories.

Validation command:

```powershell
cd backend
uv run python ../rag_pipeline/validate_support_agent.py
```

### Phase 8: Chat UI

Complete. The React frontend includes a floating support chat panel wired to the LangGraph-backed backend.

Current behavior:

- Normal support mode hides citations, retrieved context, and debug traces.
- Eval mode (`?_m=e`) shows citations, retrieved snippets, and debug metadata.
- Product detail pages include product-aware starter prompts.
- Catalog availability and ranking questions are answered from `data/catalog/products.json`.
- Contact-number requests and account/order-specific questions are handled as handoff candidates without inventing support contact data.

### Phase 9: Ticket Persistence And Support Workflow

Complete. Confirmed chat handoffs can become persisted local support tickets.

Completed scope:

- Ticket schema in `backend/app/ticket_schema.py`.
- Ticket repository in `backend/app/ticket_repository.py`.
- Runtime ticket storage in `data/support/runtime_tickets.json`.
- Ticket APIs for create/list/detail/update.
- Chat handoff metadata and optional confirmed ticket creation through `POST /chat`.
- Idempotent ticket creation with `ticketRequestId` / `idempotencyKey`.
- Frontend handoff ticket creation and confirmation UI.
- Internal support console at `?_m=s#/support/tickets`.
- First-contact-resolution eval dataset in `data/support/support_eval_queries.json`.
- Ticket workflow validation in `rag_pipeline/validate_ticket_workflow.py`.

Detailed Phase 9 documentation:

- `docs/phase-9-support-workflow-tasks.md`
- `docs/ticket-schema.md`
- `docs/first-contact-resolution-eval.md`
- `docs/local-runbook.md`
- `docs/test-case-report.csv`

## Provider Status

### Working Provider

Use Chroma with Nebius embeddings for the current local RAG workflow. The current Chroma collection was built with Nebius embeddings.

### Local Backup Provider

The deterministic hashing provider remains available for local backup runs, but Chroma must be rebuilt with `--provider hashing` before retrieval or answer previews can use hashing embeddings.

Backup commands:

```powershell
cd backend
uv run python ../rag_pipeline/preview_embeddings.py --provider hashing
uv run python ../rag_pipeline/build_vector_store.py --provider hashing
uv run python ../rag_pipeline/preview_retrieval.py --provider hashing
uv run python ../rag_pipeline/preview_answers.py --provider hashing
```

### OpenAI Embeddings

OpenAI embeddings are currently blocked by quota.

The current `OPENAI_API_KEY` can list available models, including `text-embedding-3-small`, but actual embedding requests return `429 insufficient_quota`. Add billing/credits or switch to an OpenAI key/project with usable quota before running the OpenAI embedding pass.

Resume command after quota is available:

```powershell
cd backend
uv run python ../rag_pipeline/preview_embeddings.py
```

### Chat Completion

Claude through Anthropic is the natural-language final answer provider after retrieval and context sufficiency checks when `CLAUDE_API_KEY` or `ANTHROPIC_API_KEY` is available.

The final-answer path now uses LangChain `ChatPromptTemplate` in `rag_pipeline/answer_generation.py`:

- A system prompt defines the support persona: calm, concise, practical, customer-friendly, and honest about local-demo limits.
- A human prompt injects the customer question and retrieved cited source context.
- The LLM is instructed to use only supplied retrieved/catalog context and preserve bracketed citation numbers.
- Deterministic answer formatting remains the fallback when no Claude key is configured or the LLM call fails.

## Key Decisions

- Use the Electronics category.
- Start with a clean subset of 50 products.
- Build locally first.
- Keep the ecommerce site as the baseline UI.
- Use LangChain for the RAG pipeline.
- Use LangGraph for support-agent workflow orchestration.
- Use Chroma first for local vector search.
- Keep Pinecone as a later cloud vector database option.
- Keep runtime support tickets separate from synthetic seed tickets.
- Do not invent phone numbers, account records, tracking data, payment data, or order status.

## Planned Stack

- Frontend: React/Vite
- Backend: FastAPI managed with `uv`
- Data: local JSON and markdown files
- RAG framework: LangChain
- Agent workflow framework: LangGraph
- Local vector store: Chroma
- Current embedding provider: Nebius
- Planned chat-completion provider: Claude through Anthropic
- Cloud vector-store option: Pinecone

## Important Files

- `backend/app/main.py`
- `backend/app/ticket_schema.py`
- `backend/app/ticket_repository.py`
- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `rag_pipeline/support_agent.py`
- `rag_pipeline/validate_support_agent.py`
- `rag_pipeline/validate_ticket_workflow.py`
- `rag_pipeline/retrieval.py`
- `rag_pipeline/answer_generation.py`
- `data/catalog/products.json`
- `data/catalog/categories.json`
- `data/support/tickets.json`
- `data/support/runtime_tickets.json`
- `data/support/support_eval_queries.json`
- `docs/phase-9-support-workflow-tasks.md`
- `docs/ticket-schema.md`
- `docs/first-contact-resolution-eval.md`
- `docs/stakeholder-deck/csagent-stakeholder-deck.html`

## Existing Planning Documents

- `rag-ecommerce-plan.md`
- `docs/build-plan.md`
- `docs/learning-notes.md`
- `docs/phase-0-setup-tasks.md`
- `docs/phase-1-data-layer-tasks.md`
- `docs/phase-2-ui-baseline-tasks.md`
- `docs/phase-3-frontend-logic-tasks.md`
- `docs/phase-4-backend-api-tasks.md`
- `docs/phase-5-support-kb-tasks.md`
- `docs/phase-6-rag-pipeline-tasks.md`
- `docs/phase-7-langgraph-tasks.md`
- `docs/phase-8-chat-ui-tasks.md`
- `docs/phase-9-support-workflow-tasks.md`
- `docs/first-contact-resolution-eval.md`
- `docs/ticket-schema.md`

## Next Steps

1. Add product-manual-style documents or manual excerpts as a first-class document type.
2. Build the first-contact-resolution eval runner using `data/support/support_eval_queries.json`.
3. Expand LLM answer validation once a Claude/Anthropic key is available in the environment.
4. Keep deterministic answer formatting as the fallback when the LLM provider is unavailable.
5. Rebuild Chroma with OpenAI embeddings later only if switching away from Nebius.
6. Keep Pinecone as a later cloud vector database option.

## Local-First Limitations

- Runtime tickets are stored in JSON, not a production database.
- The support console is URL-mode-gated for local testing, not protected by authentication or authorization.
- No real phone, email, SMS, CRM, notification, SLA, or operator-assignment integration exists.
- Concurrent ticket writes are acceptable for local development, but production should use a database and transactional writes.
- OpenAI embedding execution remains blocked until API quota is available.
