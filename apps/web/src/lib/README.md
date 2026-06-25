# Libraries (`src/lib/`)

Pure helpers with no React dependencies (except tests may use jsdom).

| Module | Role |
|--------|------|
| `sessionRouting.ts` | Map `SessionState` ↔ URL steps, `canVisitStep`, `isSessionClosed` |
| `recentSessions.ts` | `localStorage` list for dashboard |
| `clarificationAnswer.ts` | Multi-select answer serialization for clarify API |

Tests: `sessionRouting.test.ts`, `clarificationAnswer.test.ts`, `recentSessions.test.ts`.
