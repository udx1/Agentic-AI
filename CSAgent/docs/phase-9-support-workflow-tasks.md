# Phase 9 Support Workflow Tasks

## Goal

Add ticket persistence and support workflow extensions so escalation/handoff responses from the support agent can become trackable local support tickets.

Phase 8 already detects handoff cases, including order-specific questions, weak-context support requests, urgent safety wording, and contact-number requests. Phase 9 should turn those prepared handoffs into a usable backend and frontend workflow.

## Current Baseline

- The backend exposes `POST /chat`.
- The LangGraph support agent can classify escalation/handoff cases.
- Chat responses can include developer debug metadata when requested.
- Existing synthetic seed tickets live in `data/support/tickets.json`.
- The frontend has a floating support chat panel.
- Normal support mode hides citations, retrieved context, and debug traces.
- Eval/debug mode is available with `?_m=e`.
- Internal support-ticket console mode is available with `?_m=s`.

## Phase 9 Task List

Status: complete.

### 1. Ticket Data Model

- [x] Define the local ticket schema for newly created support tickets.
- [x] Keep compatibility with the existing seed ticket fields where practical: `id`, `productId`, `productTitle`, `category`, `subcategory`, `issueType`, `summary`, `status`, and `priority`.
- [x] Add customer workflow fields needed by chat-created tickets, such as `source`, `question`, `conversationExcerpt`, `createdAt`, `updatedAt`, and optional `contactPreference`.
- [x] Decide the first local storage file path for runtime tickets, for example `data/support/runtime_tickets.json`.
- [x] Keep generated runtime tickets separate from the seed dataset so rebuild scripts do not overwrite user-created tickets.

### 2. Ticket Repository Layer

- [x] Add a small backend repository/helper for loading, validating, creating, updating, and listing tickets.
- [x] Generate stable local ticket IDs such as `TICKET-0026`, continuing after the highest seed/runtime ID.
- [x] Make writes atomic enough for local development by writing through a temporary file and replacing the target.
- [x] Add defensive handling for missing, empty, or malformed runtime ticket files.
- [x] Add filtering helpers for status, priority, issue type, and product ID.

### 3. Ticket API Endpoints

- [x] Add `POST /tickets` to create a ticket directly.
- [x] Add `GET /tickets` to list tickets, with optional filters.
- [x] Add `GET /tickets/{ticket_id}` to inspect a ticket.
- [x] Add `PATCH /tickets/{ticket_id}` to update status, priority, summary, or internal notes.
- [x] Return clear 400/404 errors for invalid ticket input or unknown ticket IDs.
- [x] Keep request and response models explicit with Pydantic.

### 4. Chat-To-Ticket Handoff

- [x] Extend support-agent escalation results with structured handoff fields that are safe for ticket creation.
- [x] Add an optional `createTicket` flag or separate chat follow-up action so normal answers do not create tickets unexpectedly.
- [x] When the user confirms handoff, create a ticket using the chat question, inferred issue type, product hints, priority, and escalation reason.
- [x] Return the created ticket ID in the chat or ticket response.
- [x] Keep contact-number requests honest: do not invent a phone number; offer ticket creation or supported self-service paths.

### 5. Frontend Chat Workflow

- [x] In the support chat panel, show a ticket creation action only when the backend indicates handoff is appropriate.
- [x] Confirm ticket creation before calling `POST /tickets`.
- [x] Show a clear ticket confirmation with ticket ID and current status.
- [x] Preserve the user's chat draft and message history when ticket creation fails.
- [x] Keep ticket controls out of normal answers where no escalation is needed.
- [x] Ensure eval mode can show the escalation reason and ticket payload preview.

### 6. Support Console View

- [x] Add a lightweight support console route or panel for local operators.
- [x] List open tickets with status, priority, issue type, product, and creation time.
- [x] Add filters for open/resolved tickets and high-priority tickets.
- [x] Add a ticket detail view with conversation excerpt and product context.
- [x] Allow status updates such as `open`, `in_progress`, `waiting_on_customer`, and `resolved`.
- [x] Keep the console visually consistent with the existing ecommerce UI without turning it into a marketing page.

