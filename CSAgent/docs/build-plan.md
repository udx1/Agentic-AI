# Build Plan

## Goal

Build a local-first ecommerce site from a clean 50-product Electronics catalog, then add a RAG-based customer support chat agent.

## Stack

- Frontend: React with Vite
- Backend: FastAPI managed with `uv`
- Data: local JSON and markdown files
- RAG components: LangChain
- Agent workflow: LangGraph
- Local vector store: Chroma
- Later cloud vector option: Pinecone
- Models: Nebius embeddings currently; OpenAI remains planned/optional after quota is available; chat model provider is still to be finalized

## Phase Task Lists

- `docs/phase-0-setup-tasks.md`
- `docs/phase-1-data-layer-tasks.md`
- `docs/phase-2-ui-baseline-tasks.md`
- `docs/phase-3-frontend-logic-tasks.md`
- `docs/phase-4-backend-api-tasks.md`
- `docs/phase-5-support-kb-tasks.md`
- `docs/phase-6-rag-pipeline-tasks.md`
- `docs/phase-7-langgraph-tasks.md`
- `docs/phase-8-chat-ui-tasks.md`

## Phase 0: Project Setup

Status: complete

Deliverables:

- Create the initial folder structure.
- Record the stack decision.
- Add learning notes scaffolding.
- Add lightweight frontend and backend setup notes.
- Initialize the backend as a `uv` project with FastAPI and Uvicorn.

## Phase 1: Data First

Status: complete

Deliverables:

- Locate or download the UCSD Amazon Electronics dataset.
- Inspect the dataset shape.
- Select 50 clean products.
- Normalize product fields.
- Save the catalog to `data/catalog/products.json`.
- Save source notes to `docs/data-source.md`.
- Save schema notes to `docs/catalog-schema.md`.
- Add repeatable build and validation scripts.

Target product fields:

- `id`
- `title`
- `brand`
- `category`
- `subcategory`
- `price`
- `rating`
- `reviewCount`
- `image`
- `description`
- `features`

## Phase 2: UI Baseline

Status: complete

Deliverables:

- Create the React/Vite frontend project in `frontend/`.
- Load products from the local catalog data.
- Build a product listing page.
- Build reusable product cards.
- Build a product detail view.
- Add a basic responsive layout.

## Phase 3: Frontend Logic

Status: complete

Deliverables:

- Add search over product title, brand, category, subcategory, and description.
- Keep department navigation as category filtering.
- Add sorting by price, rating, and review count.
- Add cart UI.
- Add, remove, and update item quantity.
- Add cart actions from product cards and product detail pages.

## Phase 4: Backend API

Status: complete

Deliverables:

- Add FastAPI response models for products and categories.
- Add `GET /products`.
- Add `GET /products/{id}`.
- Add `GET /categories`.
- Serve catalog data from `data/catalog/products.json` and `data/catalog/categories.json`.
- Add CORS for the local Vite frontend.
- Update the frontend to fetch catalog data from the backend API.
- Remove duplicate frontend catalog JSON copies.

## Phase 5: Local Support Knowledge Base

Status: complete

Deliverables:

- Extract clean real customer review samples from the UCSD Amazon Electronics review stream.
- Store review samples in `data/reviews/product_reviews.json`.
- Create store policy markdown documents.
- Create product FAQ, setup, troubleshooting, compatibility, and review-summary documents.
- Create synthetic support tickets in `data/support/tickets.json`.
- Document the KB layout in `docs/knowledge-base.md`.
- Add repeatable KB build and validation scripts.

## Phase 6: RAG Pipeline

Status: complete

Deliverables:

- Load product, category, review, policy, and support-ticket documents into one document shape.
- Normalize document text for retrieval.
- Chunk documents into retrieval-sized passages.
- Preview embeddings in memory on a small chunk sample.
- Build the full Chroma vector store, embedding all chunks, indexing vectors, and persisting vectors locally.
- Retrieve relevant chunks from Chroma with provider-matched query embeddings.
- Generate deterministic preview answers with numbered citations.
- Add `POST /chat` in FastAPI so the backend can return cited support answers.
- Add a Python notebook client that calls the backend chat endpoint with FastAPI `TestClient`.

Important distinction:

- `preview_embeddings.py` is for small, in-memory embedding inspection.
- `build_vector_store.py` is the full embedding and Chroma persistence/indexing step.
- `preview_retrieval.py` queries the persisted Chroma store.
- `preview_answers.py` formats retrieved chunks into cited answer previews.
- Phase 6 first exposed `POST /chat`; Phase 7 now routes that endpoint through the LangGraph support-agent workflow.

## Phase 7: Support Chat Agent

Status: complete

- Add `POST /chat` to answer customer support questions from retrieved context.
- Return citations and retrieved context for transparency.
- Keep the first version deterministic and extractive so it works without chat-completion quota.
- Add LangGraph state and nodes behind the existing `/chat` endpoint.
- Route questions by intent, such as product question, policy, troubleshooting, comparison, clarification, or escalation.
- Reuse the existing retrieval and citation layer.
- Assess whether retrieved context is sufficient for a grounded answer.
- Ask for clarification when the question is too broad or underspecified.
- Prepare escalation metadata for Phase 9 ticket fallback.
- Preserve the existing `/chat` API shape for Phase 8 frontend integration.
- Add repeatable support-agent validation cases.

Deferred or dependent:

- LLM-based final answer generation depends on a usable chat model/provider.
- Ticket persistence and ticket-management endpoints remain Phase 9.
- Developer/debug trace mode remains a planned observability/eval enhancement.

## Phase 8: Chat UI

Status: next

Deliverables:

- Add a frontend support chat surface.
- Call the backend `/chat` endpoint.
- Display answer text and citations.
- Add loading and error states.
- Use `docs/phase-8-chat-ui-tasks.md` as the implementation checklist.

## Later Phases

- Phase 9: Ticket fallback
