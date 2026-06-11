# Phase 4 Backend API Tasks

## Goal

Move catalog access behind FastAPI endpoints and connect the React frontend to the backend.

Status: complete.

## Task List

### 1. Backend Models

- [x] Add FastAPI product response model.
- [x] Add category response model.
- [x] Add review response model for later review endpoints.
- [x] Load JSON catalog data from `data/catalog/`.

### 2. Catalog Endpoints

- [x] Add `GET /products`.
- [x] Add `GET /products/{product_id}`.
- [x] Add `GET /categories`.
- [x] Return 404 when a product ID is not found.

### 3. Reviews Endpoint

- [x] Add `GET /products/{product_id}/reviews`.
- [x] Return review samples for the selected product.
- [x] Return an empty list when no review samples exist.

### 4. CORS

- [x] Add CORS middleware.
- [x] Allow local Vite origins.
- [x] Support frontend requests from `http://127.0.0.1:5173`.
- [x] Support frontend requests from `http://localhost:5173`.

### 5. Frontend Integration

- [x] Add `apiBaseUrl`.
- [x] Fetch products from `GET /products`.
- [x] Fetch categories from `GET /categories`.
- [x] Fetch reviews from `GET /products/{product_id}/reviews`.
- [x] Add loading states.
- [x] Add API error states.
- [x] Remove duplicate frontend catalog JSON files.

### 6. Verification

- [x] Verify `GET /health`.
- [x] Verify `GET /products`.
- [x] Verify `GET /products/{product_id}`.
- [x] Verify `GET /categories`.
- [x] Verify product review endpoint.
- [x] Run `npm run build`.

## Verification

- [x] Backend serves catalog data.
- [x] Frontend loads catalog from backend.
- [x] Frontend review section loads backend review samples.

