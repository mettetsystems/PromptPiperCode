# Shared packages (`packages/`)

TypeScript libraries consumed by the web app (and potentially other clients).

| Package | README | Purpose |
|---------|--------|---------|
| [`shared/`](shared/README.md) | Cross-app types — health response shapes, shared constants |

Add new packages here when multiple frontends or tools need the same types without importing from `apps/web`.
