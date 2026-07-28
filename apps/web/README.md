# Web app (`apps/web/`)

React 18 + TypeScript + Vite single-page app for the **PromptPiperCode** coding-prompt workflow UI (six dimensions, clarify → export).


## Structure

| Path | README | Purpose |
|------|--------|---------|
| `src/` | [src/README.md](src/README.md) | Application source |
| `vite.config.ts` | — | Dev server, API proxy, SPA routing for `/sessions/:id/*` (including `precision`) |
| `package.json` | — | `@prompt-piper/web` scripts and dependencies |

## Run

```bash
# From repo root — proxies /sessions, /registry, /health to :8000
make dev-web
```

Open http://127.0.0.1:5173. Production build is baked into `infra/Containerfile.web` (nginx).

## Test

```bash
npm test --prefix apps/web
# or: make test-web
```
