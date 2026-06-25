# API client (`src/api/`)

Browser ↔ FastAPI integration. In dev, requests go to the Vite origin and are proxied to port 8000.

| Module | Role |
|--------|------|
| `http.ts` | `apiFetch`, `ApiError`, `formatApiError` |
| `sessions.ts` | Session CRUD, workflow POST helpers, precision review, send-to-inference |
| `hooks.ts` | TanStack Query hooks (`useSession`, `useEditDraft`, `useSendToInference`, …) |
| `types.ts` | TypeScript mirrors of `SessionDetailResponse`, precision and inference DTOs |
| `client.ts` | Shared fetch configuration |

Workflow mutations invalidate `queryKeys.session(id)` and update recent-session local storage on success.
