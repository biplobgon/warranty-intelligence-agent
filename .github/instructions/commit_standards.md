# Commit Standards

Use **Conventional Commits**: `<type>(<scope>): <subject>`.

## Types

| Type | Meaning |
|---|---|
| `feat` | New feature or behavior |
| `fix` | Bug fix |
| `perf` | Performance improvement (no behavior change) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `docs` | Documentation only |
| `test` | Tests only |
| `chore` | Build / tooling / deps |
| `ci` | CI/CD pipeline changes |
| `style` | Formatting (no semantic change) |
| `revert` | Reverts an earlier commit |

## Scopes (preferred set)

`api`, `agents`, `workflow`, `rag`, `embeddings`, `inference`, `services`,
`governance`, `evaluation`, `observability`, `prompts`, `config`, `infra`,
`k8s`, `helm`, `docker`, `ci`, `deps`, `data`, `tests`, `docs`, `report`,
`memory`.

## Subject

- Imperative mood ("add", not "added" or "adds").
- ≤ 72 chars.
- No trailing period.

## Body (optional but encouraged for non-trivial commits)

- Wrap at ~80 chars.
- Explain **why**, not **what** (the diff explains what).
- Reference related PRs / issues: `Closes #123`, `Relates to #456`.

## Footer (optional)

- `BREAKING CHANGE: <description>` when applicable.
- `Co-authored-by: Name <email>` for pairing.

## Examples

```
feat(rag): add cross-encoder reranker behind FEATURE_RERANKER

The hybrid retriever now optionally reranks top-K results with a local
cross-encoder. Adds ~30 ms p95 but improves grounding by 6 pts on the
synthetic benchmark.

Closes #42
```

```
fix(api): return 422 envelope from validation errors

Previously FastAPI's default 422 body bypassed our ErrorResponse envelope,
breaking the contract for client SDKs.
```

```
chore(memory): optimize repo for low-token multi-agent continuity

Externalize repo state into REPO_STATE.md and compress per-agent memory
files to thin, agent-specific guidance. Future sessions only need to load
REPO_STATE.md instead of duplicated verbose memory.
```

## Anti-patterns

- ❌ `update stuff`
- ❌ `WIP`
- ❌ `fix things`
- ❌ Mixed concerns (`feat(api): add /forecast and fix bug in /query`)
- ❌ Subject > 72 chars
- ❌ "what" in subject without "why" in body for non-trivial commits

## Rebases / fixups

- Use `git commit --fixup=<hash>` + `git rebase -i --autosquash` BEFORE pushing.
- Don't force-push to shared branches unless coordinated.
- Don't `git rebase` on `main`.
