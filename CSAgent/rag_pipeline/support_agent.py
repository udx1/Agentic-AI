from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal, TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph

from answer_generation import Citation, build_cited_answer_from_results
from retrieval import DEFAULT_RETRIEVAL_PROVIDER, RetrievalResult, retrieve_relevant_chunks


ProviderName = Literal["hashing", "openai", "nebius"]

SupportIntent = Literal[
    "store_policy",
    "product_question",
    "troubleshooting",
    "compatibility",
    "comparison",
    "review_summary",
    "catalog_availability",
    "catalog_ranking",
    "clarification_needed",
    "escalation_candidate",
    "unsupported_category",
]


class EscalationMetadata(TypedDict, total=False):
    reason: str
    detected_intent: SupportIntent
    product_hint: str
    summary: str


class TicketProductPayload(TypedDict, total=False):
    productId: str | None
    productTitle: str | None
    category: str | None
    subcategory: str | None


class TicketHandoffPayload(TypedDict, total=False):
    question: str | None
    conversationExcerpt: str | None
    escalationReason: str | None
    agentIntent: str | None
    retrievalSufficient: bool | None


class TicketCreatePayload(TypedDict, total=False):
    issueType: str
    summary: str
    priority: str
    source: str
    product: TicketProductPayload
    handoff: TicketHandoffPayload
    contactPreference: str


class HandoffMetadata(TypedDict, total=False):
    canCreateTicket: bool
    reason: str
    ticketPayload: TicketCreatePayload


class SupportAgentState(TypedDict, total=False):
    question: str
    provider: ProviderName
    intent: SupportIntent
    product_hints: list[str]
    retrieval_query: str
    retrieval_k: int
    retrieval_candidate_count: int
    retrieved_results: list[RetrievalResult]
    citations: list[Citation]
    catalog_matches: list[dict[str, object]]
    answer: str
    has_enough_context: bool
    needs_clarification: bool
    escalation: EscalationMetadata | None
    handoff: HandoffMetadata | None


@dataclass(frozen=True)
class ProductHint:
    product_id: str
    title: str
    brand: str
    category: str
    subcategory: str


@dataclass(frozen=True)
class SupportAgentResult:
    question: str
    answer: str
    provider: ProviderName
    intent: SupportIntent
    citations: list[Citation] = field(default_factory=list)
    retrieved_results: list[RetrievalResult] = field(default_factory=list)
    has_enough_context: bool = False
    needs_clarification: bool = False
    escalation: EscalationMetadata | None = None
    handoff: HandoffMetadata | None = None
    debug: dict[str, object] | None = None


def retrieval_debug_item(result: RetrievalResult, rank: int) -> dict[str, object]:
    metadata = result.document.metadata
    return {
        "rank": rank,
        "docType": str(metadata.get("doc_type", "unknown")),
        "sourcePath": str(metadata.get("source_path", "unknown")),
        "chunkId": str(metadata.get("chunk_id", "unknown")),
        "productId": (
            str(metadata["product_id"])
            if metadata.get("product_id") is not None
            else None
        ),
        "vectorScore": "inf" if result.vector_score == float("inf") else result.vector_score,
        "lexicalScore": result.lexical_score,
    }


def debug_metadata_from_state(state: SupportAgentState) -> dict[str, object]:
    results = state.get("retrieved_results", [])
    graph_path: list[str] = ["classify"]
    intent = state.get("intent", "clarification_needed")
    if intent == "escalation_candidate":
        graph_path.append("escalate")
    elif intent == "catalog_availability":
        graph_path.append("answer_catalog")
    elif intent == "catalog_ranking":
        graph_path.append("rank_catalog")
    elif intent in {"clarification_needed", "unsupported_category"}:
        graph_path.append("clarify")
    else:
        graph_path.extend(["retrieve", "assess"])
        graph_path.append("answer" if state.get("has_enough_context") else "clarify")

    return {
        "intent": intent,
        "productHints": state.get("product_hints", []),
        "retrievalPlan": {
            "query": state.get("retrieval_query", ""),
            "k": state.get("retrieval_k", 0),
            "candidateCount": state.get("retrieval_candidate_count", 0),
            "provider": state.get("provider", DEFAULT_RETRIEVAL_PROVIDER),
        },
        "contextAssessment": {
            "hasEnoughContext": state.get("has_enough_context", False),
            "needsClarification": state.get("needs_clarification", False),
            "expectedDocTypes": sorted(
                expected_doc_types_for_intent(state.get("intent", "clarification_needed"))
            ),
            "returnedDocTypes": sorted(result_doc_types(results)),
        },
        "graphPath": graph_path,
        "escalation": state.get("escalation"),
        "handoff": state.get("handoff"),
        "retrievedResults": [
            retrieval_debug_item(result, rank)
            for rank, result in enumerate(results, start=1)
        ],
    }


def initial_support_state(
    question: str,
    provider: ProviderName = DEFAULT_RETRIEVAL_PROVIDER,
) -> SupportAgentState:
    return {
        "question": question.strip(),
        "provider": provider,
        "product_hints": [],
        "retrieved_results": [],
        "citations": [],
        "answer": "",
        "has_enough_context": False,
        "needs_clarification": False,
        "escalation": None,
        "handoff": None,
    }


REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = REPO_ROOT / "data" / "catalog" / "products.json"
PRODUCT_ID_PATTERN = re.compile(r"\bB[A-Z0-9]{9}\b", re.IGNORECASE)

