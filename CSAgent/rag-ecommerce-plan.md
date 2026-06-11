# Local Ecommerce + RAG Support Plan

## Goal

Build a simple local ecommerce site using a clean subset of 50 Electronics products from the UCSD Amazon dataset, then extend it with a RAG-based customer support chat agent.

The project should be built in phases so each layer is understandable: data, UI, app logic, backend, knowledge base, retrieval, chat, and support ticket fallback.

## Build Approach

Build by capability layer, but keep each phase small and testable.

For each phase:

1. Build the feature.
2. Review how it works.
3. Capture short learning notes.

Suggested learning docs:

```text
docs/
  build-plan.md
  learning-notes.md
```

## Phase 0: Project Setup

Create the initial project structure and decide the stack.

Recommended stack:

- React/Vite frontend
- FastAPI backend
- Local JSON and markdown data files
- LangChain for RAG pipeline components
- LangGraph for support agent workflow
- Chroma for local vector search first
- Pinecone as a later cloud vector database option
- Nebius embeddings for the current local vector store
- Claude through Anthropic for planned chat-completion answer generation
- OpenAI remains optional after quota is available

Suggested folders:

```text
data/
  raw/
  catalog/
  reviews/
  knowledge_base/
  support/
docs/
frontend/
backend/
```

## Phase 1: Data First

Use the UCSD Amazon Electronics dataset to create a clean 50-product catalog.

Tasks:

- Inspect the dataset shape.
- Select 50 clean Electronics products.
- Normalize product fields.
- Save the final catalog as `data/catalog/products.json`.

Recommended product fields:

- `id`
- `title`
- `brand`
- `category`
- `subcategory`
- `price`
- `rating`
- `reviewCount`
- `image`
- `description`
- `features`

Learning focus:

- Dataset inspection
- Data cleaning
- Schema design
- Normalizing messy source data

## Phase 2: UI Baseline

Build the first ecommerce interface using the local product JSON.

Core features:

- Product listing page
- Product detail page
- Product cards
- Basic responsive layout

Learning focus:

- React components
- Props and state
- Routing
- Product-driven UI rendering

## Phase 3: Frontend Logic

Add ecommerce behavior to the UI.

Core features:

- Search
- Category filtering
- Sorting by price or rating
- Cart UI
- Add, remove, and update item quantity

Learning focus:

- Frontend state management
- Derived data
- User workflows
- Local cart behavior

## Phase 4: Backend API

Add a FastAPI backend and move product access behind API endpoints.

Suggested endpoints:

- `GET /products`
- `GET /products/{id}`
- `GET /categories`

Learning focus:

- API design
- Backend/frontend separation
- Request and response models
- Serving structured data

## Phase 5: Local Support Knowledge Base

Because the dataset does not include manuals, FAQs, or support content, create a small synthetic knowledge base tied to the same 50 products.

Also bring in a small real review sample from the same UCSD Amazon Electronics dataset for each selected catalog product. Keep reviews separate from the product catalog so `products.json` remains lightweight for ecommerce browsing.

Recommended documents:

- Product FAQs
- Setup notes
- Troubleshooting guides
- Compatibility notes
- Store policies for shipping, returns, refunds, warranty, and payments
- 5-6 clean customer reviews per selected product
- Synthetic support tickets

Suggested structure:

```text
data/
  reviews/
    product_reviews.json
  knowledge_base/
    store_policies/
      shipping.md
      returns.md
      warranty.md
      payments.md
    products/
      <product_id>/
        faq.md
        setup.md
        troubleshooting.md
        compatibility.md
  support/
    tickets.json
```

Learning focus:

- Writing RAG-friendly documents
- Using real customer review text as retrieval context
- Separating catalog data from support knowledge
- Designing metadata for retrieval

## Phase 6: RAG Pipeline

Build the local retrieval pipeline.

Status: complete.

Core steps:

- Load product catalog and knowledge documents.
- Chunk support documents.
- Preview embeddings in memory on a small chunk sample.
- Run a full embedding pass inside the Chroma vector-store build.
- Index vectors and store them in Chroma for the first local implementation.
- Retrieve relevant chunks for a user question.
- Generate grounded preview answers with citations.
- Expose the deterministic cited answer layer through `POST /chat`.

Framework strategy:

