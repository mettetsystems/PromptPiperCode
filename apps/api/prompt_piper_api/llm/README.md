# LLM adapters (`llm/`)

OpenAI-compatible client abstraction for optional local or remote models.

| Module | Role |
|--------|------|
| `base.py` | `LLMClient` protocol |
| `factory.py` | `create_llm_client_from_env()` — picks mock, fallback, or local OpenAI |
| `local_openai.py` | Chat/completions against `PROMPT_PIPER_LOCAL_BASE_URL` |
| `fallback.py` | Rule-based responses when no model is configured |
| `mock.py` | Deterministic test double |
| `settings.py` | Model name and endpoint helpers |
| `enums.py` | Provider/model enums |

Clarification **ranking** stays CPU-fast by default; LLM is used for draft generation, edit patches, on-demand **Get model suggestions**, **precision refinement** suggestions, and optional **Send to model** on the Complete page when configured.
