# Pull Request Guidelines

## Size

- Aim for **< 400 lines changed** per PR.
- One concern per PR. Mixed concerns ⇒ split.
- Refactors and feature work go in separate PRs.

## Title

Conventional Commits format. Examples:

```
feat(rag): add cross-encoder reranker behind FEATURE_RERANKER
fix(api): return 422 envelope from validation errors
perf(inference): batch embeddings to 64 within 20 ms window
docs(report): expand evaluation section
test(governance): cover prompt-injection edge cases
chore(deps): bump fastapi to 0.115.0
```

## Description template

```
## Summary
1–3 bullet points: what + why (not how).

## Changes
- File / module: short note
- File / module: short note

## Validation
- `make lint && make test` ✅
- `pytest -m integration` ✅ (when relevant)
- `pytest -m evaluation` ✅ (when relevant)
- Manual: <one-liner if applicable>

## Risk & rollback
- Risk: <low / medium / high> — reason
- Rollback: <revert PR / disable feature flag / etc.>

## Related
- Closes #<issue>
- Depends on #<pr>
```

## Mandatory checks (CI must pass)

- Ruff lint
- Black format check
- mypy (non-blocking but no NEW errors)
- Unit tests
- AI quality benchmark (on PRs)
- Docker build + Trivy scan (on main)
- CodeQL
- Gitleaks

## Review checklist (reviewers)

- [ ] Does it preserve fallbacks (in-memory vector store, hash embeddings, regex PII)?
- [ ] Does it preserve API contracts (`/health`, `/metrics`, `/openapi.json`)?
- [ ] Are new metrics named `warranty_<domain>_<unit>{labels}`?
- [ ] Are new env vars in `.env.example`?
- [ ] Are new deps in BOTH `requirements.txt` and `pyproject.toml`?
- [ ] Is `REPO_STATE.md` updated?
- [ ] Is `CHANGELOG.md` `[Unreleased]` updated?

## Approval

- 1 approval from a code owner for changes under `app/`.
- 2 approvals for changes to `app/config/settings.py`, `app/governance/`, or
  `infrastructure/`.

## Merging

- **Squash and merge** for feature/fix PRs (1 commit per PR on main).
- **Rebase and merge** for refactor PRs that keep meaningful history.
- Never "merge commit" — keep `main` linear.