- Use LangChain for document loading, splitting, embeddings, vector store integration, retrievers, and prompt templates.
- Use LangChain vector store abstractions so Chroma can later be swapped or extended with Pinecone.
- Add Pinecone after local retrieval works reliably.

Learning focus:

- Document loading
- Chunking
- Preview embeddings versus persisted vector-store embeddings
- Chroma vector indexing and storage
- Retrieval
- Retrieval metadata
- Grounded citations

## Phase 7: Support Chat Agent

Add a chat endpoint that uses retrieved context to answer customer questions.

Status: complete.

Suggested endpoint:

- `POST /chat`

Expected chat capabilities:

- Answer product questions
- Explain setup and troubleshooting steps
- Answer return, refund, warranty, and shipping questions
- Compare products using catalog data
- Cite retrieved sources

LangGraph workflow:

- Accept user question.
- Identify whether the question is about a product, policy, troubleshooting issue, comparison, or support ticket.
- Retrieve relevant product, support, policy, and ticket context.
- Assess whether retrieved context is sufficient.
- Generate a grounded answer with citations.
- Ask for clarification or create a support ticket when context is insufficient.

Current implementation notes:

- `/chat` is backed by a LangGraph workflow.
- The first implementation is deterministic and works without a chat-completion model.
- Claude through Anthropic is planned for natural final answers after retrieval.
- Clarification and escalation preparation are implemented.
- Persistent ticket creation remains Phase 9.
- Developer/debug trace mode remains a later observability/eval enhancement.

Learning focus:

- Prompt design
- Grounded generation
- Citations
- Handling missing or weak context

## Phase 8: Chat UI

Connect the ecommerce frontend to the support chat API.

Status: complete.

Core features:

- Floating support chat panel
- Product-aware starter prompts
- Customer-facing answers in normal support mode
- Eval/developer evidence mode with `?_m=e`
- Loading, error, and draft-preservation states
- Catalog availability and ranking questions routed through catalog data
- Support contact and handoff questions routed to escalation behavior

Learning focus:

- Frontend/backend integration
- API calls from React
- Conversational UI states

## Phase 9: Support Workflow

Add ticket persistence and support workflow extensions so escalation and handoff responses can become trackable local support tickets.

Suggested endpoints:

- `POST /tickets`
- `GET /tickets`
- `GET /tickets/{ticket_id}`
- `PATCH /tickets/{ticket_id}`

Core features:

- Create a ticket from a confirmed chat handoff
- Store runtime tickets locally without overwriting seed tickets
- Show ticket confirmation in the chat UI
- Add a lightweight support console for reviewing open tickets
- Allow status and priority updates
- Keep normal support mode clean while eval mode shows handoff/debug metadata

Learning focus:

- Agent escalation workflow
- Confidence handling
- Persisting support requests
- Local workflow state
- Backend CRUD APIs

## Later RAG Enhancement: LangChain Prompted LLM Answers

Add LangChain chat prompt templates for final answer generation after retrieval and context sufficiency checks.

Core features:

- Define a customer-support persona for the LLM.
- Use a `ChatPromptTemplate` that includes system/persona instructions, retrieved context, citation rules, and the customer question.
- Require grounded answers that only use retrieved support/catalog context.
- Keep the deterministic answer formatter as fallback when the LLM provider is unavailable.
- Preserve the existing `/chat` response shape.
- Show prompt/debug metadata only in eval mode.

Learning focus:

- LangChain prompt templates
- Persona design
- Grounded LLM generation
- Fallback behavior
- Eval/debug observability

## Later RAG Enhancement: Product Manuals

Add product manual or manual-excerpt documents as first-class retrieval sources.

Core features:

- Generate or ingest `manual.md` or `manual_excerpt.md` documents per product.
- Add a `product_manual` document type to the loader metadata.
- Include manuals in chunking, embedding, Chroma indexing, hybrid retrieval, and citations.
- Add validation cases for manual-style questions, such as installation steps, button behavior, care instructions, and safety notes.
- Preserve the existing fallback behavior when manuals do not contain enough context.

Learning focus:

- RAG source coverage
- Metadata design
- Retrieval validation
- Manual-style support grounding

## Target Demo

A customer can browse 50 electronics products, ask support questions about any product, receive grounded answers with citations, and create a support ticket when needed.
