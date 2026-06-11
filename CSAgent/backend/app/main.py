import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="CSAgent Ecommerce Support API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = REPO_ROOT / "data" / "catalog"
REVIEWS_DIR = REPO_ROOT / "data" / "reviews"
SUPPORT_DIR = REPO_ROOT / "data" / "support"
PRODUCTS_PATH = CATALOG_DIR / "products.json"
CATEGORIES_PATH = CATALOG_DIR / "categories.json"
REVIEWS_PATH = REVIEWS_DIR / "product_reviews.json"
SEED_TICKETS_PATH = SUPPORT_DIR / "tickets.json"
RUNTIME_TICKETS_PATH = SUPPORT_DIR / "runtime_tickets.json"
RAG_PIPELINE_DIR = REPO_ROOT / "rag_pipeline"

if str(RAG_PIPELINE_DIR) not in sys.path:
    sys.path.append(str(RAG_PIPELINE_DIR))

from support_agent import run_support_agent  # noqa: E402
from app.ticket_repository import (  # noqa: E402
    TicketNotFoundError,
    TicketRepository,
    TicketRepositoryError,
)
from app.ticket_schema import (  # noqa: E402
    IssueType,
    SupportTicket,
    TicketCreateRequest,
    TicketListFilters,
    TicketPriority,
    TicketStatus,
    TicketUpdateRequest,
)


class Product(BaseModel):
    id: str
    title: str
    brand: str
    category: str
    subcategory: str
    price: float
    rating: float
    reviewCount: int
    image: str
    description: str
    features: list[str]


class Category(BaseModel):
    id: str
    name: str
    description: str
    subcategories: list[str]


class Review(BaseModel):
    reviewId: str
    asin: str
    rating: float
    title: str
    text: str
    helpfulVotes: int
    verifiedPurchase: bool
    timestamp: int


class ChatRequest(BaseModel):
    question: str
    provider: Literal["hashing", "openai", "nebius"] = "nebius"
    debug: bool = False
    createTicket: bool = False
    ticketRequestId: str | None = None


class ChatCitation(BaseModel):
    id: str
    label: str
    sourcePath: str
    docType: str
    productId: str | None
    chunkId: str


class RetrievedContext(BaseModel):
    rank: int
    docType: str
    sourcePath: str
    chunkId: str
    productId: str | None
    vectorScore: float | str
    lexicalScore: int
    snippet: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    provider: str
    citations: list[ChatCitation]
    retrievedContext: list[RetrievedContext]
    handoff: dict | None = None
    createdTicket: SupportTicket | None = None
    debug: dict | None = None


@lru_cache
def load_products() -> list[Product]:
    return [Product.model_validate(product) for product in read_json(PRODUCTS_PATH)]


@lru_cache
def load_categories() -> list[Category]:
    return [Category.model_validate(category) for category in read_json(CATEGORIES_PATH)]


@lru_cache
def load_reviews() -> dict[str, list[Review]]:
    reviews_by_product = read_json(REVIEWS_PATH)
    return {
        product_id: [Review.model_validate(review) for review in reviews]
        for product_id, reviews in reviews_by_product.items()
    }


@lru_cache
def get_ticket_repository() -> TicketRepository:
    return TicketRepository(
        seed_path=SEED_TICKETS_PATH,
        runtime_path=RUNTIME_TICKETS_PATH,
    )


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Catalog data file not found: {path}") from exc


def compact_for_api(value: str, limit: int = 280) -> str:
    compacted = " ".join(value.split())
    if len(compacted) <= limit:
        return compacted
    return f"{compacted[: limit - 3]}..."


def api_score(value: float) -> float | str:
    if value == float("inf"):
        return "inf"
    return value


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products", response_model=list[Product])
def get_products() -> list[Product]:
    return load_products()


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    product = next((product for product in load_products() if product.id == product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/categories", response_model=list[Category])
def get_categories() -> list[Category]:
    return load_categories()


@app.get("/products/{product_id}/reviews", response_model=list[Review])
def get_product_reviews(product_id: str) -> list[Review]:
    product = next((product for product in load_products() if product.id == product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return load_reviews().get(product_id, [])


@app.post("/tickets", response_model=SupportTicket, status_code=201)
def create_ticket(
    request: TicketCreateRequest,
    ticket_repository: TicketRepository = Depends(get_ticket_repository),
) -> SupportTicket:
    try:
        return ticket_repository.create_ticket(request)
    except TicketRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/tickets", response_model=list[SupportTicket])
def list_tickets(
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    issueType: IssueType | None = None,
    productId: str | None = None,
    ticket_repository: TicketRepository = Depends(get_ticket_repository),
) -> list[SupportTicket]:
    filters = TicketListFilters(
        status=status,
        priority=priority,
        issueType=issueType,
        productId=productId,
    )
    try:
        return ticket_repository.list_tickets(filters)
    except TicketRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/tickets/{ticket_id}", response_model=SupportTicket)
def get_ticket(
    ticket_id: str,
    ticket_repository: TicketRepository = Depends(get_ticket_repository),
) -> SupportTicket:
    try:
        return ticket_repository.get_ticket(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TicketRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.patch("/tickets/{ticket_id}", response_model=SupportTicket)
def update_ticket(
    ticket_id: str,
    request: TicketUpdateRequest,
    ticket_repository: TicketRepository = Depends(get_ticket_repository),
) -> SupportTicket:
    try:
        return ticket_repository.update_ticket(ticket_id, request)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TicketRepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    ticket_repository: TicketRepository = Depends(get_ticket_repository),
) -> ChatResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        agent_result = run_support_agent(
            question=question,
            provider=request.provider,
            include_debug=request.debug,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate support answer: {exc}",
        ) from exc

    citations = [
        ChatCitation(
            id=citation.id,
            label=citation.label,
            sourcePath=citation.source_path,
            docType=citation.doc_type,
            productId=citation.product_id,
            chunkId=citation.chunk_id,
        )
    for citation in agent_result.citations
    ]
    retrieved_context = []
    for rank, result in enumerate(agent_result.retrieved_results, start=1):
        metadata = result.document.metadata
        retrieved_context.append(
            RetrievedContext(
                rank=rank,
                docType=str(metadata.get("doc_type", "unknown")),
                sourcePath=str(metadata.get("source_path", "unknown")),
                chunkId=str(metadata.get("chunk_id", "unknown")),
                productId=(
                    str(metadata["product_id"])
                    if metadata.get("product_id") is not None
                    else None
                ),
                vectorScore=api_score(result.vector_score),
                lexicalScore=result.lexical_score,
                snippet=compact_for_api(result.document.page_content),
            )
        )

    created_ticket = None
    handoff = agent_result.handoff
    if request.createTicket:
        if not handoff or not handoff.get("canCreateTicket"):
            raise HTTPException(
                status_code=400,
                detail="Ticket creation requires a support handoff.",
            )
        try:
            ticket_payload = TicketCreateRequest.model_validate(handoff.get("ticketPayload", {}))
            if request.ticketRequestId:
                ticket_payload = ticket_payload.model_copy(
                    update={"idempotencyKey": request.ticketRequestId}
                )
            created_ticket = ticket_repository.create_ticket(ticket_payload)
        except TicketRepositoryError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        question=agent_result.question,
        answer=agent_result.answer,
        provider=request.provider,
        citations=citations,
        retrievedContext=retrieved_context,
        handoff=handoff,
        createdTicket=created_ticket,
        debug=agent_result.debug if request.debug else None,
    )
