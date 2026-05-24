# Skill — Docker Deployment

## When to load

- Building / debugging the API container
- Adding a new service to docker-compose
- Optimizing image size or startup time

## Mental model

Multi-stage: `builder` compiles wheels, `runtime` is slim, non-root, read-only FS,
tini as PID 1, gunicorn+uvicorn workers, baked healthcheck.

## Key files

| File | Role |
|---|---|
| `Dockerfile` | Multi-stage API image |
| `docker-compose.yml` | Full local stack |
| `.dockerignore` | Build context exclusions |

## Standard tasks

### 1. Add a service to compose

```yaml
my-svc:
  image: my/svc:tag
  container_name: warranty-my-svc
  networks: [warranty-net]
  ports: ["1234:1234"]
  depends_on: [redis]
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:1234/health"]
    interval: 30s
    retries: 3
```

Add to `networks: [warranty-net]` (single shared network).

### 2. Rebuild after changes

```bash
make docker-build
make docker-up    # build via compose
docker logs -f warranty-api
```

### 3. Slim the image further

- Remove unused libs (`build-essential` is already builder-only)
- Use `--no-deps` for wheel install in runtime layer
- Consider `python:3.11-alpine` only if no native wheels are needed (often the case for `pinecone-client`, `numpy`)

### 4. Add a runtime sidecar

Use Kubernetes `Pod.spec.containers` (not compose) — the API container should stay
single-process. Pattern: log forwarder, OTel sidecar, secret-fetcher.

## Hard rules

- Non-root user (`app:app`), read-only FS, dropped caps — already set in `Dockerfile`.
- HEALTHCHECK must hit `/health` (NOT `/health/ready` — readiness depends on deps).
- Don't bake secrets into images. Mount via env or secret store.
- Update `.dockerignore` if you add a new large dir to the repo.

## Debugging

```bash
docker compose ps
docker logs warranty-api
docker exec -it warranty-api sh   # if image has /bin/sh
docker compose down -v             # nuke volumes
```
