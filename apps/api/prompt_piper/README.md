# `prompt_piper` — CLI and tooling

Python package for developer-facing commands that are not part of the HTTP API.

| Directory | README | Purpose |
|-----------|--------|---------|
| `setup/` | [setup/README.md](setup/README.md) | Interactive `.env` wizard, GPU detection, llama.cpp launcher |
| `demo/` | [demo/README.md](demo/README.md) | End-to-end coding-prompt demo |
| `eval/` | [eval/README.md](eval/README.md) | Pre-inference quality gate regression runner |

## Common commands

```bash
# Interactive setup wizard (CPU-only or local SLM)
make setup

# Probe GPU and start llama-server if configured
make ensure-llm

# Run coding-prompt demo
make demo

# Run regression eval suite (quality gate)
make eval
```
