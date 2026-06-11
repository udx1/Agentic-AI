from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TicketStatus = Literal["open", "in_progress", "waiting_on_customer", "resolved"]
TicketPriority = Literal["low", "normal", "high", "urgent"]
TicketSource = Literal["chat", "support_console", "api", "seed"]
ContactPreference = Literal["email", "phone", "none", "unknown"]
IssueType = Literal[
    "order",
    "shipping",
    "return",
    "refund",
    "warranty",
    "payment",
    "product_defect",
    "missing_parts",
    "compatibility",
    "setup",
    "troubleshooting",
    "contact_request",
    "other",
]


class TicketProductContext(BaseModel):
    productId: str | None = None
    productTitle: str | None = None
    category: str | None = None
    subcategory: str | None = None


class TicketHandoffContext(BaseModel):
    question: str | None = None
    conversationExcerpt: str | None = None
    escalationReason: str | None = None
    agentIntent: str | None = None
    retrievalSufficient: bool | None = None


class SupportTicket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^TICKET-\d{4,}$")
    status: TicketStatus = "open"
    priority: TicketPriority = "normal"
    issueType: IssueType = "other"
    summary: str = Field(min_length=1)
    source: TicketSource = "api"
    product: TicketProductContext = Field(default_factory=TicketProductContext)
    handoff: TicketHandoffContext = Field(default_factory=TicketHandoffContext)
    contactPreference: ContactPreference = "unknown"
    idempotencyKey: str | None = Field(default=None, max_length=120)
    internalNotes: list[str] = Field(default_factory=list)
    createdAt: datetime
    updatedAt: datetime


class TicketCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issueType: IssueType = "other"
    summary: str = Field(min_length=1, max_length=500)
    priority: TicketPriority = "normal"
    source: TicketSource = "api"
    product: TicketProductContext = Field(default_factory=TicketProductContext)
    handoff: TicketHandoffContext = Field(default_factory=TicketHandoffContext)
    contactPreference: ContactPreference = "unknown"
    idempotencyKey: str | None = Field(default=None, max_length=120)


class TicketUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    issueType: IssueType | None = None
    summary: str | None = Field(default=None, min_length=1, max_length=500)
    contactPreference: ContactPreference | None = None
    internalNote: str | None = Field(default=None, min_length=1, max_length=1000)


class TicketListFilters(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    issueType: IssueType | None = None
    productId: str | None = None
