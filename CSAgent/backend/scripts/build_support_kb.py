from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CATALOG_PATH = Path("../data/catalog/products.json")
REVIEWS_PATH = Path("../data/reviews/product_reviews.json")
KB_ROOT = Path("../data/knowledge_base")
SUPPORT_ROOT = Path("../data/support")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "product"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def product_metadata(product: dict[str, Any], doc_type: str) -> str:
    return "\n".join(
        [
            "---",
            f"doc_type: {doc_type}",
            f"product_id: {product['id']}",
            f"title: {product['title']}",
            f"brand: {product['brand']}",
            f"category: {product['category']}",
            f"subcategory: {product['subcategory']}",
            "---",
            "",
        ]
    )


def build_faq(product: dict[str, Any]) -> str:
    features = "\n".join(f"- {feature}" for feature in product["features"][:4])
    return f"""
{product_metadata(product, "product_faq")}
# FAQ: {product["title"]}

## What is this product?

{product["title"]} is a {product["subcategory"]} item from {product["brand"]} in the {product["category"]} department.

## What are the key features?

{features}

## What should customers check before buying?

- Confirm that the product category matches the intended device or setup.
- Review the listed features and product image before purchase.
- Check compatibility notes for size, connector, model, or mounting requirements.

## What is the listed rating?

The catalog rating is {product["rating"]} out of 5 based on {product["reviewCount"]} ratings or reviews at crawl time.
"""


def build_setup(product: dict[str, Any]) -> str:
    return f"""
{product_metadata(product, "setup")}
# Setup Notes: {product["title"]}

## Before Setup

- Inspect the package and product for visible damage.
- Compare the product with the intended device, cable, slot, mount, or accessory location.
- Keep packaging until setup is complete in case a return or exchange is needed.

## Basic Setup Steps

1. Read the product description and feature list.
2. Power down connected electronics before installing accessories, cables, storage, or internal components.
3. Attach, insert, mount, or pair the product according to the device requirements.
4. Test the product with a simple use case before relying on it for daily use.

## Product-Specific Reminder

This item is categorized as {product["subcategory"]}. Check fit and compatibility carefully when using it with devices from other brands or model years.
"""


def build_troubleshooting(product: dict[str, Any]) -> str:
    return f"""
{product_metadata(product, "troubleshooting")}
# Troubleshooting: {product["title"]}

## Common Issues

- Product does not fit the target device or mounting point.
- Accessory is recognized inconsistently by the connected device.
- Audio, storage, display, or charging performance is lower than expected.
- Customer expected an included device that is not part of the package.

## Recommended Checks

1. Confirm the exact product title, brand, and subcategory.
2. Re-check model, connector, size, voltage, storage format, or mounting compatibility.
3. Disconnect and reconnect cables or accessories firmly.
4. Test with another compatible device when available.
5. If the item appears defective, start a warranty or return request.

## Escalation Guidance

Create a support ticket when the customer reports damage, missing parts, repeated failure after setup checks, or uncertainty about compatibility.
"""


def build_compatibility(product: dict[str, Any]) -> str:
    return f"""
{product_metadata(product, "compatibility")}
# Compatibility Notes: {product["title"]}

## Category

- Department: {product["category"]}
- Subcategory: {product["subcategory"]}
- Brand: {product["brand"]}

## Compatibility Rules

- Match the product to the exact device model, port, physical dimensions, or mounting style.
- For cases, covers, bands, screens, and stands, verify model year and size.
- For cables, cards, drives, and components, verify connector type, capacity support, and operating system support.
- For cameras, optics, and audio products, verify lens mount, battery model, speaker size, impedance, or accessory standard.

## When to Ask for Clarification

Ask the customer for their device model and intended use when compatibility cannot be confirmed from the product title, features, or description.
"""