POLICY_KEYWORDS = {
    "return",
    "returns",
    "refund",
    "refunds",
    "shipping",
    "ship",
    "delivery",
    "warranty",
    "payment",
    "payments",
    "policy",
}
CATALOG_AVAILABILITY_KEYWORDS = {
    "available",
    "availability",
    "carry",
    "carries",
    "catalog",
    "device",
    "devices",
    "have",
    "in",
    "looking",
    "sell",
    "show",
    "stock",
    "store",
}
CATALOG_RANKING_KEYWORDS = {
    "best",
    "cheapest",
    "costliest",
    "expensive",
    "highest",
    "least",
    "lowest",
    "most",
    "popular",
    "rank",
    "ranking",
    "rated",
    "reviewed",
    "reviews",
    "top",
}
TROUBLESHOOTING_KEYWORDS = {
    "broken",
    "charge",
    "charging",
    "connect",
    "connection",
    "fix",
    "issue",
    "pair",
    "pairing",
    "power",
    "problem",
    "setup",
    "troubleshoot",
    "troubleshooting",
    "working",
}
DEFECT_KEYWORDS = {
    "broken",
    "damage",
    "damaged",
    "defect",
    "defective",
    "failed",
    "failure",
    "malfunction",
    "shattered",
    "unsafe",
}
MISSING_PART_KEYWORDS = {
    "accessory",
    "accessories",
    "component",
    "components",
    "missing",
    "part",
    "parts",
    "piece",
    "pieces",
}
PAYMENT_HANDOFF_KEYWORDS = {
    "card",
    "charge",
    "charged",
    "double",
    "payment",
    "payments",
    "transaction",
}
SHIPPING_HANDOFF_KEYWORDS = {
    "delivered",
    "delivery",
    "package",
    "shipment",
    "shipping",
    "tracking",
}
COMPATIBILITY_KEYWORDS = {
    "compatible",
    "compatibility",
    "fit",
    "fits",
    "model",
    "version",
    "works",
}
COMPARISON_KEYWORDS = {
    "better",
    "compare",
    "comparison",
    "difference",
    "differences",
    "versus",
    "vs",
}
REVIEW_KEYWORDS = {
    "customers",
    "reviews",
    "ratings",
    "feedback",
    "say",
}
ACCOUNT_OR_ORDER_KEYWORDS = {
    "account",
    "address",
    "cancel",
    "invoice",
    "order",
    "personal",
    "tracking",
}
CONTACT_SUPPORT_KEYWORDS = {
    "agent",
    "call",
    "contact",
    "email",
    "helpdesk",
    "human",
    "number",
    "phone",
    "representative",
    "specialist",
    "support",
}
URGENT_SUPPORT_KEYWORDS = {
    "burn",
    "burning",
    "danger",
    "dangerous",
    "fire",
    "injury",
    "overheat",
    "overheating",
    "smoke",
    "smoked",
    "sparks",
    "unsafe",
}
REPEATED_UNRESOLVED_KEYWORDS = {
    "again",
    "already",
    "keeps",
    "multiple",
    "repeated",
    "still",
    "tried",
    "unresolved",
}
UNSUPPORTED_CATEGORY_KEYWORDS = {
    "apparel",
    "blouse",
    "clothes",
    "clothing",
    "dress",
    "fashion",
    "jacket",
    "jeans",
    "pants",
    "shirt",
    "shoes",
    "shorts",
    "skirt",
    "sneakers",
    "socks",
    "sweater",
}
QUESTION_DETAIL_KEYWORDS = (
    POLICY_KEYWORDS
    | CATALOG_AVAILABILITY_KEYWORDS
    | CATALOG_RANKING_KEYWORDS
    | TROUBLESHOOTING_KEYWORDS
    | DEFECT_KEYWORDS
    | MISSING_PART_KEYWORDS
    | PAYMENT_HANDOFF_KEYWORDS
    | SHIPPING_HANDOFF_KEYWORDS
    | COMPATIBILITY_KEYWORDS
    | COMPARISON_KEYWORDS
    | REVIEW_KEYWORDS
    | ACCOUNT_OR_ORDER_KEYWORDS
    | CONTACT_SUPPORT_KEYWORDS
    | URGENT_SUPPORT_KEYWORDS
    | UNSUPPORTED_CATEGORY_KEYWORDS
)
CATALOG_QUERY_STOP_WORDS = {
    "a",
    "an",
    "any",
    "are",
    "available",
    "availability",
    "carry",
    "carries",
    "catalog",
    "device",
    "devices",
    "do",
    "does",
    "for",
    "have",
    "i",
    "am",
    "in",
    "is",
    "looking",
    "me",
    "not",
    "sell",
    "show",
    "stock",
    "store",
    "the",
    "there",
    "you",
    "yes",
}
CATALOG_RANKING_STOP_WORDS = CATALOG_QUERY_STOP_WORDS | {
    "best",
    "by",
    "cheapest",
    "costliest",
    "expensive",
    "highest",
    "least",
    "list",
    "lowest",
    "most",
    "popular",
    "products",
    "rank",
    "ranking",
    "rated",
    "review",
    "reviewed",
    "reviews",
    "show",
    "top",
    "with",
}
CATALOG_SYNONYMS = {
    "camera": {"camera", "cameras", "optics"},
    "cameras": {"camera", "cameras", "optics"},
    "fitness": {"fitness", "activity", "tracker", "trackers"},
    "laptop": {"laptop", "notebook", "computer", "computers"},
    "laptops": {"laptop", "notebook", "computer", "computers"},
    "notebook": {"laptop", "notebook", "computer", "computers"},
    "notebooks": {"laptop", "notebook", "computer", "computers"},
    "tracker": {"fitness", "activity", "tracker", "trackers"},
    "trackers": {"fitness", "activity", "tracker", "trackers"},
    "watch": {"watch", "watches", "tracker", "trackers"},
    "watches": {"watch", "watches", "tracker", "trackers"},
}


