# Ticket Schema

## Goal

Phase 9 adds local support-ticket persistence for chat handoffs and operator review. Seed tickets remain in `data/support/tickets.json`; newly created runtime tickets are stored separately in `data/support/runtime_tickets.json`.

## Storage Files

- `data/support/tickets.json`: synthetic seed tickets created with the support knowledge base.
- `data/support/runtime_tickets.json`: local tickets created during app usage.

Keeping runtime tickets separate prevents rebuild scripts from overwriting user-created support work.

## Local Persistence Limitations

This ticket workflow is intentionally local-first:

- Runtime tickets are stored in JSON, not a production database.
- Writes use a temporary file and replace operation, which is enough for local development but not a substitute for transactional database writes.
- There is no authentication, authorization, role-based access control, audit log, SLA timer, notification queue, email, SMS, phone, or CRM integration.
- The internal support console is hidden behind `?_m=s` for local testing, but that is not production security.
- Seed tickets are read-only; only runtime tickets can be updated.

## Ticket ID

Ticket IDs use the existing format:

```text
TICKET-0026
```

The repository layer should generate the next ID by scanning both seed and runtime tickets and incrementing the highest numeric suffix.

## Runtime Ticket Shape

```json
{
  "id": "TICKET-0026",
  "status": "open",
  "priority": "normal",
  "issueType": "shipping",
  "summary": "Customer reports tracking has not updated.",
  "source": "chat",
  "product": {
    "productId": "B0BYBG1PPD",
    "productTitle": "Gateway 15.6 inch FHD Ultra Slim Budget Notebook",
    "category": "Computers & Storage",
    "subcategory": "Traditional Laptops"
  },
  "handoff": {
    "question": "Where is my order?",
    "conversationExcerpt": "Customer asked for order-specific shipping help.",
    "escalationReason": "Order-specific questions require human review.",
    "agentIntent": "escalation",
    "retrievalSufficient": false
  },
  "contactPreference": "unknown",
  "internalNotes": [],
  "createdAt": "2026-06-10T15:30:00Z",
  "updatedAt": "2026-06-10T15:30:00Z"
}
```

## Field Reference

- `id`: Stable ticket ID in `TICKET-0000` format.
- `status`: One of `open`, `in_progress`, `waiting_on_customer`, or `resolved`.
- `priority`: One of `low`, `normal`, `high`, or `urgent`.
- `issueType`: One of `order`, `shipping`, `return`, `refund`, `warranty`, `payment`, `product_defect`, `missing_parts`, `compatibility`, `setup`, `troubleshooting`, `contact_request`, or `other`.
- `summary`: Short human-readable description of the request.
- `source`: One of `chat`, `support_console`, `api`, or `seed`.
- `product`: Optional product context inferred from chat or selected in the UI.
- `handoff`: Optional chat and agent context used to create the ticket.
- `contactPreference`: One of `email`, `phone`, `none`, or `unknown`.
- `internalNotes`: Operator notes, not shown in normal customer chat.
- `idempotencyKey`: Optional retry key used to prevent duplicate runtime tickets.
- `createdAt`: ISO timestamp for ticket creation.
- `updatedAt`: ISO timestamp for the latest ticket update.

## API Request Models

`TicketCreateRequest` accepts the customer-safe ticket fields without `id`, `status`, `createdAt`, or `updatedAt`. The backend should generate those values.

`TicketCreateRequest` also accepts optional `idempotencyKey`. When the same key is submitted again, the repository returns the existing runtime ticket instead of creating a duplicate.

`TicketUpdateRequest` allows updates to status, priority, issue type, summary, contact preference, and one appended internal note.

## API Examples

Create a ticket:

```http
POST /tickets
Content-Type: application/json

{
  "issueType": "shipping",
  "summary": "Customer reports tracking has not updated.",
  "priority": "normal",
  "source": "chat",
  "product": {
    "productId": "B0BYBG1PPD",
    "productTitle": "Gateway 15.6 inch FHD Ultra Slim Budget Notebook",
    "category": "Computers & Storage",
    "subcategory": "Traditional Laptops"
  },
  "handoff": {
    "question": "Where is my order?",
    "conversationExcerpt": "Customer asked for order-specific shipping help.",
    "escalationReason": "Order-specific questions require human review.",
    "agentIntent": "escalation",
    "retrievalSufficient": false
  },
  "contactPreference": "unknown"
}
```

