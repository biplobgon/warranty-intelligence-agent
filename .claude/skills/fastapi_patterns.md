# Skill — FastAPI Patterns

> Playbook for adding routes, schemas, middleware, and dependencies.

## When to load

- Adding a new route
- Tightening request validation
- Adding middleware
- Standardizing error envelopes

## Mental model

```
ingress → middleware (request-ctx, CORS, metrics, OTel) → router → dependency → handler → schema → orjson response
```

## Key files

| File | Role |
|---|---|
| `app/main.py` | App factory, middleware order, exception handlers |
| `app/api/routes/*.py` | One file per route group |
| `app/api/schemas/*.py` | Pydantic v2 request/response schemas |
| `app/api/middleware/request_context.py` | request_id + structlog binding + metrics |
| `app/api/middleware/auth.py` | `require_api_key` dependency |

## Standard tasks

### 1. Add a new route

```python
# app/api/routes/forecast.py
from fastapi import APIRouter, Depends
from app.api.middleware.auth import require_api_key
from app.api.schemas import ForecastRequest, ForecastResponse  # add to schemas

router = APIRouter(tags=["analytics"])

@router.post(
    "/forecast",
    response_model=ForecastResponse,
    dependencies=[Depends(require_api_key)],
    summary="Forecast warranty cost by component",
)
async def forecast(req: ForecastRequest) -> ForecastResponse:
    ...
```

```python
# app/main.py
from app.api.routes import forecast
app.include_router(forecast.router)
```

```python
# tests/integration/test_api_forecast.py
def test_forecast(api_client):
    resp = api_client.post("/forecast", json={...})
    assert resp.status_code == 200
```

### 2. Define schemas (Pydantic v2)

```python
from pydantic import BaseModel, ConfigDict, Field

class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    component: str = Field(..., min_length=1, max_length=120)
    horizon_days: int = Field(30, ge=1, le=365)
```

Always: `extra="forbid"`, explicit bounds, descriptive field names.

### 3. Error responses

Don't hand-roll error bodies. Raise `HTTPException(status_code=..., detail=...)`
or `RequestValidationError`. The global handlers in `app/main.py` wrap them in
`ErrorResponse`. If you need richer context, pass `detail={"error": "...", "reasons": [...]}`.

### 4. Add a dependency

```python
async def get_user_quota(x_user_id: str = Header(...)) -> int:
    return await quota_service.get(x_user_id)

@router.post("/x", dependencies=[Depends(get_user_quota)])
async def handler(...): ...
```

### 5. Add streaming (SSE)

```python
from fastapi.responses import StreamingResponse

async def event_stream(): ...
@router.post("/query/stream")
async def stream(req: QueryRequest):
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

Remember to update ingress/proxy timeouts (already 120 s in `infrastructure/kubernetes/ingress.yaml`).

## Hard rules

- All `/query`-style mutating routes require `require_api_key`.
- All response models are explicit (`response_model=`) — never return raw dicts.
- Use `ORJSONResponse` (already the default).
- No business logic in routes — delegate to agents / services.
- Routes return in < 30 s OR stream; otherwise add a job queue.

## Pitfalls

- Mixing sync code in async handlers — use `loop.run_in_executor`.
- Forgetting to add a route to `app/main.py` after creating the file.
- Schemas inheriting from non-`BaseModel` classes (Pydantic won't validate).
