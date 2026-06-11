from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
RAG_PIPELINE_DIR = REPO_ROOT / "rag_pipeline"

if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))
if str(RAG_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(RAG_PIPELINE_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from support_agent import SupportIntent, run_support_agent  # noqa: E402


@dataclass(frozen=True)
class ValidationCase:
    name: str
    question: str
    expected_intent: SupportIntent
    min_citations: int = 0
    min_retrieved_context: int = 0
    expected_top_doc_type: str | None = None
    should_clarify: bool = False
    should_escalate: bool = False
    should_offer_handoff: bool = False
    expected_ticket_issue_type: str | None = None
    expected_ticket_priority: str | None = None
    answer_contains: str | None = None


VALIDATION_CASES = [
    ValidationCase(
        name="return policy",
        question="What is the return policy for opened electronics?",
        expected_intent="store_policy",
        min_citations=1,
        min_retrieved_context=1,
        expected_top_doc_type="store_policy",
        answer_contains="30 days",
    ),
    ValidationCase(
        name="product setup",
        question="How do I set up the JBL CLIP 3 speaker?",
        expected_intent="product_question",
        min_citations=1,
        min_retrieved_context=1,
    ),
    ValidationCase(
        name="troubleshooting",
        question="How do I troubleshoot a device that will not power on?",
        expected_intent="troubleshooting",
        min_citations=1,
        min_retrieved_context=1,
    ),
    ValidationCase(
        name="comparison",
        question="Compare these Bluetooth speakers",
        expected_intent="comparison",
        min_citations=1,
        min_retrieved_context=1,
    ),
    ValidationCase(
        name="catalog availability",
        question="Is IBM Laptop available?",
        expected_intent="catalog_availability",
        min_citations=1,
        min_retrieved_context=1,
        expected_top_doc_type="catalog_product",
        answer_contains="I do not see an exact catalog match",
    ),
    ValidationCase(
        name="catalog device availability refinement",
        question="Yes, I am looking for a fitness tracker devices, not the bands",
        expected_intent="catalog_availability",
        answer_contains="current electronics catalog",
    ),
    ValidationCase(
        name="catalog most reviewed ranking",
        question="List top 5 products with highest reviews",
        expected_intent="catalog_ranking",
        min_citations=5,
        min_retrieved_context=5,
        expected_top_doc_type="catalog_product",
        answer_contains="most reviewed catalog products",
    ),
    ValidationCase(
        name="catalog cheapest ranking",
        question="Top 5 cheapest products",
        expected_intent="catalog_ranking",
        min_citations=5,
        min_retrieved_context=5,
        expected_top_doc_type="catalog_product",
        answer_contains="cheapest catalog products",
    ),
    ValidationCase(
        name="catalog watch ranking no device match",
        question="show me top rated watches",
        expected_intent="catalog_ranking",
        answer_contains="could not find matching catalog products",
    ),
    ValidationCase(
        name="catalog watch bands ranking",
        question="show me top rated watch bands",
        expected_intent="catalog_ranking",
        min_citations=1,
        min_retrieved_context=1,
        expected_top_doc_type="catalog_product",
        answer_contains="highest rated catalog products",
    ),
    ValidationCase(
        name="underspecified clarification",
        question="Help",
        expected_intent="clarification_needed",
        should_clarify=True,
        answer_contains="What would you like help with?",
    ),
    ValidationCase(
        name="order escalation",
        question="Where is my order?",
        expected_intent="escalation_candidate",
        should_escalate=True,
        should_offer_handoff=True,
        expected_ticket_issue_type="order",
        expected_ticket_priority="normal",
        answer_contains="I do not have access to personal order",
    ),
    ValidationCase(
        name="support contact escalation",
        question="Can I have the support contact number.",
        expected_intent="escalation_candidate",
        should_escalate=True,
        should_offer_handoff=True,
        expected_ticket_issue_type="contact_request",
        expected_ticket_priority="normal",
        answer_contains="I do not have a published support phone number",
    ),
    ValidationCase(
        name="payment escalation",
        question="My card was charged twice for this order.",
        expected_intent="escalation_candidate",
        should_escalate=True,
        should_offer_handoff=True,
        expected_ticket_issue_type="payment",
        expected_ticket_priority="high",
        answer_contains="payment or transaction records",
    ),
    ValidationCase(
        name="damaged shipment escalation",
        question="My shipment arrived damaged and the package is crushed.",
        expected_intent="escalation_candidate",
        should_escalate=True,
        should_offer_handoff=True,
        expected_ticket_issue_type="shipping",
        expected_ticket_priority="high",
        answer_contains="shipment, delivery, or tracking records",
    ),
    ValidationCase(
        name="product defect escalation",
        question="The product is damaged and unsafe to use.",
        expected_intent="escalation_candidate",
        should_escalate=True,
        should_offer_handoff=True,
        expected_ticket_issue_type="product_defect",
        expected_ticket_priority="urgent",
        answer_contains="urgent safety-focused support",
    ),
    ValidationCase(
        name="missing parts escalation",
        question="The box is missing a cable accessory.",
        expected_intent="escalation_candidate",
        should_escalate=True,
        should_offer_handoff=True,
        expected_ticket_issue_type="missing_parts",
        expected_ticket_priority="normal",
        answer_contains="missing part or accessory issue",
    ),
    ValidationCase(
        name="repeated troubleshooting escalation",
        question="I already tried troubleshooting but the device still will not power on.",
        expected_intent="escalation_candidate",
        should_escalate=True,
        should_offer_handoff=True,
        expected_ticket_issue_type="troubleshooting",
        expected_ticket_priority="high",
        answer_contains="unresolved after troubleshooting",
    ),
    ValidationCase(
        name="unsupported category",
        question="What is the return policy for opened clothes?",
        expected_intent="unsupported_category",
        should_clarify=True,
        answer_contains="focused on electronics products",
    ),
]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_case(client: TestClient, validation_case: ValidationCase) -> None:
    agent_result = run_support_agent(validation_case.question, provider="nebius")
    api_response = client.post(
        "/chat",
        json={
            "question": validation_case.question,
            "provider": "nebius",
        },
    )

    assert_condition(
        api_response.status_code == 200,
        f"{validation_case.name}: expected 200, got {api_response.status_code}",
    )
    api_data = api_response.json()

    assert_condition(
        agent_result.intent == validation_case.expected_intent,
        (
            f"{validation_case.name}: expected intent {validation_case.expected_intent}, "
            f"got {agent_result.intent}"
        ),
    )
    assert_condition(
        len(api_data["citations"]) >= validation_case.min_citations,
        (
            f"{validation_case.name}: expected at least {validation_case.min_citations} citations, "
            f"got {len(api_data['citations'])}"
        ),
    )
    assert_condition(
        len(api_data["retrievedContext"]) >= validation_case.min_retrieved_context,
        (
            f"{validation_case.name}: expected at least {validation_case.min_retrieved_context} "
            f"retrieved contexts, got {len(api_data['retrievedContext'])}"
        ),
    )

    if validation_case.expected_top_doc_type is not None:
        assert_condition(
            api_data["retrievedContext"],
            f"{validation_case.name}: expected retrieved context",
        )
        assert_condition(
            api_data["retrievedContext"][0]["docType"] == validation_case.expected_top_doc_type,
            (
                f"{validation_case.name}: expected top doc type "
                f"{validation_case.expected_top_doc_type}, got "
                f"{api_data['retrievedContext'][0]['docType']}"
            ),
        )

    assert_condition(
        agent_result.needs_clarification == validation_case.should_clarify,
        (
            f"{validation_case.name}: expected needs_clarification="
            f"{validation_case.should_clarify}, got {agent_result.needs_clarification}"
        ),
    )
    assert_condition(
        bool(agent_result.escalation) == validation_case.should_escalate,
        (
            f"{validation_case.name}: expected escalation={validation_case.should_escalate}, "
            f"got {bool(agent_result.escalation)}"
        ),
    )
    assert_condition(
        bool(agent_result.handoff) == validation_case.should_offer_handoff,
        (
            f"{validation_case.name}: expected handoff={validation_case.should_offer_handoff}, "
            f"got {bool(agent_result.handoff)}"
        ),
    )
    assert_condition(
        bool(api_data.get("handoff")) == validation_case.should_offer_handoff,
        (
            f"{validation_case.name}: expected API handoff={validation_case.should_offer_handoff}, "
            f"got {bool(api_data.get('handoff'))}"
        ),
    )
    if validation_case.expected_ticket_issue_type is not None:
        ticket_payload = (api_data.get("handoff") or {}).get("ticketPayload") or {}
        assert_condition(
            ticket_payload.get("issueType") == validation_case.expected_ticket_issue_type,
            (
                f"{validation_case.name}: expected ticket issue type "
                f"{validation_case.expected_ticket_issue_type}, got "
                f"{ticket_payload.get('issueType')}"
            ),
        )
    if validation_case.expected_ticket_priority is not None:
        ticket_payload = (api_data.get("handoff") or {}).get("ticketPayload") or {}
        assert_condition(
            ticket_payload.get("priority") == validation_case.expected_ticket_priority,
            (
                f"{validation_case.name}: expected ticket priority "
                f"{validation_case.expected_ticket_priority}, got "
                f"{ticket_payload.get('priority')}"
            ),
        )

    if validation_case.answer_contains is not None:
        assert_condition(
            validation_case.answer_contains in api_data["answer"],
            (
                f"{validation_case.name}: expected answer to contain "
                f"{validation_case.answer_contains!r}"
            ),
        )

    print(
        f"ok: {validation_case.name} | intent={agent_result.intent} | "
        f"citations={len(api_data['citations'])} | "
        f"contexts={len(api_data['retrievedContext'])}"
    )


def main() -> None:
    client = TestClient(app)
    for validation_case in VALIDATION_CASES:
        validate_case(client, validation_case)
    print(f"\nValidated {len(VALIDATION_CASES)} support-agent cases.")


if __name__ == "__main__":
    main()
