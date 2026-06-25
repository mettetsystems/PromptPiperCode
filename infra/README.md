# Infrastructure (`infra/`)

Container images, compose manifests, and database bootstrap for Podman deployments.

| File | Purpose |
|------|---------|
| `Containerfile.api` | Python API image — pandoc/weasyprint for export |
| `Containerfile.web` | nginx + static Vite build |
| `podman-compose.yml` | Full stack — web, api, postgres, optional llama profile |
| `compose.yaml` | Postgres-only compose for native API + container DB |
| `nginx.conf` | SPA fallback and static asset rules for web container |
| `init-db.sql` | Enable `vector` extension on first Postgres start |
| `env.podman.example` | Container-oriented env overrides |

| Directory | Purpose |
|-----------|---------|
| [`quadlets/`](quadlets/README.md) | systemd Quadlet units for boot-time Podman |

## Common commands

```bash
# Build and start full stack
podman compose -f infra/podman-compose.yml up --build

# Build images manually
podman build -f infra/Containerfile.api -t prompt-piper-api .
podman build -f infra/Containerfile.web -t prompt-piper-web .
```

Helper scripts in [`scripts/`](../scripts/README.md) wrap these for daily dev.
