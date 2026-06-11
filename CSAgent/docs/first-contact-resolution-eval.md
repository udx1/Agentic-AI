# First-Contact Resolution Eval Dataset

## Goal

Use `data/support/support_eval_queries.json` to test the support bot with 20 real-world-style customer queries and calculate first-contact resolution rate.

## Dataset Fields

- `id`: Stable eval case ID.
- `question`: Customer-style support query.
- `category`: Human-readable scenario category.
- `expectedIntent`: Expected support-agent intent.
- `expectedOutcome`: One of `resolved`, `escalated`, or `clarification`.
- `expectedFirstContactResolved`: Whether this query should count as resolved on first contact.
- `expectedEvidenceType`: Expected retrieved document type for resolvable questions, when applicable.
- `expectedTicketIssueType`: Expected ticket type for handoff questions, when applicable.
- `expectedTicketPriority`: Expected ticket priority for handoff questions, when applicable.
- `productId`: Optional product target.
- `notes`: Why the case exists.

## Measurement Plan

First-contact resolution rate should be calculated as:

```text
resolved_on_first_contact / total_queries
```

A query counts as resolved on first contact when:

- The agent does not ask for clarification.
- The agent does not escalate or offer handoff.
- The answer is grounded in retrieved/catalog context.
- The response matches the expected outcome for the eval case.

Escalation and clarification are correct behaviors for some cases, but they should not count as first-contact resolution.

## Current Dataset Mix

- 11 expected first-contact resolutions.
- 7 expected escalations.
- 2 expected clarifications, including one unsupported-category clarification.

This intentionally mixes answerable questions with questions that should avoid hallucination and move to clarification or human handoff.
