from __future__ import annotations

import re

from document_loader import KnowledgeDocument, load_all_documents


def normalize_whitespace(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def normalize_booleans(value: str) -> str:
    value = value.replace("Verified purchase: True", "Verified purchase: yes")
    value = value.replace("Verified purchase: False", "Verified purchase: no")
    value = value.replace("verified purchase: True", "verified purchase: yes")
    value = value.replace("verified purchase: False", "verified purchase: no")
    return value


def metadata_context(metadata: dict) -> list[str]:
    lines: list[str] = []

    doc_type = metadata.get("doc_type")
    if doc_type:
        lines.append(f"Document type: {doc_type}.")

    if doc_type == "catalog_product":
        return lines
    if doc_type == "category":
        return lines

    product_id = metadata.get("product_id")
    title = metadata.get("title")
    if product_id and title:
        lines.append(f"Product: {title}.")
        lines.append(f"Product ID: {product_id}.")
    elif product_id:
        lines.append(f"Product ID: {product_id}.")

    brand = metadata.get("brand")
    if brand:
        lines.append(f"Brand: {brand}.")

    category = metadata.get("category")
    if category:
        lines.append(f"Category: {category}.")

    subcategory = metadata.get("subcategory")
    if subcategory:
        lines.append(f"Subcategory: {subcategory}.")

    policy = metadata.get("policy")
    if policy:
        lines.append(f"Policy: {policy}.")

    issue_type = metadata.get("issue_type")
    if issue_type:
        lines.append(f"Issue type: {issue_type}.")

    return lines


def normalize_document(document: KnowledgeDocument) -> KnowledgeDocument:
    content = normalize_booleans(document.page_content)
    content = normalize_whitespace(content)
    context_lines = metadata_context(document.metadata)

    if context_lines:
        content = "\n".join(context_lines) + "\n\n" + content

    return KnowledgeDocument(
        page_content=content,
        metadata={**document.metadata, "normalized": True},
    )


def normalize_documents(documents: list[KnowledgeDocument]) -> list[KnowledgeDocument]:
    return [normalize_document(document) for document in documents]


def load_normalized_documents() -> list[KnowledgeDocument]:
    return normalize_documents(load_all_documents())
