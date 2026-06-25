# Runtime data (`data/`)

Local-only storage created at dev/runtime. **Do not commit session exports or registry commits** unless you intend to share fixtures — most subfolders are gitignored or contain user data.

| Directory | Purpose | Env variable |
|-----------|---------|--------------|
| `sessions/` | JSON files — one per in-progress or completed session | `SESSIONS_PATH` (default `./data/sessions`) |
| `registry/` | Git repo of finalized canonical prompts (`metadata.yaml`, bodies) | `REGISTRY_PATH` / `PROMPT_PIPER_REGISTRY_ROOT` |
| `artifacts/` | Timestamped export bundles per prompt | `ARTIFACTS_PATH` / `PROMPT_PIPER_ARTIFACT_ROOT` |
| `audit/` | Append-only audit logs (`events.jsonl`, `external_inference.jsonl`) | `AUDIT_LOG_PATH` |
| `model-cache/` | Downloaded embedding models (Hugging Face) | `PROMPT_PIPER_MODEL_CACHE`, `HF_HOME` |
| `postgres/` | PostgreSQL data files (Podman bind mount) | `DATABASE_URL` in compose |
| `models/` | Local GGUF cache / HF hub cache (wizard downloads) | Wizard + `ensure_llm` |
| `demo/` | Isolated registry/artifacts for `make demo` | Set in demo tests |
| `lexicon/` | Glossary overlay + generated precision vector index | `prompt_terms.yaml`, `LEXICON_VECTOR_INDEX_PATH` |
| `test-export/` | Pytest temporary export roots | `conftest.py` monkeypatch |

Production-style exports on Fedora often use `~/Documents/PromptPiper/` instead of `data/artifacts` — see root README. Each export folder may include `inference_response.txt` after **Send to model** on the Complete page.

```bash
# Ensure session directory exists (git keeps .gitkeep only)
mkdir -p data/sessions
```
