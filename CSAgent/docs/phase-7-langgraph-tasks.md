# Phase 7 LangGraph Support Agent Tasks

## Goal

Replace the original deterministic `/chat` implementation internals with a fuller LangGraph support-agent workflow while preserving the existing FastAPI API contract as much as practical.

Status: complete.

The `/chat` endpoint now routes through a LangGraph workflow with routing, context checks, clarification behavior, and escalation preparation.

## Current Baseline

- `POST /chat` exists in `backend/app/main.py` and calls `run_support_agent(...)`.
- Request body: `{ "question": "...", "provider": "nebius" }`.
- Response fields: `question`, `answer`, `provider`, `citations`, `retrievedContext`.
- Retrieval uses `rag_pipeline/retrieval.py`.
- Answer formatting uses `rag_pipeline/answer_generation.py`.
- Current Chroma index uses Nebius embeddings.
- `langgraph` is listed in `backend/pyproject.toml`.

## Phase 7 Task List

### 1. Dependency and Structure Setup

- [x] Add `langgraph` to backend dependencies.
- [x] Decide the module location for the agent workflow.
- [x] Create an agent module, likely `rag_pipeline/support_agent.py`.
- [x] Keep existing `retrieval.py` and `answer_generation.py` reusable instead of duplicating retrieval logic.

### 2. Agent State Design

- [x] Define a typed agent state with fields for question, provider, intent, product hints, retrieved results, citations, answer, confidence/sufficiency flags, and escalation metadata.
- [x] Define stable intent labels for routing.
- [x] Define a lightweight response object that can be adapted back into the existing `ChatResponse` model.

Initial intent labels:

- `store_policy`
- `product_question`
- `troubleshooting`
- `compatibility`
- `comparison`
- `review_summary`
- `clarification_needed`
- `escalation_candidate`
- `unsupported_category`

### 3. Intent Classification Node

- [x] Add deterministic keyword/rule-based intent classification first so Phase 7 works without a chat-completion model.
- [x] Detect policy questions for returns, shipping, refunds, warranty, and payments.
- [x] Detect troubleshooting questions for setup, power, pairing, charging, compatibility, and "not working" language.
- [x] Detect product-specific questions using product IDs, product names, brand names, or category terms.
- [x] Detect comparison questions using terms like compare, better, versus, vs, or difference.
- [x] Detect underspecified questions that should ask for clarification before retrieval-heavy answer generation.

### 4. Retrieval Planning Node

- [x] Map intent to retrieval strategy.
- [x] Reuse `retrieve_relevant_chunks(...)` for the first implementation.
- [x] Defer optional metadata filtering until retrieval quality requires it.
- [x] Keep the provider default as `nebius` to match the current Chroma collection.

### 5. Context Sufficiency Node

- [x] Evaluate whether retrieved context is strong enough to answer.
- [x] Start with deterministic signals such as lexical score, doc type coverage, citation count, and whether the top context matches the detected intent.
- [x] Route weak or ambiguous context to clarification or escalation preparation.
- [x] Preserve the current "not enough matching support context" behavior as a safe fallback.

### 6. Answer Generation Node

- [x] Reuse the current deterministic citation formatting for the first LangGraph implementation.
- [x] Keep citations and retrieved context in the response.
- [x] Defer deeper intent-aware answer framing until answer quality needs it.
- [x] Leave LLM-based answer generation as a later enhancement once a usable chat model/provider is selected.

### 7. Clarification Node

- [x] Generate concise clarification prompts when the question lacks a product, policy area, or problem detail.
- [x] Return the clarification through the normal `answer` field.
- [x] Include no citations when no grounded context was used.
- [x] Defer response metadata fields until the frontend or developer mode needs them.

### 8. Escalation Preparation Node

- [x] Mark questions as escalation candidates when context is weak, issue language is urgent, or the user appears to need account/order-specific help.
- [x] Prepare escalation metadata such as reason, detected intent, product hint, and summary.
- [x] Do not create persistent tickets yet; ticket creation remains Phase 9.
- [x] Keep the API response compatible with the current frontend plan.

### 9. Graph Assembly

- [x] Build the LangGraph workflow with nodes for classify, retrieve, assess, answer, clarify, and escalation preparation.
- [x] Add conditional edges based on intent and sufficiency.
- [x] Compile the graph once and expose a small function such as `run_support_agent(question, provider)`.
- [x] Keep the graph callable from tests without running Uvicorn.

### 10. FastAPI Integration

- [x] Update `/chat` to call the LangGraph support agent instead of directly calling `generate_cited_answer(...)`.
- [x] Preserve `ChatRequest` fields for now.
- [x] Preserve `ChatResponse` fields where practical.
- [x] If new metadata is needed, add it carefully and document the response shape before Phase 8.

### 11. Verification

- [x] Add or run `TestClient` checks for a return-policy question.
- [x] Add or run checks for a product setup question.
- [x] Add or run checks for a troubleshooting question.
- [x] Add or run checks for a comparison question.
- [x] Add or run checks for an underspecified clarification question.
- [x] Add or run checks for a weak-context escalation candidate.
- [x] Confirm Nebius retrieval still works with the existing Chroma store.

### 12. Documentation Update

- [x] Update `PROJECT_STATUS.md` after each completed Phase 7 milestone.
- [x] Add learning notes explaining how the LangGraph nodes and conditional edges map to the support workflow.
- [x] Keep `rag_pipeline/rag_pipeline_walkthrough.ipynb` updated as the LangGraph agent design and implementation progress.
- [x] Update the resume point once `/chat` is backed by the LangGraph workflow.

## Suggested First Implementation Slice

1. Add `langgraph`.
2. Create `rag_pipeline/support_agent.py`.
3. Implement typed state and deterministic intent classification.
4. Wrap existing retrieval and deterministic answer generation in graph nodes.
5. Wire `/chat` to `run_support_agent(...)`.
6. Verify the existing return-policy question still works.

This keeps the first LangGraph version small: it changes orchestration before changing answer quality.
