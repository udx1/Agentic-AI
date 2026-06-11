from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


CATALOG_PATH = Path("../data/catalog/products.json")
CATEGORIES_PATH = Path("../data/catalog/categories.json")
REQUIRED_FIELDS = {
    "id": str,
    "title": str,
    "brand": str,
    "category": str,
    "subcategory": str,
    "price": (int, float),
    "rating": (int, float),
    "reviewCount": int,
    "image": str,
    "description": str,
    "features": list,
}


def validate_product(product: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in product:
            errors.append(f"Product {index} is missing `{field}`.")
            continue
        if not isinstance(product[field], expected_type):
            errors.append(f"Product {index} has invalid `{field}` type.")

    for field in ("id", "title", "brand", "category", "image", "description"):
        if not str(product.get(field, "")).strip():
            errors.append(f"Product {index} has blank `{field}`.")

    if product.get("price", 0) <= 0:
        errors.append(f"Product {index} has non-positive price.")
    if not 1 <= product.get("rating", 0) <= 5:
        errors.append(f"Product {index} has rating outside 1-5.")
    if product.get("reviewCount", 0) < 10:
        errors.append(f"Product {index} has fewer than 10 reviews.")
    if not product.get("features"):
        errors.append(f"Product {index} has no features.")

    return errors


def main() -> int:
    products = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    categories = json.loads(CATEGORIES_PATH.read_text(encoding="utf-8"))
    category_names = {category["name"] for category in categories}
    errors: list[str] = []

    if len(products) != 50:
        errors.append(f"Expected 50 products, found {len(products)}.")

    ids = [product.get("id") for product in products]
    if len(ids) != len(set(ids)):
        errors.append("Product IDs must be unique.")

    for index, product in enumerate(products, start=1):
        errors.extend(validate_product(product, index))
        if product.get("category") not in category_names:
            errors.append(f"Product {index} has unknown category `{product.get('category')}`.")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Catalog validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
