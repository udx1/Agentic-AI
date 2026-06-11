# Phase 0 Project Setup Tasks

## Goal

Create the initial local-first project structure and establish the stack for the ecommerce app plus future RAG support agent.

Status: complete.

## Task List

### 1. Project Structure

- [x] Create root project folder.
- [x] Create `backend/`.
- [x] Create `frontend/`.
- [x] Create `data/`.
- [x] Create `docs/`.
- [x] Create initial planning documents.

### 2. Backend Setup

- [x] Initialize `backend/` as a `uv` Python project.
- [x] Add FastAPI.
- [x] Add Uvicorn.
- [x] Add starter backend app.
- [x] Add `GET /health`.
- [x] Verify the backend can run locally.

### 3. Frontend Plan

- [x] Choose React/Vite for the frontend.
- [x] Defer frontend scaffold to Phase 2.
- [x] Keep Phase 0 focused on backend foundation and folder layout.

### 4. Stack Decisions

- [x] Use React/Vite for the frontend.
- [x] Use FastAPI for the backend.
- [x] Use local JSON and markdown files for data.
- [x] Use LangChain for RAG pipeline components.
- [x] Use LangGraph for support-agent workflow.
- [x] Use Chroma as the first local vector database.
- [x] Keep Pinecone as a later cloud vector database option.

### 5. Documentation

- [x] Add `docs/build-plan.md`.
- [x] Add `docs/learning-notes.md`.
- [x] Add root-level project status tracking.

## Verification

- [x] Backend project exists.
- [x] FastAPI app imports.
- [x] `GET /health` returns a basic status response.

