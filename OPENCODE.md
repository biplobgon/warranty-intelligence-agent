# OPENCODE.md — OpenCode memory (compact)

> **Read `REPO_STATE.md` first.** This file is OpenCode-specific and low-token by design.

## Project one-liner

Enterprise multi-agent AI platform for warranty analytics. See `README.md` for the pitch, `REPO_STATE.md` for current state, `CHANGELOG.md` for last shipped.

## Bootstrap (every session)

1. `REPO_STATE.md`
2. `CHANGELOG.md` `[Unreleased]`
3. Only the file(s) you'll edit. Use `grep`/`glob`, not full reads, when scanning.

# Low-Token Development Workflow

OpenCode runs on token-priced models. Follow this workflow to keep sessions cheap and continuous.

## 1. Prompt-size rules

- Open at most **2–3 files** before editing.
- Never paste full repo trees, full file lists, or full READMEs into prompts.
- Prefer `grep` (with file-pattern filters) over `read` for "where is X?" questions.
- Use `glob` for file enumeration; do not list directories with `bash`.

## 2. Module-scoped reasoning

- Edits should stay inside ONE `app/<module>/` at a time.
- Cross-module changes ⇒ split into separate commits and separate sessions.
- If a task touches >5 files, stop and ask the user to scope it.

## 3. Incremental task framing

Good (low-token) prompts to the user/agent:

- "Add `/forecast` route under `app/api/routes/`, schema, test."
- "Extend `Evaluator.evaluate` with a Jaccard metric."
- "Add Pinecone metadata filter for `failure_mode`."
- "Add Grafana panel for `warranty_governance_blocks_total`."

Avoid:

- "Re-explain the architecture."
- "Walk me through the whole repo."
- "Generate the project again."

## 4. Persistent memory first

For state, ALWAYS read `REPO_STATE.md` before scanning code. It is the canonical compressed state.
If you find a delta, **update `REPO_STATE.md`** in the same commit; do not re-paste it elsewhere.

## 5. Avoid repo-wide scans

Forbidden by default:

- `Get-ChildItem -Recurse` on the whole repo
- `grep -r` without `--include` filter
- Reading more than 200 lines of a file without intent

Use:

- `grep --include="*.py" "<pattern>" app`
- `glob "app/**/<thing>.py"`
- `read app/<path> offset=N limit=80`

## 6. Model usage strategy

| Model class | Use for |
|---|---|
| **Opus / GPT-5 / large reasoning** | Architecture, orchestration, RAG design, infra design, debugging distributed/concurrent issues, evaluation methodology |
| **Sonnet / Haiku / smaller** | Boilerplate, refactors, markdown, Dockerfiles, K8s YAML, unit tests, CRUD routes, doc updates, prompt tweaks |
| **Local / cheap** | Renaming, formatting, comment cleanup, dependency bumps |

Heuristic: if the task has ONE clear correct answer (e.g. "add a metric"), use the small model.
Use the large model only when the task is "decide between options" or "design X".

## 7. Tool-call discipline

- Batch independent reads/searches in one tool call.
- Don't re-read a file you've already read in the session.
- Use `read offset/limit` for large files; never dump 2000 lines just to see one function.

## 8. Stop conditions

Stop and ask the user when:

- A change would touch >5 files or >2 modules
- A change would alter `REPO_STATE.md` "Hard constraints"
- A new external dependency would be added
- A `/health`, `/metrics`, or `/openapi.json` contract would change

## 9. End-of-session checklist

- [ ] `make lint && make test` clean
- [ ] `REPO_STATE.md` updated (only changed sections)
- [ ] `CHANGELOG.md` `[Unreleased]` has a one-liner
- [ ] Conventional Commit message
- [ ] No secrets, no large files added

## OpenCode-specific gotchas

- Windows host. Don't normalize CRLF/LF in bulk.
- Use the structured tools (`read`/`edit`/`write`/`grep`/`glob`) over shell.
- `bash` is PowerShell here — use `;` or `if ($?) { ... }`, not `&&`.
- Idempotent inits: every `setup_*` is safe to call multiple times.

## Where state lives (don't duplicate)

- Architecture / status: `REPO_STATE.md`
- ADRs: `CLAUDE.md` (compact table)
- Standards (deploy, observability, governance): `.github/instructions/`
- Reusable playbooks: `.claude/skills/`
- Long-form report: `docs/reports/technical_report.md`
