# Registry Format

The prompt registry in `data/registry` is a **Git-backed, file-based store** for finalized and in-progress prompt definitions.

This scaffold establishes the directory only. The format below is the intended contract for upcoming implementation.

## Goals

- Human-readable files suitable for diff and review
- Stable identifiers and semantic versioning
- Local-first operation with optional remote Git remotes chosen by the user

## Planned layout

```
data/registry/
  prompts/
    {prompt_id}/
      manifest.yaml      # metadata, tags, status
      versions/
        v1/
          prompt.md      # canonical prompt body
          notes.md       # optional design notes
        v2/
          prompt.md
  schemas/
    manifest.schema.json
```

## `manifest.yaml` (planned)

```yaml
id: clarify-customer-email
title: Clarify customer email
status: draft            # draft | finalized | archived
tags:
  - support
  - clarification
created_at: 2026-06-15T12:00:00Z
updated_at: 2026-06-15T12:00:00Z
latest_version: v1
```

## Version rules (planned)

- Versions are immutable once finalized.
- Draft versions may be edited in place until marked finalized.
- Git commits provide audit history; Prompt Piper APIs will mirror Git operations.

## Identifiers

- `prompt_id`: lowercase kebab-case slug (`clarify-customer-email`)
- Version directories: `v1`, `v2`, … or semver if needed later

## Git usage

The registry is intended to be its own Git repository:

```bash
cd data/registry
git init
git add .
git commit -m "Initialize prompt registry"
```

Users may add remotes (GitHub, GitLab, self-hosted) on their own terms. Prompt Piper does not require a hosted remote.

## Relationship to artifacts

Finalized prompts may generate exports in `data/artifacts/{prompt_id}/{version}/` as TXT, Markdown, HTML, PDF, or bibliography files. Registry files remain the source of truth; artifacts are derived outputs.
