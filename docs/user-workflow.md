# User workflow

This document describes the end-to-end prompt design flow implemented by `SessionService` and exposed through the web UI and REST API.

## Overview

```
New session → clarification loop (up to 10 questions) → initial draft → edits → finalize
  → similarity check → optimize → approve → generate artifacts
  → (optional) send to external inference
```

Each step maps to a session state. Invalid actions return HTTP 409 with the current state and attempted action.

## 1. New session

**UI:** Dashboard → New Session  
**API:** `POST /sessions`

Provide:

- `initial_request` — free-text description of what the prompt should do.
- `title` (optional) — defaults to a truncated objective.

The system extracts a RequirementCard from the request and enters `clarifying`. The response includes the first clarification question, target field name, and quick-reply options (always ending with `unspecified`).

Example:

```json
{
  "initial_request": "I need a prompt that helps an internal AI tool generate implementation reports for new features.",
  "title": "Implementation report prompt"
}
```

## 2. Clarification loop

**UI:** Clarification page (`/sessions/{id}/clarify`)  
**API:** `POST /sessions/{id}/answer` with `{ "answer": "..." }`  
**Early finish:** `POST /sessions/{id}/clarify/complete` when remaining gaps are explicitly `unspecified`

The ranker asks about missing RequirementCard fields by priority (`ClarificationQuestionRanker`), up to **10** questions. The loop ends when:

1. All requirement fields have values, or
2. Remaining gaps are marked `unspecified` and the user chooses **Generate draft now**, or
3. The question cap is reached (draft is generated automatically).

Answers may be quick-reply strings or free text. Answering `unspecified`, `skip`, or `unknown` keeps the field unresolved; the draft will mark it `unspecified` rather than inventing a value.

Typical sequence for an implementation-report prompt:

| Turn | Field | Example answer |
|------|-------|----------------|
| 1 | `audience` | Mixed technical and business audience. |
| 2 | `desired_output_shape` | Report with sections and risks. |
| … | … | Additional fields or `unspecified` |

## 3. Initial draft

Created automatically after the second clarification answer. No separate API call.

The draft is plain text with labeled sections:

- Mission
- Context (audience, input materials, language, optimization targets)
- Constraints
- Style
- Output contract
- Acceptance criteria
- Forbidden content or actions (when applicable)

Missing fields appear as `unspecified`. The response includes `draft.body`, `draft.version` (starts at 1), and updated `requirement_card`.

Implementation-report prompts additionally include section headings for Proposed feature, Architecture, Delivery plan, Key risks, and Mitigations in the output contract.

## 4. Iterative edits

**UI:** Draft Editor (`/sessions/{id}/edit`)  
**API:** `POST /sessions/{id}/edit` with `{ "instruction": "..." }`

Available only in `edit` state. Each edit:

1. Classifies intent (`DraftPatchService` — e.g. `ADD_CONSTRAINT`, `CHANGE_TONE`, `CHANGE_OUTPUT_SHAPE`).
2. Updates the RequirementCard.
3. Regenerates the full draft body.
4. Creates a new draft version (`version` increments; prior versions retained).

Example instructions:

```
Add constraint: prefer open-source alternatives and change tone to analytical
Change output shape to report with one Mermaid diagram and a short API section
```

The response includes `revised_draft`, `semantic_diff`, `change_summary`, and `edit_intent`.

Edits are rejected after finalization (canonical draft is frozen).

## 5. Finalization

**UI:** Triggered from the edit flow before similarity  
**API:** `POST /sessions/{id}/finalize`

Available only from `edit` state. Finalization:

1. Marks the current draft as canonical and frozen.
2. Assigns `prompt_id`.
3. Writes registry files under `data/registry/{prompt_id}/`.
4. Runs similarity check and indexes the prompt (when similarity service is configured).
5. Sets state to `similarity_check`.

Response fields: `prompt_id`, `registry_warning`, `similarity_result`, `similarity_matches`, `similarity_warning`.

## 6. Similarity check

