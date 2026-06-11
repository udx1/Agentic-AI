# Knowledge Base

Phase 5 creates local support knowledge for retrieval.

## Structure

```text
data/
  reviews/
    product_reviews.json
  knowledge_base/
    store_policies/
      shipping.md
      returns.md
      warranty.md
      payments.md
    products/
      <product_id>/
        faq.md
        setup.md
        troubleshooting.md
        compatibility.md
        reviews.md
  support/
    tickets.json
```

## Product Documents

Each selected product has five markdown documents:

- `faq.md`
- `setup.md`
- `troubleshooting.md`
- `compatibility.md`
- `reviews.md`

Each product document starts with front matter:

```text
doc_type
product_id
title
brand
category
subcategory
```

This metadata is intended for filtering and citations during retrieval.

## Review Coverage

Reviews are sourced from the UCSD/McAuley Lab Amazon Reviews 2023 Electronics review stream.

The current extraction scanned 5,000,000 review records:

- Products with at least one clean review sample: 39 of 50
- Products with 6 or more clean review samples: 17 of 50

For products without review samples, `reviews.md` explicitly says no clean review sample was found and directs the future agent to use catalog fields, support docs, and store policies.

## Validation

Run:

```powershell
cd backend
uv run python scripts/validate_support_kb.py
```
