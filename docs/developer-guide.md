# Developer guide

## Repo structure

```
PromptPiper/
├── apps/
│   ├── api/
│   │   ├── prompt_piper_api/     # FastAPI application package
│   │   │   ├── domain/           # Pydantic models (session, draft, registry, metrics)
│   │   │   ├── routes/           # HTTP routers
│   │   │   ├── services/         # Business logic
│   │   │   ├── llm/              # Local/external OpenAI-compatible clients
│   │   │   ├── db/               # SQLModel tables (similarity index)
│   │   │   └── schemas/          # Request/response DTOs
│   │   └── prompt_piper/         # CLI modules (demo, eval)
│   └── web/
│       └── src/
│           ├── api/              # HTTP client + TanStack Query hooks
│           ├── pages/            # Route-level workflow pages
│           └── components/       # Shared UI (layout, RequirementCard panel)
├── packages/shared/              # Shared TS types (future OpenAPI codegen)
├── demo/                         # Demo scenario YAML
├── data/                         # Runtime data (gitignored except .gitkeep)
├── infra/                        # Podman Containerfiles, compose, nginx
├── tests/                        # pytest suite + eval regression cases
└── docs/
```

Python package install: `cd apps/api && pip install -e ".[dev]"` (or `make install-api`).

## Backend services

| Service | Module | Responsibility |
|---------|--------|----------------|
| `SessionService` | `services/session_service.py` | State machine orchestration |
| `RequirementCardExtractor` | `services/requirement_card_extractor.py` | Parse initial request and clarification answers |
| `ClarificationQuestionRanker` | `services/clarification_question_ranker.py` | Rank and format clarification questions |
| `DraftGenerator` | `services/draft_generator.py` | Build plain-text draft from RequirementCard |
| `DraftPatchService` | `services/draft_patch_service.py` | Apply edit instructions to card + body |
| `GitRegistryService` | `services/git_registry_service.py` | Write/list registry files; Git commits |
| `SimilarityCheckService` | `services/similarity_check_service.py` | Embed, retrieve, index on finalize |
| `HybridRetrievalService` | `services/hybrid_retrieval_service.py` | Lexical + vector retrieval with MMR |
| `EmbeddingService` | `services/embedding_service.py` | Local sentence-transformers or hash fallback |
| `TokenOptimizationEngine` | `services/optimization/engine.py` | Five-pass token optimizer |
| `QualityGateService` | `services/quality_gate_service.py` | Pre-inference approval gate |
| `PreInferenceMetricsService` | `services/pre_inference_metrics_service.py` | Deterministic quality metrics |
| `ArtifactService` | `services/artifact_service.py` | Export TXT/MD/HTML/PDF + manifest |
| `ExternalInferenceService` | `services/external_inference_service.py` | Gated external model dispatch |
| `AuditLogService` | `services/audit_log_service.py` | Append-only JSONL audit log |

Dependency wiring for production API: `routes/sessions.py` → `get_session_service()`.

For tests and demo, construct `SessionService` manually with explicit dependencies (see `prompt_piper/demo/runner.py`).

## Frontend structure

React 18 + Vite + TypeScript. Routing in `apps/web/src/App.tsx`:

| Route | Page | Workflow step |
|-------|------|---------------|
| `/` | Dashboard | Recent sessions |
| `/sessions/new` | NewSessionPage | Create session |
| `/sessions/:id/clarify` | ClarificationPage | Answer questions |
| `/sessions/:id/edit` | DraftEditorPage | Edit draft |
| `/sessions/:id/similarity` | SimilarityCheckPage | Review matches |
| `/sessions/:id/optimize` | OptimizationPage | Optimize + approve |
| `/sessions/:id/export` | ExportPage | Generate artifacts |
| `/sessions/:id/complete` | Completion summary | Done |
| `/registry` | RegistryPage | Browse finalized prompts |

`SessionWorkflowPage` redirects `/sessions/:id` to the correct step based on `session.state`.

API layer: `apps/web/src/api/` — typed HTTP client, TanStack Query hooks (`useSession`, `useCreateSession`, etc.), shared types aligned with backend schemas.

Run dev server: `make dev-web` (proxies to `VITE_API_BASE_URL`).

Frontend tests: Vitest in `apps/web/src/**/*.test.ts(x)`.

## Tests

Backend tests live in `tests/` at repo root (configured via root `pyproject.toml`).

```bash
make test          # all pytest tests
make lint          # ruff on backend + tests
make typecheck     # mypy on prompt_piper_api + prompt_piper
make eval          # pre-inference quality gate regression suite
make demo          # implementation-report E2E demo CLI
```

Key test modules:

| File | Coverage |
|------|----------|
| `test_session_state_machine.py` | State transitions, finalize guards |
| `test_clarification_loop.py` | Two-question loop, unspecified handling |
| `test_draft_generator.py` | Plain-text contract, no hallucination |
| `test_draft_edit.py` | Edit intents, version increments |
| `test_token_optimizer.py` | Optimizer passes, approval blocking |
| `test_quality_gate.py` | Metrics thresholds, regression eval |
| `test_similarity_search.py` | Embedding fallback, finalize indexing |
| `test_registry_finalize.py` | Registry file layout, Git warnings |
| `test_artifacts.py` | Artifact generation, manifest |
| `test_external_inference.py` | Privacy gates, audit log |
| `test_demo_flow.py` | Full workflow E2E |
| `integration/test_api_startup.py` | Health, uvicorn import |

