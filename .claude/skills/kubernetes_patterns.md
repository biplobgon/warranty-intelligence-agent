# Skill — Kubernetes Patterns

## When to load

- Adding / changing manifests or Helm templates
- Tuning HPA, PDB, NetworkPolicy
- Debugging probe failures
- Onboarding a new cluster / environment

## Mental model

```
Ingress (TLS) → Service (ClusterIP) → Deployment (HPA 3..20) → Pod (non-root, RO FS)
                                                               ├─ /health (liveness)
                                                               └─ /health/ready (readiness)
```

## Key files

| File | Role |
|---|---|
| `infrastructure/kubernetes/*.yaml` | Raw manifests |
| `infrastructure/helm/warranty-intel/` | Helm chart |
| `infrastructure/terraform/main.tf` | GKE skeleton |

## Standard tasks

### 1. Roll out a new image

```bash
# Raw
kubectl -n warranty-intel set image deploy/warranty-api api=ghcr.io/.../api:<sha>
kubectl -n warranty-intel rollout status deploy/warranty-api

# Helm
helm upgrade warranty-intel infrastructure/helm/warranty-intel \
  -n warranty-intel --set image.tag=<sha>
```

### 2. Tune autoscaling

`infrastructure/kubernetes/hpa.yaml` and `values.yaml`:
- CPU target 65%
- Memory target 75%
- Aggressive scale-up (Percent 100, Pods 4 / 30s)
- Conservative scale-down (5 min stabilization, Percent 25 / 60s)

### 3. Add a NetworkPolicy egress

```yaml
egress:
  - to: [{ namespaceSelector: {} }]
    ports:
      - { protocol: TCP, port: <new_port> }
```

Currently allow-listed: 6379 (Redis), 5000 (MLflow), 4317 (OTel), 443 (external APIs), 53 (DNS).

### 4. Add a CronJob (e.g. nightly ingestion)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: warranty-ingest, namespace: warranty-intel }
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: ingest
              image: ghcr.io/.../api:latest
              command: ["python", "scripts/run_ingestion.py"]
              envFrom: [{ configMapRef: { name: warranty-api-config } }, { secretRef: { name: warranty-api-secrets } }]
          restartPolicy: OnFailure
```

## Hard rules

- runAsNonRoot, readOnlyRootFilesystem, drop ALL caps — already enforced.
- minAvailable=2 PDB so rolling updates can't take everyone down.
- Probes hit `/health` (liveness) and `/health/ready` (readiness).
- Use Workload Identity (or IRSA) for cloud creds — NOT JSON keys in secrets.

## Debugging

```bash
kubectl -n warranty-intel get pods,svc,ingress,hpa
kubectl -n warranty-intel describe pod <name>
kubectl -n warranty-intel logs <pod> -c api --tail=200
kubectl -n warranty-intel exec -it <pod> -- /bin/sh
kubectl -n warranty-intel port-forward svc/warranty-api 8000:80
```
