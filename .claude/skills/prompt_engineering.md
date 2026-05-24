# Skill — Prompt Engineering

## When to load

- Authoring a new agent's prompts
- Tightening an existing prompt
- Debugging "model ignores instructions" issues

## Mental model

All prompts live in `app/prompts/registry.py` as `PromptTemplate(id, version, system, user_template)`.
Agents render `user_template.format(...)` and pass `system` separately to the LLM.

## Key files

| File | Role |
|---|---|
| `app/prompts/registry.py` | All templates (single source of truth) |
| `app/agents/*.py` | Consume prompts via `get_prompt(<id>)` |

## Authoring checklist

When writing or revising a prompt:

- [ ] Clear role assignment in the system message ("You are a senior reliability engineer…")
- [ ] Explicit OUTPUT FORMAT (JSON schema, citation style, etc.)
- [ ] Explicit boundaries ("Answer ONLY from the supplied context", "Never invent…")
- [ ] Conservative bias ("prefer 'inconclusive' over speculation")
- [ ] Concrete example if behavior is non-obvious
- [ ] Token budget realistic for the configured `max_tokens`
- [ ] Versioned (`version="YYYY.MM.N"`) and committed to `CHANGELOG.md`

## Standard tasks

### 1. Add a new prompt

```python
# app/prompts/registry.py
"forecast": PromptTemplate(
    id="forecast",
    version="2025.05.1",
    system="You are a forecasting analyst. Return JSON only.",
    user_template="Component: {component}\nHistory: {history}\n\nReturn {{...}}",
),
```

Reference it via `get_prompt("forecast").render(...)`.

### 2. Update a prompt

- BUMP the version (`2025.05.1` → `2025.05.2`)
- Add `CHANGELOG.md` entry
- Run `pytest -m evaluation` to confirm no quality regression
- If output schema changed, update the parser in the consuming agent

### 3. Force structured output

Two options:

1. **Tolerant parsing** (current default): instruct "Return JSON". Use the
   `_parse_*` helpers in agents that strip code fences and fall back gracefully.
2. **Provider-native structured outputs** (preferred when available):
   ```python
   response = await client.chat.completions.create(
       model=...,
       response_format={"type": "json_schema", "json_schema": {...}},
   )
   ```
   Gate behind `FEATURE_STRUCTURED_OUTPUTS` for cross-provider compatibility.

## Pitfalls

- Don't put dynamic values in the `system` message — keep it stable for caching.
- Don't exceed ~3 KB system prompts — concise > exhaustive.
- Don't ask for "creative" output in RAG settings; lower temperature.
- Don't rely on chain-of-thought monologue in production — request final answer only.

## Versioning convention

`YYYY.MM.N` — year.month.iteration (e.g. `2026.05.1`). Bump `N` per change.
