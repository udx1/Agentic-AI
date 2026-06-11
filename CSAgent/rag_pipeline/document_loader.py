from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
CATALOG_PATH = DATA_ROOT / "catalog" / "products.json"
CATEGORIES_PATH = DATA_ROOT / "catalog" / "categories.json"
REVIEWS_PATH = DATA_ROOT / "reviews" / "product_reviews.json"
KB_ROOT = DATA_ROOT / "knowledge_base"
TICKETS_PATH = DATA_ROOT / "support" / "tickets.json"


@dataclass(frozen=True)
class KnowledgeDocument:
    page_content: str
    metadata: dict[str, Any]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_front_matter(markdown: str) -> tuple[dict[str, str], str]:
    if not markdown.startswith("---"):
        return {}, markdown.strip()

    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return {}, markdown.strip()

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata, parts[2].strip()


def relative_source(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def load_markdown_documents() -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []

    for path in sorted(KB_ROOT.rglob("*.md")):
        markdown = path.read_text(encoding="utf-8")
        front_matter, body = parse_front_matter(markdown)
        documents.append(
            KnowledgeDocument(
                page_content=body,
                metadata={
                    "source_type": "markdown",
                    "source_path": relative_source(path),
                    **front_matter,
                },
            )
        )

    return documents


def load_catalog_documents() -> list[KnowledgeDocument]:
    products = read_json(CATALOG_PATH)
    documents: list[KnowledgeDocument] = []

    for product in products:
        features = "\n".join(f"- {feature}" for feature in product["features"])
        content = f"""
Product: {product["title"]}
Brand: {product["brand"]}
Category: {product["category"]}
Subcategory: {product["subcategory"]}
Price: ${product["price"]}
Rating: {product["rating"]} out of 5
Review count: {product["reviewCount"]}
Description: {product["description"]}
Features:
{features}
"""
        documents.append(
            KnowledgeDocument(
                page_content=content.strip(),
                metadata={
                    "source_type": "catalog_json",
                    "source_path": relative_source(CATALOG_PATH),
                    "doc_type": "catalog_product",
                    "product_id": product["id"],
                    "title": product["title"],
                    "brand": product["brand"],
                    "category": product["category"],
                    "subcategory": product["subcategory"],
                },
            )
        )

    return documents


def load_category_documents() -> list[KnowledgeDocument]:
    categories = read_json(CATEGORIES_PATH)
    documents: list[KnowledgeDocument] = []

    for category in categories:
        subcategories = ", ".join(category["subcategories"])
        content = f"""
Category: {category["name"]}
Description: {category["description"]}
Mapped subcategories: {subcategories}
"""
        documents.append(
            KnowledgeDocument(
                page_content=content.strip(),
                metadata={
                    "source_type": "category_json",
                    "source_path": relative_source(CATEGORIES_PATH),
                    "doc_type": "category",
                    "category_id": category["id"],
                    "category": category["name"],
                },
            )
        )

    return documents


def load_review_documents() -> list[KnowledgeDocument]:
    reviews_by_product = read_json(REVIEWS_PATH)
    documents: list[KnowledgeDocument] = []

    for product_id, reviews in reviews_by_product.items():
        for review in reviews:
            title = review["title"] or "Untitled review"
            content = f"""
Customer review for product {product_id}
Rating: {review["rating"]} out of 5
Verified purchase: {review["verifiedPurchase"]}
Helpful votes: {review["helpfulVotes"]}
Review title: {title}
Review text: {review["text"]}
"""
            documents.append(
                KnowledgeDocument(
                    page_content=content.strip(),
                    metadata={
                        "source_type": "reviews_json",
                        "source_path": relative_source(REVIEWS_PATH),
                        "doc_type": "customer_review",
                        "product_id": product_id,
                        "review_id": review["reviewId"],
                        "asin": review["asin"],
                        "rating": review["rating"],
                        "verified_purchase": review["verifiedPurchase"],
                    },
                )
            )

    return documents


def load_ticket_documents() -> list[KnowledgeDocument]:
    tickets = read_json(TICKETS_PATH)
    documents: list[KnowledgeDocument] = []

    for ticket in tickets:
        content = f"""
Support ticket: {ticket["id"]}
Issue type: {ticket["issueType"]}
Status: {ticket["status"]}
Priority: {ticket["priority"]}
Product: {ticket["productTitle"]}
Category: {ticket["category"]}
Subcategory: {ticket["subcategory"]}
Summary: {ticket["summary"]}
"""
        documents.append(
            KnowledgeDocument(
                page_content=content.strip(),
                metadata={
                    "source_type": "tickets_json",
                    "source_path": relative_source(TICKETS_PATH),
                    "doc_type": "support_ticket",
                    "ticket_id": ticket["id"],
                    "product_id": ticket["productId"],
                    "issue_type": ticket["issueType"],
                    "status": ticket["status"],
                    "priority": ticket["priority"],
                    "category": ticket["category"],
                    "subcategory": ticket["subcategory"],
                },
            )
        )

    return documents


def load_all_documents() -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    documents.extend(load_catalog_documents())
    documents.extend(load_category_documents())
    documents.extend(load_markdown_documents())
    documents.extend(load_review_documents())
    documents.extend(load_ticket_documents())
    return documents
