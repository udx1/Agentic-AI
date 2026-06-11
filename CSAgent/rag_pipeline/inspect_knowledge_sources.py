from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
CATALOG_PATH = DATA_ROOT / "catalog" / "products.json"
CATEGORIES_PATH = DATA_ROOT / "catalog" / "categories.json"
REVIEWS_PATH = DATA_ROOT / "reviews" / "product_reviews.json"
KB_ROOT = DATA_ROOT / "knowledge_base"
POLICY_ROOT = KB_ROOT / "store_policies"
PRODUCT_KB_ROOT = KB_ROOT / "products"
TICKETS_PATH = DATA_ROOT / "support" / "tickets.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def count_markdown_files(path: Path) -> int:
    if not path.exists():
        return 0
    return len(list(path.rglob("*.md")))


def main() -> int:
    products = read_json(CATALOG_PATH)
    categories = read_json(CATEGORIES_PATH)
    reviews_by_product = read_json(REVIEWS_PATH)
    tickets = read_json(TICKETS_PATH)

    product_ids = {product["id"] for product in products}
    review_counts = {
        product_id: len(reviews_by_product.get(product_id, []))
        for product_id in product_ids
    }

    ticket_issue_counts = Counter(ticket["issueType"] for ticket in tickets)

    print("Knowledge Source Inventory")
    print("=" * 28)

    print("\nCatalog")
    print(f"- Products: {len(products)}")
    print(f"- Categories: {len(categories)}")

    print("\nReviews")
    print(f"- Products with review samples: {sum(count > 0 for count in review_counts.values())}")
    print(f"- Products with 6+ review samples: {sum(count >= 6 for count in review_counts.values())}")
    print(f"- Total review samples: {sum(review_counts.values())}")

    print("\nKnowledge Base Markdown")
    print(f"- Store policy docs: {count_markdown_files(POLICY_ROOT)}")
    print(f"- Product KB docs: {count_markdown_files(PRODUCT_KB_ROOT)}")
    print(f"- Total KB markdown docs: {count_markdown_files(KB_ROOT)}")

    print("\nSupport Tickets")
    print(f"- Tickets: {len(tickets)}")
    for issue_type, count in sorted(ticket_issue_counts.items()):
        print(f"- {issue_type}: {count}")

    print("\nSource Paths")
    print(f"- Catalog: {CATALOG_PATH.relative_to(DATA_ROOT.parents[0])}")
    print(f"- Categories: {CATEGORIES_PATH.relative_to(DATA_ROOT.parents[0])}")
    print(f"- Reviews: {REVIEWS_PATH.relative_to(DATA_ROOT.parents[0])}")
    print(f"- Knowledge base: {KB_ROOT.relative_to(DATA_ROOT.parents[0])}")
    print(f"- Tickets: {TICKETS_PATH.relative_to(DATA_ROOT.parents[0])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
