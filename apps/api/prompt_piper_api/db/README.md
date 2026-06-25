# Database (`db/`)

SQLAlchemy setup for PostgreSQL (Podman stack). Native dev often uses SQLite via `DATABASE_URL` in `.env`.

| Module | Role |
|--------|------|
| `session.py` | Engine, session factory, `init_db()` |
| `similarity_models.py` | pgvector tables for hybrid retrieval index |

Schema bootstrap SQL for containers: [`infra/init-db.sql`](../../../../infra/init-db.sql). Application init is triggered by [`scripts/init-db.sh`](../../../../scripts/init-db.sh).

Session workflow state is stored in JSON files (`SESSIONS_PATH`), not Postgres — DB is for similarity vectors and future multi-user features.
