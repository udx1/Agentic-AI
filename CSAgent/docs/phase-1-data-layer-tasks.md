# Phase 1 Data Layer Tasks

## Goal

Build a clean 50-product Electronics catalog from the UCSD/McAuley Lab Amazon Reviews 2023 dataset.

Status: complete.

## Task List

### 1. Source Dataset

- [x] Use the UCSD/McAuley Lab Amazon Reviews 2023 Electronics metadata.
- [x] Stream or inspect the source dataset without loading the full file into memory.
- [x] Select clean product records suitable for a storefront demo.
- [x] Keep selected raw records for traceability.

### 2. Catalog Builder

- [x] Add `backend/scripts/build_catalog.py`.
- [x] Normalize source records into frontend-friendly product fields.
- [x] Generate `data/catalog/products.json`.
- [x] Save selected source records to `data/raw/electronics_sample.jsonl`.

### 3. Product Schema

- [x] Include `id`.
- [x] Include `title`.
- [x] Include `brand`.
- [x] Include `category`.
- [x] Include `subcategory`.
- [x] Include `price`.
- [x] Include `rating`.
- [x] Include `reviewCount`.
- [x] Include `image`.
- [x] Include `description`.
- [x] Include `features`.

### 4. Validation

- [x] Add `backend/scripts/validate_catalog.py`.
- [x] Validate required fields.
- [x] Validate usable image and text fields.
- [x] Validate numeric fields such as price, rating, and review count.
- [x] Confirm the final subset contains 50 products.

### 5. Documentation

- [x] Document the dataset source in `docs/data-source.md`.
- [x] Document the normalized schema in `docs/catalog-schema.md`.
- [x] Add Phase 1 notes to `docs/learning-notes.md`.

## Verification

- [x] `data/catalog/products.json` exists.
- [x] `data/raw/electronics_sample.jsonl` exists.
- [x] Catalog validation passes.