Use `tmp_path` fixtures for isolated registry/artifact directories. Similarity tests use `EmbeddingService(prefer_fallback=True)`.

Regression cases: `tests/evals/regression_cases.yaml` — consumed by `prompt_piper.eval`.

## Local model config

Prompt Piper uses an **OpenAI-compatible HTTP API** for optional LLM-assisted clarification, extraction, and draft generation.

Environment variables (`.env`):

```env
PROMPT_PIPER_LLM_ENABLED=true
PROMPT_PIPER_LOCAL_BASE_URL=http://127.0.0.1:8080/v1
PROMPT_PIPER_LOCAL_CHAT_MODEL=llama
PROMPT_PIPER_LOCAL_EMBED_MODEL=llama
# PROMPT_PIPER_LOCAL_API_KEY=optional
PROMPT_PIPER_MODEL_PROFILE=compatibility   # temperature/max_tokens preset
```

Client factory: `llm/factory.py` → `create_llm_client_from_env()`.

When the local server is unreachable or `PROMPT_PIPER_LLM_ENABLED=false`, services use **deterministic fallbacks** via `llm/fallback.with_llm_fallback()`.

Embeddings for similarity (separate from chat LLM):

```env
PROMPT_PIPER_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
PROMPT_PIPER_EMBEDDING_FALLBACK=false
SIMILARITY_INDEX_PATH=./data/similarity_index.json
SIMILARITY_WARNING_THRESHOLD=0.90
```

External inference (opt-in only):

```env
PROMPT_PIPER_EXTERNAL_ENABLED=false
PROMPT_PIPER_EXTERNAL_BASE_URL=https://api.openai.com/v1
PROMPT_PIPER_EXTERNAL_CHAT_MODEL=gpt-4o-mini
PROMPT_PIPER_EXTERNAL_API_KEY=sk-...
REQUIRE_APPROVAL_BEFORE_EXTERNAL_CALL=true   # cannot be set false
```

## Adding new optimization metrics

Optimization produces two metric layers:

1. **`OptimizationMetrics`** — token counts and five target scores inside `OptimizationResult.metrics` (`services/optimization/metrics.py`).
2. **`PreInferenceMetrics`** — quality gate inputs (`domain/pre_inference_metrics.py`).

### Add an optimization target score

1. Add field to `OptimizationTargets` in `domain/requirement_card.py` if it is user-specified, or extend `OptimizationTargetMetrics` in `domain/optimization.py`.
2. Implement scoring in `OptimizationMetricsCalculator.compute()` (`services/optimization/metrics.py`).
3. Surface in `ApprovalExportPass.run()` if it should appear in the change log.
4. Map into `evaluation_scores` in `SessionService.generate_artifacts()` if it should persist to `metadata.yaml`.
5. Add tests in `tests/test_token_optimizer.py`.

### Add a pre-inference gate metric

1. Add field to `PreInferenceMetrics` (`domain/pre_inference_metrics.py`).
2. Implement computation in `PreInferenceMetricsService.compute()`.
3. Add threshold check in `QualityGateService.evaluate()`.
4. Persist via `ArtifactService` → `metrics.json` and registry update path.
5. Add unit tests in `tests/test_quality_gate.py` and optionally a regression case in `tests/evals/regression_cases.yaml`.

Keep metrics **deterministic**—no model calls inside the gate.

## Adding new artifact types

Core artifact list: `_CORE_ARTIFACTS` in `services/artifact_service.py`.

To add a format:

1. Implement a generator method on `ArtifactService` (e.g. `generate_bibtex()`).
2. Register the filename and format in `_CORE_ARTIFACTS` or treat as optional (like HTML/PDF).
3. Add path key to `_ARTIFACT_PATH_KEYS` for registry linking.
4. Invoke from `ArtifactService.generate()` and append to `ArtifactManifest.files`.
5. Update `GitRegistryService.update_artifact_paths()` consumers if metadata keys change.
6. Add tests in `tests/test_artifacts.py`.
7. Document in [registry-format.md](registry-format.md).

Optional formats should set `optional: true` in the manifest and append human-readable warnings when dependencies (Pandoc, WeasyPrint) are missing—do not fail the whole export.

## Running the API locally

```bash
make dev-api
# uvicorn prompt_piper_api.main:app --reload
```

OpenAPI docs: http://127.0.0.1:8000/docs

## Code conventions

- Pydantic v2 models in `domain/`; no ORM on session state (in-memory `SessionRecord` dict for v1).
- Services raise `StateTransitionError` for invalid workflow actions; routes map to HTTP 409.
- Draft bodies are **plain text** with underline-style section headers, not Markdown headings (format checker enforces this).
- Use `UNSPECIFIED = "unspecified"` constant from `draft_generator.py` for missing fields.
- Ruff + mypy enforced via Makefile; match existing import and naming patterns.
