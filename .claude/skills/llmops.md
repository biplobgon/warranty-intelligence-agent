# Skill — LLMOps

> Lifecycle management for prompts, models, evaluations, and rollouts.

## When to load

- Bumping a prompt version
- Swapping LLM providers / models
- Setting up online evaluation sampling
- Designing canary / shadow deployments

## Pillars

1. **Prompt lifecycle** — `app/prompts/registry.py` is the single source of truth.
2. **Provider lifecycle** — `app/services/llm_provider.py` ABC; swap via `LLM_PROVIDER` env.
3. **Evaluation lifecycle** — deterministic (always-on) + periodic (CI / nightly).
4. **Cost lifecycle** — track tokens via `warranty_llm_token_usage_total`; cache via `InferenceEngine.complete(cache=True)`.
5. **Release lifecycle** — Helm versioned + image tags pinned to commit SHA.

## Standard tasks

### 1. Update a prompt (correctly)

```python
# app/prompts/registry.py
"root_cause": PromptTemplate(
    id="root_cause",
    version="2025.05.2",   # ← BUMP THIS
    system="...new wording...",
    user_template="..."
),
```

Then:
- Add a `CHANGELOG.md` entry
- If JSON output schema changed, update `_parse_*` parser
- Run `pytest -m evaluation` to confirm no regression

### 2. Add a model / provider

```python
# app/services/llm_provider.py
class BedrockProvider(LLMProvider):
    name = "bedrock"
    ...

# Wire in get_llm_provider()
if settings.llm_provider == "bedrock":
    _provider_cache = BedrockProvider(settings)
```

Add `BEDROCK_*` fields to `Settings`. Update `.env.example`.

### 3. Add cost guardrails

```python
# app/inference/engine.py — extend with budget checks
if settings.daily_token_budget and tokens_used_today >= settings.daily_token_budget:
    raise BudgetExceededError(...)
```

Emit `warranty_llm_budget_exceeded_total` counter.

### 4. Shadow / canary

In Helm `values.yaml`:
```yaml
canary:
  enabled: true
  weight: 10           # 10% traffic
  image: { tag: sha-NEW }
```

Use an Argo Rollouts manifest or NGINX `nginx.ingress.kubernetes.io/canary` annotations.

### 5. Online evaluation sampling

In `app/api/routes/query.py`, after the graph runs:

```python
if random.random() < settings.online_eval_sample_rate:
    asyncio.create_task(_sample_to_mlflow(state))
```

NEVER block the response on online eval.

## Hard rules

- Prompt change = version bump (auditability).
- Provider swap = config change, not code change.
- All token usage flows through `LLM_TOKEN_USAGE` counter.
- Caching only for deterministic prompts (temperature == 0.0).
