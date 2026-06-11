from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app, get_ticket_repository  # noqa: E402
from app.ticket_repository import TicketRepository  # noqa: E402


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_ticket_api(client: TestClient) -> None:
    list_response = client.get("/tickets")
    assert_condition(list_response.status_code == 200, list_response.text)
    assert_condition(len(list_response.json()) == 25, "expected 25 seed tickets")

    create_payload = {
        "issueType": "shipping",
        "summary": "Customer needs delivery help.",
        "priority": "high",
        "source": "api",
        "product": {"productId": "B0BYBG1PPD"},
        "handoff": {
            "question": "Where is my shipment?",
            "escalationReason": "Shipment-specific request.",
        },
        "idempotencyKey": "api-test-delivery-help",
    }
    create_response = client.post("/tickets", json=create_payload)
    assert_condition(create_response.status_code == 201, create_response.text)
    created_ticket = create_response.json()
    assert_condition(created_ticket["id"] == "TICKET-0026", "expected TICKET-0026")

    duplicate_response = client.post("/tickets", json=create_payload)
    assert_condition(duplicate_response.status_code == 201, duplicate_response.text)
    assert_condition(
        duplicate_response.json()["id"] == created_ticket["id"],
        "idempotent POST /tickets should return existing ticket",
    )

    tickets_after_duplicate = client.get("/tickets").json()
    runtime_matches = [
        ticket
        for ticket in tickets_after_duplicate
        if ticket.get("idempotencyKey") == "api-test-delivery-help"
    ]
    assert_condition(len(runtime_matches) == 1, "duplicate API create produced extra ticket")

    detail_response = client.get(f"/tickets/{created_ticket['id']}")
    assert_condition(detail_response.status_code == 200, detail_response.text)

    filter_response = client.get(
        "/tickets",
        params={"status": "open", "priority": "high", "productId": "B0BYBG1PPD"},
    )
    assert_condition(filter_response.status_code == 200, filter_response.text)
    assert_condition(
        [ticket["id"] for ticket in filter_response.json()] == [created_ticket["id"]],
        "ticket filters did not isolate created ticket",
    )

    patch_response = client.patch(
        f"/tickets/{created_ticket['id']}",
        json={"status": "in_progress", "internalNote": "Reviewing delivery details."},
    )
    assert_condition(patch_response.status_code == 200, patch_response.text)
    patched_ticket = patch_response.json()
    assert_condition(patched_ticket["status"] == "in_progress", "ticket status was not updated")
    assert_condition(
        patched_ticket["internalNotes"] == ["Reviewing delivery details."],
        "internal note was not appended",
    )

    missing_response = client.get("/tickets/TICKET-9999")
    assert_condition(missing_response.status_code == 404, "missing ticket should return 404")

    seed_patch_response = client.patch("/tickets/TICKET-0001", json={"status": "resolved"})
    assert_condition(seed_patch_response.status_code == 400, "seed ticket update should fail")


def validate_chat_ticket_idempotency(client: TestClient) -> None:
    request_payload = {
        "question": "Can I have the support contact number.",
        "provider": "nebius",
        "createTicket": True,
        "ticketRequestId": "chat-contact-request-1",
    }

    first_response = client.post("/chat", json=request_payload)
    assert_condition(first_response.status_code == 200, first_response.text)
    first_ticket = first_response.json()["createdTicket"]
    assert_condition(first_ticket["id"] == "TICKET-0027", "expected second runtime ticket")
    assert_condition(first_ticket["issueType"] == "contact_request", "wrong issue type")

    retry_response = client.post("/chat", json=request_payload)
    assert_condition(retry_response.status_code == 200, retry_response.text)
    retry_ticket = retry_response.json()["createdTicket"]
    assert_condition(
        retry_ticket["id"] == first_ticket["id"],
        "chat retry should return existing ticket",
    )

    matching_tickets = [
        ticket
        for ticket in client.get("/tickets").json()
        if ticket.get("idempotencyKey") == "chat-contact-request-1"
    ]
    assert_condition(len(matching_tickets) == 1, "chat retry produced duplicate ticket")

    no_handoff_response = client.post(
        "/chat",
        json={
            "question": "What is the return policy?",
            "provider": "nebius",
            "createTicket": True,
            "ticketRequestId": "normal-answer-ticket-attempt",
        },
    )
    assert_condition(
        no_handoff_response.status_code == 400,
        "normal answer should not create ticket",
    )


def main() -> None:
    seed_path = REPO_ROOT / "data" / "support" / "tickets.json"

    with TemporaryDirectory() as temp_dir:
        runtime_path = Path(temp_dir) / "runtime_tickets.json"
        app.dependency_overrides[get_ticket_repository] = lambda: TicketRepository(
            seed_path=seed_path,
            runtime_path=runtime_path,
        )
        client = TestClient(app)

        validate_ticket_api(client)
        validate_chat_ticket_idempotency(client)

        app.dependency_overrides.clear()

    print("Validated ticket workflow: CRUD, ID generation, filtering, updates, and idempotent chat handoff.")


if __name__ == "__main__":
    main()