def question_tokens(question: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", question.lower()))


@lru_cache
def load_product_hints() -> tuple[ProductHint, ...]:
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    return tuple(
        ProductHint(
            product_id=str(product["id"]),
            title=str(product["title"]),
            brand=str(product["brand"]),
            category=str(product["category"]),
            subcategory=str(product["subcategory"]),
        )
        for product in products
    )


@lru_cache
def load_catalog_products() -> tuple[dict[str, object], ...]:
    return tuple(json.loads(PRODUCTS_PATH.read_text(encoding="utf-8")))


def expanded_catalog_tokens(value: str) -> set[str]:
    tokens = question_tokens(value)
    expanded = set(tokens)
    for token in tokens:
        expanded.update(CATALOG_SYNONYMS.get(token, set()))
    return expanded


def availability_query_tokens(question: str) -> set[str]:
    return {
        token
        for token in expanded_catalog_tokens(question)
        if token not in CATALOG_QUERY_STOP_WORDS
    }


def availability_display_terms(question: str) -> str:
    excluded_terms = catalog_exclusion_tokens(question)
    terms = [
        token
        for token in question_tokens(question)
        if token not in CATALOG_QUERY_STOP_WORDS and token not in excluded_terms
    ]
    return " ".join(terms) if terms else question


def is_catalog_availability_question(question: str) -> bool:
    question_lower = question.lower()
    tokens = question_tokens(question)
    phrase_match = any(
        phrase in question_lower
        for phrase in (
            "do you have",
            "does the store have",
            "is there",
            "in stock",
            "available",
            "do you sell",
            "do you carry",
            "i am looking for",
            "i'm looking for",
            "looking for",
            "show me",
        )
    )
    return phrase_match or bool(tokens & {"available", "availability", "stock"})


def is_catalog_ranking_question(question: str) -> bool:
    question_lower = question.lower()
    tokens = question_tokens(question)
    if not (tokens & CATALOG_RANKING_KEYWORDS):
        return False
    if "review" in tokens or "reviews" in tokens:
        return bool(tokens & {"top", "most", "highest", "least", "lowest", "best"})
    ranking_phrases = (
        "top ",
        "highest rated",
        "most reviewed",
        "cheapest",
        "lowest price",
        "most expensive",
        "highest price",
        "best rated",
    )
    return any(phrase in question_lower for phrase in ranking_phrases)


def is_contact_request(question: str) -> bool:
    question_lower = question.lower()
    tokens = question_tokens(question)
    contact_phrases = (
        "contact number",
        "support number",
        "phone number",
        "support contact",
        "customer support",
        "talk to",
        "speak to",
        "call support",
        "contact support",
    )
    return any(phrase in question_lower for phrase in contact_phrases) or bool(
        tokens & {"phone", "email", "helpdesk"}
    )


def is_ticket_handoff_question(question: str) -> bool:
    question_lower = question.lower()
    tokens = question_tokens(question)
    if is_contact_request(question):
        return True
    if tokens & ACCOUNT_OR_ORDER_KEYWORDS:
        return True
    if tokens & URGENT_SUPPORT_KEYWORDS:
        return True
    if tokens & DEFECT_KEYWORDS:
        return True
    if tokens & MISSING_PART_KEYWORDS:
        return True
    if tokens & PAYMENT_HANDOFF_KEYWORDS and (
        tokens & {"card", "charged", "double", "transaction"}
        or "charged twice" in question_lower
    ):
        return True
    if tokens & SHIPPING_HANDOFF_KEYWORDS and (
        tokens & {"delivered", "missing", "tracking", "package", "shipment"}
        or "marked delivered" in question_lower
        or "cannot be found" in question_lower
    ):
        return True
    if tokens & TROUBLESHOOTING_KEYWORDS and tokens & REPEATED_UNRESOLVED_KEYWORDS:
        return True
    return False


def catalog_product_search(question: str, limit: int = 5) -> list[dict[str, object]]:
    query_tokens = availability_query_tokens(question)
    if not query_tokens:
        return []

    exclusion_tokens = catalog_exclusion_tokens(question)
    require_tracker_device = is_fitness_tracker_device_request(question)
    ranked: list[tuple[int, dict[str, object]]] = []
    for product in load_catalog_products():
        if product_contains_excluded_terms(product, exclusion_tokens):
            continue
        if require_tracker_device and not product_matches_tracker_device(product):
            continue
        title_tokens = expanded_catalog_tokens(str(product.get("title", "")))
        brand_tokens = expanded_catalog_tokens(str(product.get("brand", "")))
        category_tokens = expanded_catalog_tokens(str(product.get("category", "")))
        subcategory_tokens = expanded_catalog_tokens(str(product.get("subcategory", "")))
        description_tokens = expanded_catalog_tokens(str(product.get("description", "")))
        id_tokens = expanded_catalog_tokens(str(product.get("id", "")))
        score = (
            6 * len(query_tokens & brand_tokens)
            + 5 * len(query_tokens & title_tokens)
            + 3 * len(query_tokens & subcategory_tokens)
            + 2 * len(query_tokens & category_tokens)
            + len(query_tokens & description_tokens)
            + len(query_tokens & id_tokens)
        )
        brand = str(product.get("brand", "")).lower()
        title = str(product.get("title", "")).lower()
        if brand and brand in question.lower():
            score += 3
        if title and title in question.lower():
            score += 4
        if score > 0:
            ranked.append((score, product))

    return [product for _, product in sorted(ranked, key=lambda item: (-item[0], str(item[1].get("title", ""))))[:limit]]


def catalog_exclusion_tokens(question: str) -> set[str]:
    question_lower = question.lower()
    exclusions: set[str] = set()
    if "not the bands" in question_lower or "not bands" in question_lower or "not band" in question_lower:
        exclusions.update({"band", "bands", "strap", "straps", "replacement"})
    if "device" in question_lower or "devices" in question_lower:
        exclusions.update({"band", "bands", "strap", "straps", "replacement"})
    return exclusions


def product_contains_excluded_terms(product: dict[str, object], exclusion_tokens: set[str]) -> bool:
    if not exclusion_tokens:
        return False
    searchable = " ".join(
        str(product.get(field, ""))
        for field in ("title", "subcategory", "description")
    )
    return bool(question_tokens(searchable) & exclusion_tokens)


def is_fitness_tracker_device_request(question: str) -> bool:
    tokens = question_tokens(question)
    return bool(tokens & {"fitness", "tracker", "trackers", "watch", "watches"}) and bool(
        tokens & {"device", "devices"}
    )


def product_matches_tracker_device(product: dict[str, object]) -> bool:
    searchable = " ".join(
        str(product.get(field, ""))
        for field in ("title", "brand", "category", "subcategory", "description")
    )
    tokens = question_tokens(searchable)
    accessory_terms = {"accessories", "accessory", "band", "bands", "case", "cover", "replacement", "strap", "straps", "wristband", "wristbands"}
    if tokens & accessory_terms:
        return False
    return bool(tokens & {"tracker", "trackers", "watch", "watches", "fitbit", "garmin", "vivofit"})


def product_matches_accessory_terms(product: dict[str, object], filter_tokens: set[str]) -> bool:
    searchable = " ".join(
        str(product.get(field, ""))
        for field in ("title", "brand", "category", "subcategory", "description")
    )
    tokens = expanded_catalog_tokens(searchable)
    if filter_tokens & {"watch", "watches", "tracker", "trackers", "fitness"} and tokens & {
        "airpod",
        "airpods",
        "ear",
        "earbud",
        "earbuds",
        "headphone",
        "headphones",
        "headset",
    }:
        return False
    band_terms = {
        "band",
        "bands",
        "replacement",
        "strap",
        "straps",
        "wristband",
        "wristbands",
    }
    generic_accessory_terms = {"accessories", "accessory", "case", "cover"}
    requested_band = bool(filter_tokens & band_terms)
    has_accessory_match = bool(tokens & band_terms) if requested_band else bool(
        tokens & (band_terms | generic_accessory_terms)
    )
    has_domain_match = not (
        filter_tokens & {"watch", "watches", "tracker", "trackers", "fitness"}
    ) or bool(
        tokens
        & {"watch", "watches", "tracker", "trackers", "fitbit", "garmin", "vivofit", "alta"}
    )
    return has_accessory_match and has_domain_match


def catalog_ranking_limit(question: str) -> int:
    numbers = [int(match) for match in re.findall(r"\b\d+\b", question)]
    if not numbers:
        return 5
    return min(max(numbers[0], 1), 10)


def catalog_ranking_filter_tokens(question: str) -> set[str]:
    return {
        token
        for token in expanded_catalog_tokens(question)
        if token not in CATALOG_RANKING_STOP_WORDS and not token.isdigit()
    }


def catalog_ranking_filter_label(question: str) -> str:
    return " ".join(
        token
        for token in re.findall(r"[a-z0-9]+", question.lower())
        if token not in CATALOG_RANKING_STOP_WORDS and not token.isdigit()
    )


def catalog_ranking_metric(question: str) -> tuple[str, str, bool]:
    tokens = question_tokens(question)
    question_lower = question.lower()
    if tokens & {"cheapest"} or "lowest price" in question_lower:
        return "price", "cheapest", False
    if tokens & {"expensive", "costliest"} or "highest price" in question_lower:
        return "price", "most expensive", True
    if tokens & {"rated", "rating", "best"} or "highest rated" in question_lower:
        return "rating", "highest rated", True
    return "reviewCount", "most reviewed", True


def product_matches_catalog_filter(product: dict[str, object], filter_tokens: set[str]) -> bool:
    if not filter_tokens:
        return True
    if filter_tokens & {"band", "bands", "strap", "straps", "wristband", "wristbands"}:
        return product_matches_accessory_terms(product, filter_tokens)
    if filter_tokens & {"watch", "watches", "tracker", "trackers", "fitness"}:
        return product_matches_tracker_device(product)
    searchable = " ".join(
        str(product.get(field, ""))
        for field in ("title", "brand", "category", "subcategory", "description")
    )
    product_tokens = expanded_catalog_tokens(searchable)
    return bool(filter_tokens & product_tokens)


def catalog_ranked_products(question: str) -> tuple[list[dict[str, object]], str, str]:
    metric, metric_label, reverse = catalog_ranking_metric(question)
    filter_tokens = catalog_ranking_filter_tokens(question)
    products = [
        product
        for product in load_catalog_products()
        if product_matches_catalog_filter(product, filter_tokens)
    ]
    ranked = sorted(
        products,
        key=lambda product: (
            float(product.get(metric, 0)),
            float(product.get("rating", 0)),
            int(product.get("reviewCount", 0)),
        ),
        reverse=reverse,
    )
    if metric == "price" and not reverse:
        ranked = sorted(
            products,
            key=lambda product: (
                float(product.get("price", 0)),
                -float(product.get("rating", 0)),
                -int(product.get("reviewCount", 0)),
            ),
        )
    filter_label = catalog_ranking_filter_label(question)
    return ranked[:catalog_ranking_limit(question)], metric_label, filter_label


def detect_product_hints(question: str) -> list[str]:
    question_lower = question.lower()
    hints: list[str] = []

    for product_id in PRODUCT_ID_PATTERN.findall(question):
        normalized_id = product_id.upper()
        if normalized_id not in hints:
            hints.append(normalized_id)

    for product in load_product_hints():
        title = product.title.lower()
        brand = product.brand.lower()
        category = product.category.lower()
        subcategory = product.subcategory.lower()
        if product.product_id in hints:
            continue
        if title and title in question_lower:
            hints.append(product.product_id)
            continue
        if brand and len(brand) >= 4 and brand in question_lower:
            hints.append(product.product_id)
            continue
        if category and len(category) >= 4 and category in question_lower:
            hints.append(product.product_id)
            continue
        if subcategory and len(subcategory) >= 4 and subcategory in question_lower:
            hints.append(product.product_id)

    return hints[:5]


def classify_support_intent(question: str, product_hints: list[str] | None = None) -> SupportIntent:
    tokens = question_tokens(question)
    product_hints = product_hints or []

    if not question.strip() or (
        len(tokens) <= 3 and not tokens.intersection(QUESTION_DETAIL_KEYWORDS) and not product_hints
    ):
        return "clarification_needed"

    if tokens.intersection(UNSUPPORTED_CATEGORY_KEYWORDS) and not product_hints:
        return "unsupported_category"

    if is_catalog_ranking_question(question):
        return "catalog_ranking"

    if is_catalog_availability_question(question):
        return "catalog_availability"

    if is_ticket_handoff_question(question):
        return "escalation_candidate"

    if tokens.intersection(COMPARISON_KEYWORDS):
        return "comparison"

    if tokens.intersection(REVIEW_KEYWORDS):
        return "review_summary"

    if tokens.intersection(TROUBLESHOOTING_KEYWORDS):
        return "troubleshooting"

    if tokens.intersection(COMPATIBILITY_KEYWORDS):
        return "compatibility"

    if tokens.intersection(POLICY_KEYWORDS):
        return "store_policy"

    if product_hints:
        return "product_question"

    return "clarification_needed"


def classify_intent(state: SupportAgentState) -> SupportAgentState:
    question = state.get("question", "")
    product_hints = detect_product_hints(question)
    intent = classify_support_intent(question, product_hints=product_hints)
    return {
        **state,
        "intent": intent,
        "product_hints": product_hints,
        "needs_clarification": intent == "clarification_needed",
        "escalation": (
            {
                "reason": "Question appears to need account, order, or personal support.",
                "detected_intent": intent,
                "product_hint": product_hints[0] if product_hints else "",
                "summary": question,
            }
            if intent == "escalation_candidate"
            else state.get("escalation")
        ),
    }


def retrieval_query_for_intent(
    question: str,
    intent: SupportIntent,
    product_hints: list[str] | None = None,
) -> str:
    product_hints = product_hints or []
    hint_text = " ".join(product_hints)

    if intent == "store_policy":
        tokens = question_tokens(question)
        policy_terms = ["store", "policy"]
        if tokens & {"return", "returns", "refund", "refunds"}:
            policy_terms.extend(["returns", "refunds"])
        if tokens & {"shipping", "ship", "delivery"}:
            policy_terms.extend(["shipping", "delivery"])
        if "warranty" in tokens:
            policy_terms.append("warranty")
        if tokens & {"payment", "payments"}:
            policy_terms.append("payments")
        if len(policy_terms) == 2:
            policy_terms.extend(["returns", "refunds", "shipping", "warranty", "payments"])
        return f"{question} {' '.join(policy_terms)}"
    if intent == "troubleshooting":
        return f"{question} troubleshooting setup power charging pairing not working {hint_text}".strip()
    if intent == "compatibility":
        return f"{question} compatibility fit model device version {hint_text}".strip()
    if intent == "comparison":
        return f"{question} compare product features rating reviews compatibility {hint_text}".strip()
    if intent == "review_summary":
        return f"{question} customer reviews ratings feedback {hint_text}".strip()
    if intent == "product_question":
        return f"{question} product faq setup compatibility troubleshooting {hint_text}".strip()
    return question


def retrieval_settings_for_intent(intent: SupportIntent) -> tuple[int, int]:
    if intent in {"catalog_availability", "catalog_ranking", "clarification_needed", "escalation_candidate", "unsupported_category"}:
        return 0, 0
    if intent in {"comparison", "review_summary"}:
        return 6, 80
    return 4, 50


def plan_retrieval(state: SupportAgentState) -> SupportAgentState:
    question = state.get("question", "")
    intent = state.get("intent", "clarification_needed")
    product_hints = state.get("product_hints", [])
    k, candidate_count = retrieval_settings_for_intent(intent)
    retrieval_query = retrieval_query_for_intent(
        question=question,
        intent=intent,
        product_hints=product_hints,
    )
    return {
        **state,
        "retrieval_query": retrieval_query,
        "retrieval_k": k,
        "retrieval_candidate_count": candidate_count,
    }


def retrieve_context(state: SupportAgentState) -> SupportAgentState:
    planned_state = plan_retrieval(state)
    k = planned_state.get("retrieval_k", 0)
    candidate_count = planned_state.get("retrieval_candidate_count", 0)
    if k <= 0 or candidate_count <= 0:
        return {
            **planned_state,
            "retrieved_results": [],
        }

    results = retrieve_relevant_chunks(
        query=planned_state.get("retrieval_query", planned_state.get("question", "")),
        provider=planned_state.get("provider", DEFAULT_RETRIEVAL_PROVIDER),
        k=k,
        candidate_count=candidate_count,
    )
    return {
        **planned_state,
        "retrieved_results": results,
    }


def expected_doc_types_for_intent(intent: SupportIntent) -> set[str]:
    if intent in {"catalog_availability", "catalog_ranking"}:
        return {"catalog_product"}
    if intent == "store_policy":
        return {"store_policy"}
    if intent == "troubleshooting":
        return {"troubleshooting", "product_faq", "support_ticket"}
    if intent == "compatibility":
        return {"compatibility", "product_faq", "support_ticket"}
    if intent == "comparison":
        return {"catalog_product", "product_faq", "compatibility", "customer_review"}
    if intent == "review_summary":
        return {"customer_review", "review_summary", "catalog_product"}
    if intent == "product_question":
        return {"catalog_product", "product_faq", "setup", "compatibility", "troubleshooting"}
    return set()


def result_doc_types(results: list[RetrievalResult]) -> set[str]:
    return {
        str(result.document.metadata.get("doc_type", "unknown"))
        for result in results
    }


def has_intent_matching_context(
    intent: SupportIntent,
    results: list[RetrievalResult],
) -> bool:
    expected_doc_types = expected_doc_types_for_intent(intent)
    if not expected_doc_types:
        return False
    return bool(expected_doc_types & result_doc_types(results))


def has_sufficient_context(
    intent: SupportIntent,
    results: list[RetrievalResult],
) -> bool:
    if intent in {"clarification_needed", "escalation_candidate", "unsupported_category"}:
        return False
    if not results:
        return False

    top_lexical_score = max(result.lexical_score for result in results)
    has_matching_doc_type = has_intent_matching_context(intent, results)

    return top_lexical_score >= 2 and has_matching_doc_type


def assess_context(state: SupportAgentState) -> SupportAgentState:
    intent = state.get("intent", "clarification_needed")
    results = state.get("retrieved_results", [])
    enough_context = has_sufficient_context(intent, results)
    needs_clarification = state.get("needs_clarification", False) or (
        not enough_context and intent != "escalation_candidate"
    )

    return {
        **state,
        "has_enough_context": enough_context,
        "needs_clarification": needs_clarification,
    }


def generate_answer(state: SupportAgentState) -> SupportAgentState:
    cited_answer = build_cited_answer_from_results(
        question=state.get("question", ""),
        results=state.get("retrieved_results", []),
    )
    return {
        **state,
        "answer": cited_answer.answer,
        "citations": cited_answer.citations,
        "retrieved_results": cited_answer.retrieved_results,
    }


def catalog_result_from_product(product: dict[str, object], rank: int, question: str) -> RetrievalResult:
    product_id = str(product.get("id", "unknown"))
    title = str(product.get("title", "Untitled product"))
    brand = str(product.get("brand", "Unknown brand"))
    category = str(product.get("category", "Unknown category"))
    subcategory = str(product.get("subcategory", "Unknown subcategory"))
    price = product.get("price", "")
    rating = product.get("rating", "")
    review_count = product.get("reviewCount", "")
    description = str(product.get("description", ""))
    content = (
        f"{title}\n"
        f"Brand: {brand}\n"
        f"Category: {category} > {subcategory}\n"
        f"Price: ${float(price):.2f}\n"
        f"Rating: {rating}/5 from {review_count} reviews.\n"
        f"{description}"
    )
    document = Document(
        page_content=content,
        metadata={
            "doc_type": "catalog_product",
            "source_path": "data/catalog/products.json",
            "chunk_id": f"catalog_product:{product_id}",
            "product_id": product_id,
            "title": title,
        },
    )
    return RetrievalResult(
        document=document,
        vector_score=float("inf"),
        lexical_score=max(1, len(availability_query_tokens(question) & expanded_catalog_tokens(content))),
    )


def generate_catalog_availability_answer(state: SupportAgentState) -> SupportAgentState:
    question = state.get("question", "")
    matches = catalog_product_search(question)
    query_label = availability_display_terms(question)

    if matches:
        result_rows = []
        for index, product in enumerate(matches[:3], start=1):
            result_rows.append(
                (
                    f"- {product.get('title')} ({product.get('id')}) by {product.get('brand')} - "
                    f"${float(product.get('price', 0)):.2f}, "
                    f"{product.get('rating')}/5 from {product.get('reviewCount')} reviews [{index}]"
                )
            )
        if any(str(product.get("brand", "")).lower() in question.lower() for product in matches):
            intro = "Yes, I found matching catalog products:"
        else:
            intro = (
                f"I do not see an exact catalog match for \"{query_label}\", "
                "but I found related products:"
            )
        answer = "\n".join([intro, *result_rows])
    else:
        answer = (
            f"I do not see \"{query_label}\" in the current electronics catalog. "
            "Try another brand, product type, or product ID and I can check again."
        )

    retrieved_results = [
        catalog_result_from_product(product, rank, question)
        for rank, product in enumerate(matches, start=1)
    ]
    citations = [
        Citation(
            id=str(index),
            label=f"{index}. {product.get('title')} (catalog product)",
            source_path="data/catalog/products.json",
            doc_type="catalog_product",
            product_id=str(product.get("id", "")),
            chunk_id=f"catalog_product:{product.get('id', 'unknown')}",
        )
        for index, product in enumerate(matches[:3], start=1)
    ]
    return {
        **state,
        "answer": answer,
        "catalog_matches": matches,
        "citations": citations,
        "retrieved_results": retrieved_results,
        "has_enough_context": bool(matches),
        "needs_clarification": False,
    }


def generate_catalog_ranking_answer(state: SupportAgentState) -> SupportAgentState:
    question = state.get("question", "")
    matches, metric_label, filter_label = catalog_ranked_products(question)

    if matches:
        scope = f" matching {filter_label}" if filter_label else ""
        result_rows = []
        for index, product in enumerate(matches, start=1):
            result_rows.append(
                (
                    f"{index}. {product.get('title')} ({product.get('id')}) by {product.get('brand')} - "
                    f"${float(product.get('price', 0)):.2f}, "
                    f"{product.get('rating')}/5 from {product.get('reviewCount')} reviews [{index}]"
                )
            )
        answer = "\n".join(
            [
                f"Here are the {metric_label} catalog products{scope}:",
                *result_rows,
            ]
        )
    else:
        answer = (
            "I could not find matching catalog products for that ranking request. "
            "Try a broader product type, brand, or category."
        )

    retrieved_results = [
        catalog_result_from_product(product, rank, question)
        for rank, product in enumerate(matches, start=1)
    ]
    citations = [
        Citation(
            id=str(index),
            label=f"{index}. {product.get('title')} (catalog product)",
            source_path="data/catalog/products.json",
            doc_type="catalog_product",
            product_id=str(product.get("id", "")),
            chunk_id=f"catalog_product:{product.get('id', 'unknown')}",
        )
        for index, product in enumerate(matches, start=1)
    ]
    return {
        **state,
        "answer": answer,
        "catalog_matches": matches,
        "citations": citations,
        "retrieved_results": retrieved_results,
        "has_enough_context": bool(matches),
        "needs_clarification": False,
    }


def clarification_prompt_for_intent(intent: SupportIntent) -> str:
    if intent == "store_policy":
        return (
            "Which policy area do you want help with: returns, refunds, shipping, "
            "warranty, or payments?"
        )
    if intent == "product_question":
        return (
            "Which product do you want help with? Please share the product name, "
            "product ID, or category."
        )
    if intent == "troubleshooting":
        return (
            "Which product are you troubleshooting, and what is happening? For example, "
            "tell me whether it will not power on, will not charge, will not pair, or has a setup issue."
        )
    if intent == "compatibility":
        return (
            "Which product and device model should I check for compatibility?"
        )
    if intent == "comparison":
        return (
            "Which two or more products would you like me to compare?"
        )
    if intent == "review_summary":
        return (
            "Which product should I summarize customer reviews for? Please share the product name or ID."
        )
    if intent == "unsupported_category":
        return (
            "This demo store's support knowledge base is focused on electronics products. "
            "Please ask about an electronics product, product ID, or electronics policy area such as returns, shipping, warranty, or payments."
        )
    return (
        "I can help with product setup, troubleshooting, compatibility, reviews, "
        "shipping, returns, refunds, warranty, or payments. What would you like help with?"
    )


def generate_clarification(state: SupportAgentState) -> SupportAgentState:
    intent = state.get("intent", "clarification_needed")
    return {
        **state,
        "answer": clarification_prompt_for_intent(intent),
        "citations": [],
        "needs_clarification": True,
        "has_enough_context": False,
    }


def escalation_reason_for_state(state: SupportAgentState) -> str:
    intent = state.get("intent", "escalation_candidate")
    question = state.get("question", "")
    tokens = question_tokens(question)

    if tokens & URGENT_SUPPORT_KEYWORDS:
        return "Question uses urgent or safety-related issue language."
    if tokens & PAYMENT_HANDOFF_KEYWORDS and tokens & {"charged", "double", "transaction", "card"}:
        return "Question appears to require payment or transaction-specific support."
    if tokens & SHIPPING_HANDOFF_KEYWORDS and tokens & {"damaged", "delivered", "missing", "tracking", "package", "shipment"}:
        return "Question appears to require shipment, delivery, or tracking-specific support."
    if tokens & DEFECT_KEYWORDS:
        return "Question reports possible product damage, defect, or unsafe behavior."
    if tokens & MISSING_PART_KEYWORDS:
        return "Question reports a missing part, component, or accessory."
    if tokens & {"order", "tracking", "address", "invoice", "account"}:
        return "Question appears to need account, order, tracking, or personal support data."
    if tokens & {"cancel"}:
        return "Question appears to require an order-specific cancellation workflow."
    if is_contact_request(question):
        return "Question asks for customer support contact or handoff details."
    if tokens & TROUBLESHOOTING_KEYWORDS and tokens & REPEATED_UNRESOLVED_KEYWORDS:
        return "Question suggests repeated unresolved troubleshooting attempts."
    if intent == "escalation_candidate":
        return "Question appears to need support beyond the local product and policy knowledge base."
    return "Retrieved context was not strong enough for a grounded self-service answer."


def escalation_answer_for_reason(reason: str) -> str:
    if "account, order, tracking" in reason or "cancellation" in reason:
        return (
            "I do not have access to personal order, account, invoice, address, or tracking details. "
            "I can explain the general shipping, returns, refunds, warranty, or payment policies, "
            "or I can help prepare this as a support ticket for order-specific help."
        )
    if "contact or handoff" in reason:
        return (
            "I do not have a published support phone number in this local demo knowledge base. "
            "I can help with product setup, troubleshooting, compatibility, reviews, shipping, returns, refunds, warranty, or payments, "
            "or I can help prepare this as a support ticket for a specialist."
        )
    if "safety-related" in reason or "unsafe behavior" in reason:
        return (
            "This sounds like it may need urgent safety-focused support. Stop using the product if it seems unsafe, "
            "and I can help prepare this as a support ticket for specialist review."
        )
    if "payment or transaction-specific" in reason:
        return (
            "I do not have access to personal payment or transaction records. "
            "I can explain the general payment policy, or I can help prepare this as a support ticket for billing review."
        )
    if "shipment, delivery, or tracking-specific" in reason:
        return (
            "I do not have access to shipment, delivery, or tracking records. "
            "I can explain the general shipping policy, or I can help prepare this as a support ticket for delivery help."
        )
    if "missing part" in reason:
        return (
            "This sounds like a missing part or accessory issue that may need specialist review. "
            "I can help prepare this as a support ticket."
        )
    if "repeated unresolved troubleshooting" in reason:
        return (
            "Since this sounds unresolved after troubleshooting, I can help prepare this as a support ticket "
            "so a specialist can review the issue."
        )
    return (
        "I do not have enough grounded support context to answer that confidently. "
        "I can help prepare this as a support ticket so a support specialist can review it."
    )


def ticket_issue_type_for_question(question: str, reason: str) -> str:
    tokens = question_tokens(question)
    reason_lower = reason.lower()
    if is_contact_request(question):
        return "contact_request"
    if tokens & URGENT_SUPPORT_KEYWORDS or tokens & DEFECT_KEYWORDS or "unsafe" in reason_lower:
        if tokens & SHIPPING_HANDOFF_KEYWORDS and tokens & {"damaged", "package", "shipment"}:
            return "shipping"
        return "product_defect"
    if tokens & {"refund", "refunds"}:
        return "refund"
    if tokens & {"return", "returns"}:
        return "return"
    if tokens & {"warranty"}:
        return "warranty"
    if tokens & PAYMENT_HANDOFF_KEYWORDS:
        return "payment"
    if tokens & SHIPPING_HANDOFF_KEYWORDS:
        return "shipping"
    if tokens & MISSING_PART_KEYWORDS or "missing part" in reason_lower:
        return "missing_parts"
    if tokens & {"order", "cancel", "invoice", "address", "account"}:
        return "order"
    if tokens & {"missing", "part", "parts", "accessory"}:
        return "missing_parts"
    if tokens & {"compatible", "compatibility", "fit", "fits", "model"}:
        return "compatibility"
    if tokens & {"setup", "install", "pair", "pairing"}:
        return "setup"
    if tokens & TROUBLESHOOTING_KEYWORDS:
        return "troubleshooting"
    return "other"


def ticket_priority_for_question(question: str, issue_type: str) -> str:
    tokens = question_tokens(question)
    question_lower = question.lower()
    if tokens & URGENT_SUPPORT_KEYWORDS:
        return "urgent"
    if tokens & DEFECT_KEYWORDS:
        return "high"
    if issue_type in {"product_defect", "payment"}:
        return "high"
    if "marked delivered" in question_lower or "cannot be found" in question_lower:
        return "high"
    if tokens & {"damaged", "missing"} and tokens & {"shipment", "delivery", "package", "item"}:
        return "high"
    if tokens & TROUBLESHOOTING_KEYWORDS and tokens & REPEATED_UNRESOLVED_KEYWORDS:
        return "high"
    return "normal"


def product_context_from_hints(product_hints: list[str]) -> TicketProductPayload:
    for hint in product_hints:
        hint_lower = hint.lower()
        for product in load_product_hints():
            product_id = product.product_id
            title = product.title
            if (
                hint_lower == product_id.lower()
                or product_id.lower() in hint_lower
                or hint_lower in title.lower()
                or title.lower() in hint_lower
            ):
                return {
                    "productId": product.product_id,
                    "productTitle": product.title,
                    "category": product.category,
                    "subcategory": product.subcategory,
                }
    return {
        "productId": None,
        "productTitle": None,
        "category": None,
        "subcategory": None,
    }


def support_ticket_payload_for_state(
    state: SupportAgentState,
    reason: str,
) -> TicketCreatePayload:
    question = state.get("question", "").strip()
    issue_type = ticket_issue_type_for_question(question, reason)
    return {
        "issueType": issue_type,
        "summary": question[:500] if question else "Support handoff requested.",
        "priority": ticket_priority_for_question(question, issue_type),
        "source": "chat",
        "product": product_context_from_hints(state.get("product_hints", [])),
        "handoff": {
            "question": question,
            "conversationExcerpt": question[:500] if question else None,
            "escalationReason": reason,
            "agentIntent": state.get("intent", "escalation_candidate"),
            "retrievalSufficient": state.get("has_enough_context", False),
        },
        "contactPreference": "unknown",
    }


def handoff_metadata_for_state(
    state: SupportAgentState,
    reason: str,
) -> HandoffMetadata:
    return {
        "canCreateTicket": True,
        "reason": reason,
        "ticketPayload": support_ticket_payload_for_state(state, reason),
    }


def prepare_escalation(state: SupportAgentState) -> SupportAgentState:
    reason = escalation_reason_for_state(state)
    product_hints = state.get("product_hints", [])
    escalation: EscalationMetadata = {
        "reason": reason,
        "detected_intent": state.get("intent", "escalation_candidate"),
        "product_hint": product_hints[0] if product_hints else "",
        "summary": state.get("question", ""),
    }
    return {
        **state,
        "answer": escalation_answer_for_reason(reason),
        "citations": [],
        "has_enough_context": False,
        "needs_clarification": False,
        "escalation": escalation,
        "handoff": handoff_metadata_for_state(state, reason),
    }


def route_after_classification(state: SupportAgentState) -> Literal["retrieve", "clarify", "escalate", "answer_catalog", "rank_catalog"]:
    intent = state.get("intent", "clarification_needed")
    if intent == "catalog_ranking":
        return "rank_catalog"
    if intent == "catalog_availability":
        return "answer_catalog"
    if intent == "escalation_candidate":
        return "escalate"
    if intent in {"clarification_needed", "unsupported_category"}:
        return "clarify"
    return "retrieve"


def route_after_assessment(state: SupportAgentState) -> Literal["answer", "clarify", "escalate"]:
    if state.get("intent") == "escalation_candidate":
        return "escalate"
    if state.get("has_enough_context"):
        return "answer"
    return "clarify"


@lru_cache
def build_support_agent_graph():
    graph = StateGraph(SupportAgentState)
    graph.add_node("classify", classify_intent)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("assess", assess_context)
    graph.add_node("answer", generate_answer)
    graph.add_node("answer_catalog", generate_catalog_availability_answer)
    graph.add_node("rank_catalog", generate_catalog_ranking_answer)
    graph.add_node("clarify", generate_clarification)
    graph.add_node("escalate", prepare_escalation)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classification,
        {
            "retrieve": "retrieve",
            "clarify": "clarify",
            "escalate": "escalate",
            "answer_catalog": "answer_catalog",
            "rank_catalog": "rank_catalog",
        },
    )
    graph.add_edge("retrieve", "assess")
    graph.add_conditional_edges(
        "assess",
        route_after_assessment,
        {
            "answer": "answer",
            "clarify": "clarify",
            "escalate": "escalate",
        },
    )
    graph.add_edge("answer", END)
    graph.add_edge("answer_catalog", END)
    graph.add_edge("rank_catalog", END)
    graph.add_edge("clarify", END)
    graph.add_edge("escalate", END)

    return graph.compile()


def support_agent_result_from_state(
    state: SupportAgentState,
    include_debug: bool = False,
) -> SupportAgentResult:
    return SupportAgentResult(
        question=state.get("question", ""),
        answer=state.get("answer", ""),
        provider=state.get("provider", DEFAULT_RETRIEVAL_PROVIDER),
        intent=state.get("intent", "clarification_needed"),
        citations=state.get("citations", []),
        retrieved_results=state.get("retrieved_results", []),
        has_enough_context=state.get("has_enough_context", False),
        needs_clarification=state.get("needs_clarification", False),
        escalation=state.get("escalation"),
        handoff=state.get("handoff"),
        debug=debug_metadata_from_state(state) if include_debug else None,
    )


def run_support_agent(
    question: str,
    provider: ProviderName = DEFAULT_RETRIEVAL_PROVIDER,
    include_debug: bool = False,
) -> SupportAgentResult:
    initial_state = initial_support_state(question=question, provider=provider)
    final_state = build_support_agent_graph().invoke(initial_state)
    return support_agent_result_from_state(final_state, include_debug=include_debug)
