# Privacy Model

Prompt Piper is designed around **local control** and **explicit consent**.

## Core guarantees (target product behavior)

1. **Local-first storage** — drafts, registry entries, artifacts, and metadata remain on the user's machine unless the user chooses otherwise.
2. **No background external calls** — the application does not send prompt content to external services automatically.
3. **Finalized prompts only** — external model calls are limited to user-approved, finalized prompts.
4. **User-initiated dispatch** — sending a prompt to an external model requires an explicit user action each time.
5. **No SaaS dependency by default** — the scaffold runs entirely with local processes and local files.

## Data locations

| Data            | Location           | Leaves device? |
|-----------------|--------------------|----------------|
| Draft prompts   | Local DB / UI state| No             |
| Registry        | `data/registry`    | No (Git ops are user-controlled) |
| Artifacts       | `data/artifacts`   | No             |
| Final dispatch  | User action only   | Only when user sends |

## External model usage (future)

When external model integration is added, Prompt Piper should:

- Show exactly what text will be sent before dispatch
- Record dispatch metadata locally (timestamp, model id, prompt version)
- Never include unrelated drafts or registry history in the request
- Support fully offline workflows for all non-dispatch features

## Development vs production

The scaffold uses local SQLite/PostgreSQL and a local Vite dev server. No telemetry or third-party analytics are included in the baseline scaffold.

## Threat model notes (scaffold stage)

- Secrets (API keys for external models) should live in local environment files or OS keychains, not in the Git registry.
- The registry should avoid storing third-party credentials.
- Container images should be built from pinned base images when deployed.

This document describes intent and boundaries. Implementation of dispatch auditing and consent UI will come in later product phases.
