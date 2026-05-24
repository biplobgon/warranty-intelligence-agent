# COPILOT.md — GitHub Copilot Agent Mode memory (compact)

> **Read `REPO_STATE.md` first.** This file is Copilot-specific guidance only.

## Project one-liner

Enterprise multi-agent AI platform for warranty intelligence. See `README.md` (pitch), `REPO_STATE.md` (state), `CHANGELOG.md` (history).

## Files Copilot should read first

1. `REPO_STATE.md`
2. `CHANGELOG.md` `[Unreleased]`
3. The single module you'll edit (`app/<module>/`)
4. Matching tests under `tests/`

Don't load the workspace tree wholesale. Use the workspace symbol index and targeted opens.

## Copilot sweet spot here

- Method-body completion from a clear docstring + signature
- Repetitive scaffolding (schema → route → test triplet)
- Translating shell snippets to PowerShell equivalents when needed
- Suggesting metric labels following `warranty_*` convention

## Copilot MUST NOT auto-do

- Add deps without updating both `requirements.txt` and `pyproject.toml`
- Replace `structlog` with stdlib `logging` / `print`
- Bypass `app/services/llm_provider.py` for any LLM call
- Change governance thresholds in `app/config/settings.py` without a `CHANGELOG.md` entry
- Break the offline test path (`fake_llm` fixture must keep working)

## Hard constraints

See `REPO_STATE.md` §11. Frozen contracts: `/health`, `/health/ready`, `/metrics`, `/openapi.json`.

## End-of-session checklist

- [ ] `make lint && make test` clean
- [ ] `REPO_STATE.md` updated (only changed sections)
- [ ] `CHANGELOG.md` `[Unreleased]` one-liner added
- [ ] Conventional Commit message

## Token discipline

- Limit Copilot Chat context to: `REPO_STATE.md` + the file being edited + its test.
- Don't paste full files into Chat; reference them by path.
- Prefer "explain just this function" over "explain this module".