def build_store_policy_docs() -> dict[str, str]:
    return {
        "shipping.md": """
---
doc_type: store_policy
policy: shipping
---

# Shipping Policy

Orders are prepared for shipment after payment is accepted.

## Standard Shipping

- Standard shipping usually arrives within 5 to 7 business days.
- Tracking information is provided when a carrier scan is available.
- Some electronics accessories may ship separately if sourced from different inventory locations.

## Delivery Issues

Customers should contact support if tracking has not updated for more than 3 business days, the package is marked delivered but missing, or the shipment arrives damaged.
""",
        "returns.md": """
---
doc_type: store_policy
policy: returns
---

# Returns and Refunds

Most unopened or gently tested electronics products can be returned within 30 days of delivery.

## Return Conditions

- Include all original accessories, manuals, packaging, and parts.
- Remove personal data from storage devices, laptops, cameras, and connected electronics.
- Items damaged by misuse may be ineligible for refund.

## Refund Timing

Refunds are processed after the returned item is received and inspected.
""",
        "warranty.md": """
---
doc_type: store_policy
policy: warranty
---

# Warranty Policy

Warranty coverage depends on the product brand and product type.

## Covered Issues

- Defects in materials or workmanship.
- Early failure under normal use.
- Missing parts discovered during initial setup.

## Not Covered

- Accidental damage.
- Water damage unless the product is explicitly rated for it.
- Compatibility issues caused by unsupported devices.
""",
        "payments.md": """
---
doc_type: store_policy
policy: payments
---

# Payments Policy

The store accepts major credit cards and common digital payment methods.

## Payment Problems

Customers should verify billing address, card security code, available balance, and bank authorization.

## Order Holds

Orders may be held for fraud review, payment mismatch, or incomplete customer information.
""",
    }


def build_support_tickets(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tickets = []
    issue_types = [
        ("compatibility", "Customer is unsure whether the item fits their device model."),
        ("setup", "Customer needs help with first-time setup."),
        ("defect", "Customer reports the product does not work after basic troubleshooting."),
        ("missing_parts", "Customer reports a missing accessory or part."),
        ("return", "Customer wants to start a return after checking compatibility."),
    ]
    for index, product in enumerate(products[:20], start=1):
        issue_type, summary = issue_types[(index - 1) % len(issue_types)]
        tickets.append(
            {
                "id": f"TICKET-{index:04d}",
                "productId": product["id"],
                "productTitle": product["title"],
                "category": product["category"],
                "subcategory": product["subcategory"],
                "issueType": issue_type,
                "summary": summary,
                "status": "open" if index % 3 else "resolved",
                "priority": "high" if issue_type == "defect" else "normal",
            }
        )
    return tickets


def build_review_summary(product: dict[str, Any], reviews: list[dict[str, Any]]) -> str:
    if not reviews:
        return f"""
{product_metadata(product, "review_summary")}
# Review Summary: {product["title"]}

No clean customer review sample was found for this selected product during Phase 5 review extraction.

Use catalog fields, product support docs, and store policies when answering customer questions about this product.
"""

    review_lines = []
    for review in reviews:
        title = review["title"] or "Untitled review"
        review_lines.append(
            f"- Rating {review['rating']}/5, verified purchase: {review['verifiedPurchase']}. "
            f"{title}: {review['text']}"
        )

    return f"""
{product_metadata(product, "review_summary")}
# Customer Review Sample: {product["title"]}

These are clean customer review excerpts from the source dataset for the selected catalog product.

{chr(10).join(review_lines)}
"""


def main() -> int:
    products = read_json(CATALOG_PATH)
    reviews_by_product = read_json(REVIEWS_PATH) if REVIEWS_PATH.exists() else {}

    for file_name, content in build_store_policy_docs().items():
        write_text(KB_ROOT / "store_policies" / file_name, content)

    for product in products:
        product_dir = KB_ROOT / "products" / product["id"]
        write_text(product_dir / "faq.md", build_faq(product))
        write_text(product_dir / "setup.md", build_setup(product))
        write_text(product_dir / "troubleshooting.md", build_troubleshooting(product))
        write_text(product_dir / "compatibility.md", build_compatibility(product))
        write_text(product_dir / "reviews.md", build_review_summary(product, reviews_by_product.get(product["id"], [])))

    write_json(SUPPORT_ROOT / "tickets.json", build_support_tickets(products))

    print(f"Wrote product KB docs for {len(products)} products.")
    print("Wrote 4 store policy docs.")
    print("Wrote support tickets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
