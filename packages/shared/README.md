# `@prompt-piper/shared`

Minimal shared TypeScript types published as a local workspace package.

| File | Role |
|------|------|
| `src/index.ts` | Exported types (e.g. `HealthResponse`, `LlmHealthResponse`) |
| `package.json` | Package name and build config |
| `tsconfig.json` | TypeScript project settings |

Imported by `apps/web` for health checks and API typing alignment. Session-specific DTOs live in `apps/web/src/api/types.ts`; extend this package when types are shared across multiple frontends.
