# Engineering Standards

> Policy for human and AI contributors to this repository. Concise, mandatory.

## Language & runtime

- Python **3.11+** only. Use modern syntax (`match`, `|` unions, `TypedDict`, `Self`).
- Async-first on I/O. Sync only when wrapped via `loop.run_in_executor`.

## Style & formatting

- **ruff** (lint) + **black** (format) — config in `pyproject.toml`.
- **mypy** non-blocking but should not regress.
- Line length 100. Double quotes. Import grouping per Ruff `I`.

## Typing

- Public functions: type hints required (params + return).
- Prefer `list[str]` / `dict[str, int]` (PEP 585) over `typing.List/Dict`.
- Use `Literal[...]` for enums-as-strings.
- Use `TypedDict` for structured dicts that cross module boundaries.

## Logging

- `structlog` only. Never `print()` in `app/`.
- Get logger via `from app.utils.logging import get_logger; log = get_logger(__name__)`.
- Use key=value, not f-strings, in log messages.

## Errors

- No naked `except:` or bare `except Exception:` without (a) logging
  structurally and (b) either re-raising or returning a typed fallback.
- API errors: raise `HTTPException(...)`; the global handler wraps them.
- Domain errors: define lightweight exception classes in the consuming module.

## Pydantic

- Pydantic **v2** only. `BaseModel`, `ConfigDict`, `model_dump()`, `Field(...)`.
- Use `extra="forbid"` for request schemas.
- Use `SecretStr` for any sensitive field.

## Configuration

- One source of truth: `app/config/settings.py` (`pydantic-settings`).
- New setting ⇒ add an env var, default value, and update `.env.example`.
- Never import `os.environ` directly in `app/` (outside settings).

## Concurrency

- `asyncio.gather` for fan-out; `asyncio.wait_for` for time bounds.
- Bounded concurrency via `Semaphore` when calling rate-limited APIs.
- Singletons (`_settings`, `_llm_provider`, etc.) use module-level caches.

## Dependencies

- New runtime dep ⇒ add to **both** `requirements.txt` and `pyproject.toml`
  (if relevant). Pin to a compatible version range.
- Dev-only deps go under the same files, grouped at the bottom.
- No deps with GPL/AGPL licenses.

## Tests

- Pytest. Marks: `unit`, `integration`, `evaluation`, `slow`.
- New module ⇒ at least one unit test.
- New route ⇒ at least one integration test.
- Tests MUST pass offline (use `fake_llm` fixture from `tests/conftest.py`).
- Don't mock what you can fake (in-memory vector store > MagicMock).

## Documentation

- Update `REPO_STATE.md` for any state change (terse).
- Update `CHANGELOG.md` `[Unreleased]` with a one-liner.
- Public-facing API change ⇒ update `README.md` API table.
- Architecture change ⇒ update `docs/architecture/system_architecture.md`.

## Don't

- Don't introduce a hard dependency without an offline test path.
- Don't break the `/health`, `/health/ready`, `/metrics`, `/openapi.json` contracts.
- Don't bypass `LLMProvider` / `VectorStore` / `Guardrails` abstractions.
- Don't commit secrets. `.env` is gitignored; example only is committed.
- Don't push directly to `main` — open a PR.
