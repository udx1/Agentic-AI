# Data

Local data is organized by source and use.

- `raw/`: source datasets before cleaning
- `catalog/`: normalized ecommerce product catalog and category definitions
- `reviews/`: selected customer review samples for support and RAG context
- `knowledge_base/`: markdown support documents for retrieval
- `support/`: local synthetic support tickets

Phase 1 outputs:

- `catalog/products.json`: normalized 50-product Electronics catalog
- `catalog/categories.json`: shopper-facing category groups
- `raw/electronics_sample.jsonl`: raw metadata records used to build the catalog
