# Phase 3 Frontend Logic Tasks

## Goal

Add ecommerce interaction logic to the React UI: search, category filtering, sorting, and a local cart.

Status: complete.

## Task List

### 1. Search

- [x] Add search input.
- [x] Search product title.
- [x] Search brand.
- [x] Search category.
- [x] Search subcategory.
- [x] Search description.
- [x] Show no-results state when nothing matches.

### 2. Category Filtering

- [x] Add department/category navigation.
- [x] Show counts per category.
- [x] Use hash-based category navigation.
- [x] Combine category filtering with search.

### 3. Sorting

- [x] Add sort control.
- [x] Sort by featured order.
- [x] Sort by price low to high.
- [x] Sort by price high to low.
- [x] Sort by rating.
- [x] Sort by review count.

### 4. Cart State

- [x] Add local cart state at the app level.
- [x] Add product-card add-to-cart action.
- [x] Add product-detail add-to-cart action.
- [x] Persist cart state in `localStorage`.
- [x] Remove stale cart entries when catalog data changes.

### 5. Cart UI

- [x] Add cart panel.
- [x] Show cart item list.
- [x] Show quantity controls.
- [x] Support quantity increase.
- [x] Support quantity decrease.
- [x] Support direct quantity edit.
- [x] Support remove item.
- [x] Show cart total.
- [x] Show empty cart state.

### 6. Internationalization Baseline

- [x] Add English text labels.
- [x] Add French text labels.
- [x] Add language toggle.
- [x] Translate category labels where available.

### 7. Verification

- [x] Run `npm run build`.
- [x] Verify search/filter/sort combinations.
- [x] Verify cart add/update/remove behavior.
- [x] Verify cart persistence after reload.

## Verification

- [x] Search, filtering, and sorting work together.
- [x] Cart workflows work from cards and detail pages.
- [x] `npm run build` succeeds.

