# Documentation (`docs/`)

Design and operator guides. The [root README](../README.md) is the quick-start; these go deeper.

| Document | Audience | Contents |
|----------|----------|----------|
| [architecture.md](architecture.md) | Developers | System boundaries, data flow, quality gate |
| [user-workflow.md](user-workflow.md) | Users / integrators | Step-by-step session API and UI flow |
| [developer-guide.md](developer-guide.md) | Contributors | Repo conventions, testing, adding routes |
| [local-setup.md](local-setup.md) | Fedora operators | Native vs Podman setup detail |
| [privacy-model.md](privacy-model.md) | Security review | What stays local, external inference gate |
| [registry-format.md](registry-format.md) | Integrators | `metadata.yaml`, artifact layout, git layout |

Folder-level READMEs under `apps/`, `data/`, etc. describe **where code and runtime files live**; these docs describe **how the product behaves**.