List tickets:

```http
GET /tickets?status=open&priority=high
```

Inspect one ticket:

```http
GET /tickets/TICKET-0026
```

Update a runtime ticket:

```http
PATCH /tickets/TICKET-0026
Content-Type: application/json

{
  "status": "in_progress",
  "internalNote": "Reviewing shipment details."
}
```

Seed tickets can be listed and inspected, but only runtime tickets can be updated.

## Chat Handoff

`POST /chat` returns a `handoff` object when the support agent decides a question should be escalated. Normal support answers leave this field empty.

Example escalation response fields:

```json
{
  "handoff": {
    "canCreateTicket": true,
    "reason": "Question asks for customer support contact or handoff details.",
    "ticketPayload": {
      "issueType": "contact_request",
      "summary": "Can I have the support contact number.",
      "priority": "normal",
      "source": "chat",
      "product": {
        "productId": null,
        "productTitle": null,
        "category": null,
        "subcategory": null
      },
      "handoff": {
        "question": "Can I have the support contact number.",
        "conversationExcerpt": "Can I have the support contact number.",
        "escalationReason": "Question asks for customer support contact or handoff details.",
        "agentIntent": "escalation_candidate",
        "retrievalSufficient": false
      },
      "contactPreference": "unknown"
    }
  },
  "createdTicket": null
}
```

To create a ticket from a confirmed chat handoff, send the same question with `createTicket: true`:

```http
POST /chat
Content-Type: application/json

{
  "question": "Can I have the support contact number.",
  "provider": "nebius",
  "createTicket": true,
  "ticketRequestId": "stable-message-id-from-ui"
}
```

The response includes `createdTicket` when creation succeeds. If `createTicket` is sent for a normal answer with no handoff, the API returns `400`.
The optional `ticketRequestId` is copied to the ticket `idempotencyKey`, so UI retries return the same ticket instead of creating duplicates.

## Handoff Policy Rules

The support agent uses deterministic handoff rules before ticket creation:

- Contact requests map to `contact_request` with `normal` priority.
- Order/account/tracking/address/invoice requests map to `order` or `shipping` depending on the wording.
- Transaction-specific payment language, such as a card being charged twice, maps to `payment` with `high` priority.
- Shipment-specific language, such as damaged shipment, missing package, delivery, or tracking issues, maps to `shipping`; damaged or missing shipment issues are `high` priority.
- Product damage, defect, or unsafe behavior maps to `product_defect`; urgent safety language such as smoke, sparks, overheating, fire, or unsafe use is `urgent`.
- Missing accessories, parts, components, or pieces map to `missing_parts`.
- Repeated unresolved troubleshooting language maps to `troubleshooting` with `high` priority.
- Unsupported non-electronics-category questions remain clarification responses and do not offer ticket creation by default.

Customer-facing handoff language stays honest about local-demo limits: it does not invent phone numbers, personal order data, tracking status, payment records, or shipment records. It offers self-service policy help when available, or ticket preparation when specialist review is needed.

The support-ticket console is an internal local view, not part of the default customer UI. Open it with:

```text
http://127.0.0.1:5173/?_m=s#/support/tickets
```

Developer/eval evidence mode is separate:

```text
http://127.0.0.1:5173/?_m=e
```

## Backend Schema Source

The Pydantic schema lives in `backend/app/ticket_schema.py`.

## Repository Layer

The local repository lives in `backend/app/ticket_repository.py`.

It is responsible for:

- Loading seed tickets from `data/support/tickets.json`.
- Loading runtime tickets from `data/support/runtime_tickets.json`.
- Normalizing legacy seed fields into the runtime schema.
- Generating the next ticket ID by scanning seed and runtime tickets.
- Creating runtime tickets.
- Updating runtime tickets.
- Filtering tickets by status, priority, issue type, and product ID.
- Writing runtime ticket changes through a temporary file before replacing the target file.

Seed tickets are read-only. The repository can list and inspect them, but update operations are intended for runtime tickets created during app usage.
