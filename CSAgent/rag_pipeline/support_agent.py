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
    "clarification_needed",
    "escalation_candidate",
    "unsupported_category",
]


class EscalationMetadata(TypedDict, total=False):
    reason: str
    detected_intent: SupportIntent
    product_hint: str
    summary: str


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
    "have",
    "in",
    "sell",
    "stock",
    "store",
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
    | TROUBLESHOOTING_KEYWORDS
    | COMPATIBILITY_KEYWORDS
    | COMPARISON_KEYWORDS
    | REVIEW_KEYWORDS
    | ACCOUNT_OR_ORDER_KEYWORDS
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
    "do",
    "does",
    "have",
    "in",
    "is",
    "me",
    "sell",
    "show",
    "stock",
    "store",
    "the",
    "there",
    "you",
}
CATALOG_SYNONYMS = {
    "laptop": {"laptop", "notebook", "computer", "computers"},
    "laptops": {"laptop", "notebook", "computer", "computers"},
    "notebook": {"laptop", "notebook", "computer", "computers"},
    "notebooks": {"laptop", "notebook", "computer", "computers"},
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
    terms = [
        token
        for token in question_tokens(question)
        if token not in CATALOG_QUERY_STOP_WORDS
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
        )
    )
    return phrase_match or bool(tokens & {"available", "availability", "stock"})


def catalog_product_search(question: str, limit: int = 5) -> list[dict[str, object]]:
    query_tokens = availability_query_tokens(question)
    if not query_tokens:
        return []

    ranked: list[tuple[int, dict[str, object]]] = []
    for product in load_catalog_products():
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

    if is_catalog_availability_question(question):
        return "catalog_availability"

    if tokens.intersection(ACCOUNT_OR_ORDER_KEYWORDS | URGENT_SUPPORT_KEYWORDS):
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
    if intent in {"catalog_availability", "clarification_needed", "escalation_candidate", "unsupported_category"}:
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
    if intent == "catalog_availability":
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

    if tokens & {"order", "tracking", "address", "invoice", "account"}:
        return "Question appears to need account, order, tracking, or personal support data."
    if tokens & {"cancel"}:
        return "Question appears to require an order-specific cancellation workflow."
    if tokens & URGENT_SUPPORT_KEYWORDS:
        return "Question uses urgent or safety-related issue language."
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
    if "safety-related" in reason:
        return (
            "This sounds like it may need urgent safety-focused support. Stop using the product if it seems unsafe, "
            "and I can help prepare this as a support ticket for specialist review."
        )
    return (
        "I do not have enough grounded support context to answer that confidently. "
        "I can help prepare this as a support ticket so a support specialist can review it."
    )


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
    }


def route_after_classification(state: SupportAgentState) -> Literal["retrieve", "clarify", "escalate", "answer_catalog"]:
    intent = state.get("intent", "clarification_needed")
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