Similarity runs as part of finalize—there is no separate endpoint. Review results on the Similarity page (`/sessions/{id}/similarity`).

The UI/API expose:

- **Matches** — prior prompts ranked by hybrid retrieval score.
- **Warning** — shown when any match ≥ threshold (default 90%); message defined in `SIMILARITY_WARNING_MESSAGE`.

Similarity does not block progression. It informs reuse and duplication risk before optimization.

## 7. Optimization

**UI:** Optimization page (`/sessions/{id}/optimize`)  
**API:** `POST /sessions/{id}/optimize`

Requires `similarity_check` state. Runs the five-pass `TokenOptimizationEngine` on the canonical body. Returns:

- `optimization_result.optimized_body`
- `optimization_result.metrics` (token counts, five target scores)
- `pre_inference_metrics` (quality gate inputs)
- `optimization_result.hard_conflicts` (must be empty before approval)

State becomes `optimization`.

## 8. Approve optimization

**UI:** Approve button on Optimization page  
**API:** `POST /sessions/{id}/optimize/approve`

Runs the pre-inference quality gate on the optimized body. On failure, returns HTTP 409 with gate failure reasons (e.g. low requirement capture, unspecified field honesty, hard conflicts).

On success, state becomes `approval` and `quality_gate_passed` is true.

## 9. Artifact generation

**UI:** Export page (`/sessions/{id}/export`)  
**API:** `POST /sessions/{id}/artifacts` with optional `{ "include_pdf": true }`

Requires `approval` state. Writes to `data/artifacts/{prompt_id}/`:

| File | Required |
|------|----------|
| `canonical_prompt.txt` / `.md` | Yes |
| `optimized_prompt.txt` / `.md` | Yes |
| `metadata.yaml` | Yes |
| `requirement_card.json` | Yes |
| `metrics.json` | Yes |
| `similarity_report.json` | Yes |
| `lessons_learned.md` | Yes |
| `artifact_manifest.json` | Yes |
| `optimized_prompt.html` | Optional (Pandoc or built-in fallback) |
| `optimized_prompt.pdf` | Optional (WeasyPrint + Pandoc) |

Registry `metadata.yaml` is updated with artifact paths and evaluation scores. State becomes `exported`.

## 10. Optional external inference

**API:** `POST /sessions/{id}/send-to-inference`

```json
{ "explicit_approval": true }
```

Only after optimization approval. Disabled by default (`PROMPT_PIPER_EXTERNAL_ENABLED=false`).

When enabled and approved:

1. Sends `optimization_result.optimized_body` to the configured external OpenAI-compatible provider.
2. Writes `inference_response.txt` under the artifact directory.
3. Appends an audit event to `data/audit/external_inference.jsonl`.

Blocked attempts are also audited with `outcome: blocked` and a `block_reason`.

There is no UI requirement to use this step; local artifact export is the primary deliverable.

## Registry browsing

After finalization, prompts appear in the Registry UI (`/registry`, `/registry/{promptId}`) via:

- `GET /registry/prompts`
- `GET /registry/prompts/{prompt_id}`
- `GET /registry/prompts/{prompt_id}/files/{filename}`

## Demo flow

Run the bundled implementation-report scenario:

```bash
make demo
```

Prints session ID, prompt ID, registry path, and generated artifact paths under `data/demo/`.

Scenario definition: `demo/implementation_report.yaml`. E2E test: `tests/test_demo_flow.py`.

## API quick reference

| Step | Method | Path |
|------|--------|------|
| Create | POST | `/sessions` |
| Get session | GET | `/sessions/{id}` |
| Answer clarification | POST | `/sessions/{id}/answer` |
| Edit draft | POST | `/sessions/{id}/edit` |
| Finalize | POST | `/sessions/{id}/finalize` |
| Optimize | POST | `/sessions/{id}/optimize` |
| Approve optimization | POST | `/sessions/{id}/optimize/approve` |
| Generate artifacts | POST | `/sessions/{id}/artifacts` |
| External inference | POST | `/sessions/{id}/send-to-inference` |
| Inference settings | GET | `/settings/inference` |
