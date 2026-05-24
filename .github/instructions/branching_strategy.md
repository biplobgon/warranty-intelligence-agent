# Branching Strategy

A **trunk-based** strategy with short-lived feature branches.

## Branches

| Branch | Purpose | Lifetime |
|---|---|---|
| `main` | Always deployable. Tagged for releases. | permanent |
| `feat/<short-name>` | New feature work | hours – a few days |
| `fix/<short-name>` | Bug fix | hours – days |
| `chore/<short-name>` | Tooling / deps / cleanup | hours |
| `release/v<x.y.z>` | Release stabilization (only for major releases) | ≤ 1 week |
| `hotfix/<short-name>` | Production hotfix off a release tag | hours |

## Rules

- Branch off `main`. Rebase onto `main` regularly while open.
- Open a PR EARLY (draft is fine) for visibility.
- Squash-merge into `main`. One commit per PR on `main` for feature/fix.
- Delete branches after merge.

## Naming

- Short, kebab-case, descriptive: `feat/reranker`, `fix/health-probe-timeout`.
- Don't include the issue number in the branch — put it in the PR description.

## Protection rules (configured in GitHub settings)

- `main` is protected:
  - Required reviews: 1 (2 for `app/config/`, `app/governance/`, `infrastructure/`)
  - Required status checks: `CI / lint`, `CI / test`, `CI / build` (where applicable)
  - Require linear history (squash or rebase only)
  - No force push, no direct push

## Release tagging

- Tag format: `v<x.y.z>` (SemVer).
- Tag from `main` after CI is green: `git tag v0.2.0 && git push origin v0.2.0`.
- Update `CHANGELOG.md`: move `[Unreleased]` items to `[<x.y.z>] — <date>`.

## Hotfix flow

1. Branch from the tag: `git checkout -b hotfix/<name> v<x.y.z>`
2. Fix + test.
3. PR into `main` AND cherry-pick to the release branch if one exists.
4. Tag `v<x.y.z+1>`.
