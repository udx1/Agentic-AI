import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from app.ticket_schema import (
    IssueType,
    SupportTicket,
    TicketCreateRequest,
    TicketListFilters,
    TicketProductContext,
    TicketUpdateRequest,
)


TICKET_ID_PATTERN = re.compile(r"^TICKET-(\d{4,})$")
SEED_TICKET_TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)
LEGACY_ISSUE_TYPE_MAP: dict[str, IssueType] = {
    "defect": "product_defect",
}


class TicketRepositoryError(RuntimeError):
    pass


class TicketNotFoundError(TicketRepositoryError):
    pass


class TicketRepository:
    def __init__(self, seed_path: Path, runtime_path: Path):
        self.seed_path = seed_path
        self.runtime_path = runtime_path

    def list_tickets(self, filters: TicketListFilters | None = None) -> list[SupportTicket]:
        tickets = sorted(
            [*self.load_seed_tickets(), *self.load_runtime_tickets()],
            key=lambda ticket: ticket.id,
        )
        if filters is None:
            return tickets
        return [ticket for ticket in tickets if self._matches_filters(ticket, filters)]

    def get_ticket(self, ticket_id: str) -> SupportTicket:
        ticket = next(
            (ticket for ticket in self.list_tickets() if ticket.id == ticket_id),
            None,
        )
        if ticket is None:
            raise TicketNotFoundError(f"Ticket not found: {ticket_id}")
        return ticket

    def create_ticket(self, request: TicketCreateRequest) -> SupportTicket:
        existing_ticket = self.find_runtime_ticket_by_idempotency_key(request.idempotencyKey)
        if existing_ticket is not None:
            return existing_ticket

        now = datetime.now(UTC)
        ticket = SupportTicket(
            id=self.next_ticket_id(),
            status="open",
            priority=request.priority,
            issueType=request.issueType,
            summary=request.summary.strip(),
            source=request.source,
            product=request.product,
            handoff=request.handoff,
            contactPreference=request.contactPreference,
            idempotencyKey=request.idempotencyKey,
            createdAt=now,
            updatedAt=now,
        )
        runtime_tickets = self.load_runtime_tickets()
        self._write_runtime_tickets([*runtime_tickets, ticket])
        return ticket

    def find_runtime_ticket_by_idempotency_key(
        self,
        idempotency_key: str | None,
    ) -> SupportTicket | None:
        if not idempotency_key:
            return None
        return next(
            (
                ticket
                for ticket in self.load_runtime_tickets()
                if ticket.idempotencyKey == idempotency_key
            ),
            None,
        )

    def update_ticket(self, ticket_id: str, request: TicketUpdateRequest) -> SupportTicket:
        runtime_tickets = self.load_runtime_tickets()
        updated_tickets: list[SupportTicket] = []
        updated_ticket: SupportTicket | None = None

        for ticket in runtime_tickets:
            if ticket.id != ticket_id:
                updated_tickets.append(ticket)
                continue

            update_data = request.model_dump(exclude_none=True)
            internal_note = update_data.pop("internalNote", None)
            if internal_note is not None:
                update_data["internalNotes"] = [
                    *ticket.internalNotes,
                    internal_note.strip(),
                ]
            update_data["updatedAt"] = datetime.now(UTC)
            updated_ticket = ticket.model_copy(update=update_data)
            updated_tickets.append(updated_ticket)

        if updated_ticket is None:
            self.get_ticket(ticket_id)
            raise TicketRepositoryError(f"Seed tickets cannot be updated: {ticket_id}")

        self._write_runtime_tickets(updated_tickets)
        return updated_ticket

    def next_ticket_id(self) -> str:
        highest = 0
        for ticket in self.list_tickets():
            match = TICKET_ID_PATTERN.match(ticket.id)
            if match:
                highest = max(highest, int(match.group(1)))
        return f"TICKET-{highest + 1:04d}"

    def load_seed_tickets(self) -> list[SupportTicket]:
        raw_tickets = self._read_ticket_json(self.seed_path, required=True)
        return [self._normalize_seed_ticket(raw_ticket) for raw_ticket in raw_tickets]

    def load_runtime_tickets(self) -> list[SupportTicket]:
        raw_tickets = self._read_ticket_json(self.runtime_path, required=False)
        try:
            return [SupportTicket.model_validate(raw_ticket) for raw_ticket in raw_tickets]
        except ValidationError as exc:
            raise TicketRepositoryError(
                f"Runtime ticket file is malformed: {self.runtime_path}"
            ) from exc

    def _read_ticket_json(self, path: Path, required: bool) -> list[dict]:
        if not path.exists():
            if required:
                raise TicketRepositoryError(f"Ticket data file not found: {path}")
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TicketRepositoryError(f"Ticket data file is not valid JSON: {path}") from exc
        if data is None:
            return []
        if not isinstance(data, list):
            raise TicketRepositoryError(f"Ticket data file must contain a JSON list: {path}")
        if not all(isinstance(item, dict) for item in data):
            raise TicketRepositoryError(f"Ticket data file must contain ticket objects: {path}")
        return data

    def _write_runtime_tickets(self, tickets: list[SupportTicket]) -> None:
        self.runtime_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.runtime_path.with_suffix(f"{self.runtime_path.suffix}.tmp")
        payload = [ticket.model_dump(mode="json") for ticket in sorted(tickets, key=lambda item: item.id)]
        temp_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, self.runtime_path)

    def _normalize_seed_ticket(self, raw_ticket: dict) -> SupportTicket:
        issue_type = LEGACY_ISSUE_TYPE_MAP.get(
            str(raw_ticket.get("issueType", "other")),
            str(raw_ticket.get("issueType", "other")),
        )
        normalized = {
            "id": raw_ticket.get("id"),
            "status": raw_ticket.get("status", "open"),
            "priority": raw_ticket.get("priority", "normal"),
            "issueType": issue_type,
            "summary": raw_ticket.get("summary", "Seed support ticket"),
            "source": "seed",
            "product": TicketProductContext(
                productId=raw_ticket.get("productId"),
                productTitle=raw_ticket.get("productTitle"),
                category=raw_ticket.get("category"),
                subcategory=raw_ticket.get("subcategory"),
            ),
            "createdAt": SEED_TICKET_TIMESTAMP,
            "updatedAt": SEED_TICKET_TIMESTAMP,
        }
        try:
            return SupportTicket.model_validate(normalized)
        except ValidationError as exc:
            raise TicketRepositoryError(
                f"Seed ticket is malformed: {raw_ticket.get('id', '<missing id>')}"
            ) from exc

    @staticmethod
    def _matches_filters(ticket: SupportTicket, filters: TicketListFilters) -> bool:
        if filters.status is not None and ticket.status != filters.status:
            return False
        if filters.priority is not None and ticket.priority != filters.priority:
            return False
        if filters.issueType is not None and ticket.issueType != filters.issueType:
            return False
        if filters.productId is not None and ticket.product.productId != filters.productId:
            return False
        return True
