# Phase 8 Chat UI Tasks

## Goal

Add a frontend support chat experience to the React ecommerce app and connect it to the LangGraph-backed backend `POST /chat` endpoint.

The backend API is already stable:

```json
{
  "question": "What is the return policy?",
  "provider": "nebius"
}
```

Response fields:

- `question`
- `answer`
- `provider`
- `citations`
- `retrievedContext`

## Current Frontend Baseline

- The frontend is a React/Vite app in `frontend/`.
- Main UI lives in `frontend/src/main.jsx`.
- Styling lives in `frontend/src/styles.css`.
- The frontend already uses `apiBaseUrl` for product, category, and review API calls.
- The UI is catalog-first with product listing, product detail, reviews, local cart, and a floating support chat panel.
- Normal support mode shows customer-facing answers only.
- Eval mode is unlocked with `?eval=z` and shows citations, retrieved context, and developer trace details.

## Phase 8 Task List

Status: complete.

### 1. Chat UI Placement and Shape

- [x] Decide whether the first chat surface is a floating support panel, a full support page, or a product-detail support section.
- [x] Start with a floating support panel so chat is available from catalog and product pages.
- [x] Add a support/chat button in the existing header controls area.
- [x] Make the chat panel responsive on mobile and desktop.
- [x] Keep the panel visually consistent with the existing cart panel and product UI.

### 2. Chat State Design

- [x] Add frontend state for whether the chat panel is open.
- [x] Add message history state with user and assistant messages.
- [x] Add input text state.
- [x] Add loading state for in-flight chat requests.
- [x] Add error state for failed requests.
- [x] Store citations and retrieved context with assistant messages.

### 3. API Client Function

- [x] Add a `sendChatQuestion(question)` helper that calls `POST /chat`.
- [x] Use the existing `apiBaseUrl`.
- [x] Send provider as `nebius` for now.
- [x] Handle non-200 responses with a clear frontend error.
- [x] Keep the backend response shape unchanged.

### 4. Chat Panel UI

- [x] Add message list rendering.
- [x] Distinguish user messages from assistant messages.
- [x] Add an input box and submit button.
- [x] Disable submit while loading or when the input is empty.
- [x] Add a loading indicator while waiting for the backend.
- [x] Add empty-state prompt suggestions, such as returns, setup, troubleshooting, and compatibility.
- [x] Add a close button and accessible labels.

### 5. Citations and Retrieved Context

- [x] Display citations under assistant answers when available.
- [x] Show source labels, document type, product ID when available, and source path.
- [x] Add a compact expandable section for retrieved context snippets.
- [x] Hide citations and retrieved context for clarification or escalation responses with no sources.

### 6. Product-Aware Support

- [x] When a user is on a product detail page, offer a product-aware starter prompt.
- [x] Optionally prefill product context in the question text, such as product title or product ID.
- [x] Keep the first version simple: do not change the backend API contract yet.

### 7. Error and Edge States

- [x] Show a friendly error if the backend is unavailable.
- [x] Preserve the user's draft question after an error.
- [x] Prevent duplicate sends while loading.
- [x] Handle empty or whitespace-only input.
- [x] Ensure clarification and escalation answers render cleanly with no citation section.

### 8. Developer Mode Planning

- [x] Do not expose debug traces in the first customer-facing chat UI.
- [x] Reserve space in the design for a later developer/debug panel.
- [x] Later backend enhancement: add optional trace/debug metadata for observability and eval.
- [x] Add a frontend developer-mode toggle that is hidden from the default customer flow and unlocked with `?eval=z`.
- [x] When developer mode is enabled, send a debug flag with chat requests without changing the normal customer request path.
- [x] Extend `POST /chat` to optionally return debug metadata such as intent, product hints, retrieval plan, sufficiency decision, retrieval scores, and selected graph path.
- [x] Render debug metadata in a compact expandable developer panel separate from customer-facing citations.
- [x] Keep developer mode disabled by default and safe to ignore when the backend does not return debug metadata.
- [x] Hide citations and retrieved context in normal support mode; show them only in eval/developer mode.
- [x] Enable eval/developer evidence by default when the URL includes `?eval=z`.

### 9. Claude LLM Answer Generation Planning

- [x] Add Claude as the planned chat-completion provider for natural support answers.
- [x] Keep Nebius as the current embedding provider for retrieval.
- [x] Add backend configuration for an Anthropic/Claude API key and model name.
- [x] Add an LLM answer-generation step after retrieval/context sufficiency in the LangGraph workflow.
- [x] Preserve the current `/chat` response shape: `question`, `answer`, `provider`, `citations`, and `retrievedContext`.
- [x] Require grounded answers that only use retrieved context and retain citation numbering.
- [x] Keep the deterministic answer formatter as a fallback when Claude is unavailable.

### 10. Styling and Responsiveness

- [x] Add chat panel CSS to `frontend/src/styles.css`.
- [x] Check desktop layout with cart and chat interactions.
- [x] Check mobile layout so the panel fits within the viewport.
- [x] Ensure long answers, long source paths, and long product names wrap correctly.
- [x] Keep cards/panels at 8px border radius to match the existing design.

### 11. Verification

- [x] Run `npm run build`.
- [x] Start or verify the backend API.
- [x] Start or verify the Vite frontend.
- [x] Test a return-policy question.
- [x] Test a product setup question.
- [x] Test a vague clarification question, such as `Help`.
- [x] Test an escalation question, such as `Where is my order?`.
- [x] Test an unsupported-category question, such as `What is the return policy for opened clothes?`.
- [x] Confirm citations render only when returned by the backend.
- [x] Confirm catalog availability questions such as `Is IBM Laptop available?` are answered from catalog data instead of generic clarification.

## Planned Backend Enhancements

- [x] Add a catalog availability intent for questions such as `Is IBM Laptop available?`, `Do you have HP laptops?`, or `Is this product in stock?`.
- [ ] Add a catalog-ranking intent for questions such as `List top 5 products with highest reviews`, `What are the most reviewed products?`, `Show highest rated products`, `Top 5 cheapest products`, and `Most expensive cameras`.
- [ ] Answer catalog-ranking questions from `data/catalog/products.json` using deterministic sorting by `reviewCount`, `rating`, or `price` instead of routing them through RAG review-summary clarification.
- [ ] Keep catalog-ranking answers separate from customer review summarization, which should remain product-specific.

## Completion Summary

- Added a floating support panel available from catalog and product detail pages.
- Connected the frontend to `POST /chat` with the Nebius retrieval provider.
- Added customer-friendly answer rendering, starter prompts, loading state, error state, and draft preservation.
- Added product-aware starter prompts on product detail pages.
- Hid citations, retrieved context, and developer traces from normal support mode.
- Added eval/developer mode at `?eval=z`, enabled by default when unlocked, for citations, retrieved context, and debug traces.
- Added catalog availability handling for questions such as `Is IBM Laptop available?`.
- Verified with `npm run build` and `uv run python ../rag_pipeline/validate_support_agent.py`.

Phase 9 should start from ticket persistence, support handoff storage, and the remaining catalog-ranking enhancement.
