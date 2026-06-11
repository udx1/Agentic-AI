from __future__ import annotations

import json
import sys
from pathlib import Path


CATALOG_PATH = Path("../data/catalog/products.json")
REVIEWS_PATH = Path("../data/reviews/product_reviews.json")
KB_ROOT = Path("../data/knowledge_base")
TICKETS_PATH = Path("../data/support/tickets.json")
REQUIRED_PRODUCT_DOCS = [
    "faq.md",
    "setup.md",
    "troubleshooting.md",
    "compatibility.md",
    "reviews.md",
]
REQUIRED_POLICY_DOCS = [
    "shipping.md",
    "returns.md",
    "warranty.md",
    "payments.md",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    products = read_json(CATALOG_PATH)
    reviews_by_product = read_json(REVIEWS_PATH)
    tickets = read_json(TICKETS_PATH)
    errors: list[str] = []

    for file_name in REQUIRED_POLICY_DOCS:
        path = KB_ROOT / "store_policies" / file_name
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"Missing or empty policy doc: {path}")

    for product in products:
        product_dir = KB_ROOT / "products" / product["id"]
        for file_name in REQUIRED_PRODUCT_DOCS:
            path = product_dir / file_name
            if not path.exists() or not path.read_text(encoding="utf-8").strip():
                errors.append(f"Missing or empty product doc: {path}")

    if len(tickets) < 10:
        errors.append("Expected at least 10 support tickets.")

    review_counts = {product["id"]: len(reviews_by_product.get(product["id"], [])) for product in products}
    products_with_reviews = sum(1 for count in review_counts.values() if count > 0)
    products_with_six_reviews = sum(1 for count in review_counts.values() if count >= 6)

    if products_with_reviews == 0:
        errors.append("No real review samples were found.")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Support KB validation passed.")
    print(f"Product docs: {len(products) * len(REQUIRED_PRODUCT_DOCS)}")
    print(f"Policy docs: {len(REQUIRED_POLICY_DOCS)}")
    print(f"Support tickets: {len(tickets)}")
    print(f"Products with reviews: {products_with_reviews}/{len(products)}")
    print(f"Products with 6+ reviews: {products_with_six_reviews}/{len(products)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
