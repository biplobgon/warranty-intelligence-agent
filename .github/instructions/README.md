# `.github/instructions/` — Engineering Standards

Policy documents that apply to every contributor (human or AI).

| Standard | Scope |
|---|---|
| [engineering_standards.md](engineering_standards.md) | Language, style, typing, logging, errors, deps, tests, docs |
| [pr_guidelines.md](pr_guidelines.md) | PR size, description template, checks, review checklist, merging |
| [commit_standards.md](commit_standards.md) | Conventional Commits, scopes, examples, anti-patterns |
| [branching_strategy.md](branching_strategy.md) | Trunk-based, branch naming, protection rules, release tagging |
| [deployment_instructions.md](deployment_instructions.md) | Environments, Helm deploy, smoke tests, rollback, cutover |
| [architecture_conventions.md](architecture_conventions.md) | Layers, allowed deps, abstractions, naming, folder rules |
| [ai_governance.md](ai_governance.md) | Input/output policy, PII, logging, audit, incident response |
| [observability_standards.md](observability_standards.md) | Metrics, traces, logs, instrumentation requirements |

## How these are enforced

- Reviewers reject PRs that violate these standards.
- CI catches lint / type / test violations automatically.
- Architectural deviations (cross-layer imports, removed abstractions) require an
  RFC and 2 approvals.

## How to propose a change

1. Open an RFC PR that modifies the relevant standard file.
2. Tag at least 2 code owners.
3. Discuss; merge once consensus is reached.
4. Update `CHANGELOG.md` if the change affects external contributors.
