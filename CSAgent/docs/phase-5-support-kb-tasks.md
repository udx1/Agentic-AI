# Phase 5 Local Support Knowledge Base Tasks

## Goal

Create a local support knowledge base tied to the 50-product catalog, including product support docs, store policies, real review samples, and synthetic support tickets.

Status: complete.

## Task List

### 1. Real Review Samples

- [x] Add `backend/scripts/build_reviews.py`.
- [x] Extract clean review samples from the UCSD Electronics review stream.
- [x] Save review samples to `data/reviews/product_reviews.json`.
- [x] Save raw selected review records to `data/raw/electronics_review_sample.jsonl`.
- [x] Keep review samples separate from `products.json`.

### 2. Store Policies

- [x] Create shipping policy markdown.
- [x] Create returns/refunds policy markdown.
- [x] Create warranty policy markdown.
- [x] Create payments policy markdown.
- [x] Store policies under `data/knowledge_base/store_policies/`.

### 3. Product Knowledge Base

- [x] Add `backend/scripts/build_support_kb.py`.
- [x] Generate product FAQ documents.
- [x] Generate product setup documents.
- [x] Generate product troubleshooting documents.
- [x] Generate product compatibility documents.
- [x] Generate review-summary documents.
- [x] Store product documents under `data/knowledge_base/products/<product_id>/`.

### 4. Synthetic Support Tickets

- [x] Generate synthetic support tickets.
- [x] Save tickets to `data/support/tickets.json`.
- [x] Include issue type, status, priority, product details, and issue text.

### 5. Metadata Design

- [x] Include document type metadata.
- [x] Include product ID where applicable.
- [x] Include category and subcategory where applicable.
- [x] Keep source paths traceable for later citations.

### 6. Validation

- [x] Add `backend/scripts/validate_support_kb.py`.
- [x] Validate product docs exist for selected catalog products.
- [x] Validate store policy docs exist.
- [x] Validate review sample JSON shape.
- [x] Validate support ticket JSON shape.

### 7. Documentation

- [x] Document the KB layout in `docs/knowledge-base.md`.
- [x] Add Phase 5 notes to `docs/learning-notes.md`.

## Verification

- [x] 250 product KB markdown documents generated.
- [x] 4 store policy markdown documents generated.
- [x] Review samples generated for available catalog products.
- [x] Synthetic support tickets generated.
- [x] KB validation passes.

