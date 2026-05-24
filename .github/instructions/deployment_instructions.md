# Deployment Instructions

## Environments

| Env | Cluster | Branch | Trigger |
|---|---|---|---|
| `local` | docker-compose | any | `make docker-up` |
| `staging` | GKE `warranty-intel-staging` | `main` | manual `deploy.yml` |
| `production` | GKE `warranty-intel-prod` | tags `v*` | manual `deploy.yml` with approval |

## Prerequisites (per environment)

- Kubernetes cluster reachable (Workload Identity configured)
- `warranty-intel` namespace exists
- Secrets provisioned (via External Secrets / SealedSecrets / Vault):
  - `OPENAI_API_KEY` (or `GOOGLE_APPLICATION_CREDENTIALS` for Vertex)
  - `PINECONE_API_KEY`
  - `API_KEY` (strong, random)
  - `LANGCHAIN_API_KEY` (optional)
- `kube-prometheus-stack`, `cert-manager`, and `ingress-nginx` installed
- (Optional) Tempo / Jaeger / Cloud Trace endpoint reachable

## Standard deploy (Helm)

```bash
helm upgrade --install warranty-intel infrastructure/helm/warranty-intel \
  --namespace warranty-intel --create-namespace \
  --set image.tag=<git-sha> \
  --set ingress.host=api.warranty-intel.<env>.example.com \
  --wait --timeout 5m
```

## Verify

```bash
kubectl -n warranty-intel rollout status deploy/warranty-intel -w
kubectl -n warranty-intel get hpa
curl -sf https://api.warranty-intel.<env>.example.com/health
```

## Smoke test (run after every deploy)

```bash
BASE=https://api.warranty-intel.<env>.example.com
KEY=$API_KEY

curl -sf $BASE/health
curl -sf $BASE/health/ready
curl -sf -X POST $BASE/evaluate -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"question":"x","answer":"y","contexts":["x"]}'
```

## Rollback

```bash
helm rollback warranty-intel <previous-revision> -n warranty-intel --wait
```

Or pin to a previous image:

```bash
helm upgrade warranty-intel infrastructure/helm/warranty-intel \
  -n warranty-intel --set image.tag=<previous-sha> --wait
```

## Cutover for breaking changes

1. Deploy NEW version alongside OLD (canary 10%).
2. Monitor `warranty_request_duration_seconds`, `warranty_hallucination_score`,
   `warranty_governance_blocks_total`, and 5xx rate.
3. Promote (50% → 100%) or rollback within 30 min.
4. Update DNS / ingress only after 100% promote is stable.

## Approval

- Production deploys require **one approver** in the GitHub Environment.
- Hotfixes can self-approve if the on-call has elevated permissions and posts
  in `#warranty-intel-deploys`.

## Post-deploy

- Update `CHANGELOG.md` with the release tag and date.
- Tag the commit on `main`: `git tag v<x.y.z> && git push origin v<x.y.z>`.
- Post a brief summary in `#warranty-intel-releases` (what / why / risk).