### 7. Agent Policy And Priority Rules

- [x] Define deterministic issue-type mapping for order, shipping, return, refund, warranty, payment, product defect, missing part, compatibility, setup, and contact requests.
- [x] Define priority rules for safety language, damaged shipment, missing delivery, payment issue, and repeated unresolved troubleshooting.
- [x] Ensure unsupported-category questions still avoid creating misleading electronics tickets unless the user explicitly wants general help.
- [x] Ensure weak retrieval context can trigger handoff without exposing retrieved context in normal support mode.

### 8. Validation And Regression Tests

- [x] Extend `rag_pipeline/validate_support_agent.py` with ticket-handoff expectations.
- [x] Add backend tests or scripts for ticket create/list/get/update behavior.
- [x] Add validation for ID generation across seed and runtime tickets.
- [x] Add validation that chat handoff does not create duplicate tickets on repeated render or retry.
- [x] Create a 20-query first-contact resolution eval dataset.
- [x] Add frontend build verification with `npm run build`.
- [x] Manually test chat handoff questions such as `Where is my order?`, `Can I have the support contact number?`, and `The product is damaged and I need help`.

### 9. Documentation

- [x] Update `PROJECT_STATUS.md` when Phase 9 implementation starts and completes.
- [x] Update `docs/build-plan.md` with the completed Phase 8 status and expanded Phase 9 scope.
- [x] Document the ticket schema and runtime storage behavior.
- [x] Add example API requests for `POST /tickets`, `GET /tickets`, and `PATCH /tickets/{ticket_id}`.
- [x] Document the expected customer-facing handoff language.
- [x] Add notes about local-only persistence and any limitations.

## Acceptance Criteria

- A chat handoff can become a persisted local ticket only after a user confirmation or explicit ticket-create request.
- Created tickets survive backend restart because they are stored in a local JSON file.
- Ticket APIs support create, list, detail, and status update operations.
- The frontend shows ticket confirmation with the ticket ID.
- The support-ticket console is hidden from the default customer view and shown only with `?_m=s`.
- Normal support mode remains customer-facing and does not show citations, retrieved context, or debug traces.
- Eval mode continues to expose relevant support-agent trace metadata.
- Existing Phase 8 support-agent regression cases still pass.

## Out Of Scope For Phase 9

- Real email, SMS, or phone integration.
- Authentication and role-based access control.
- Production database migration.
- Multi-agent operator assignment.
- SLA timers or notification queues.
- LangChain chat prompt templates and LLM persona-driven final answer generation.

## Completion Summary

Phase 9 is complete.

Completed:

- Added explicit Pydantic ticket schema models.
- Added local runtime ticket storage in `data/support/runtime_tickets.json`.
- Kept seed tickets in `data/support/tickets.json` read-only.
- Added ticket repository helpers for loading, validating, creating, updating, filtering, ID generation, and idempotent runtime ticket creation.
- Added ticket APIs: `POST /tickets`, `GET /tickets`, `GET /tickets/{ticket_id}`, and `PATCH /tickets/{ticket_id}`.
- Added chat handoff metadata and confirmed chat ticket creation with `createTicket: true`.
- Added retry-safe chat ticket creation with `ticketRequestId` / `idempotencyKey`.
- Added frontend ticket creation from handoff responses.
- Added internal support console at `?_m=s#/support/tickets`.
- Kept the support console hidden from the default customer view.
- Added deterministic issue-type and priority rules for handoff tickets.
- Added a 20-query first-contact-resolution eval dataset.
- Added repeatable validations for support-agent behavior and ticket workflow behavior.

Validation:

```powershell
cd backend
uv run python ../rag_pipeline/validate_support_agent.py
uv run python ../rag_pipeline/validate_ticket_workflow.py
cd ../frontend
npm run build
```

Limitations:

- Ticket persistence is local JSON only.
- Runtime tickets are not protected by authentication or role-based access control.
- The support console is mode-gated for local/internal testing, not production-secured.
- No real phone, email, SMS, CRM, notification, or operator-assignment integration exists.
- Concurrent writes are acceptable for local development, but a production system should use a real database and transactional writes.
