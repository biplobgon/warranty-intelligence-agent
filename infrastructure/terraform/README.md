# Terraform — Warranty Intelligence Agent

Skeleton infrastructure for GCP. Provides:

- GKE cluster (`warranty-intel-<env>`) with Workload Identity enabled
- Artifact Registry (Docker) for container images
- Vertex AI-bound service account (`warranty-api`) used via Workload Identity by
  the `warranty-api` Kubernetes deployment

## Usage

```bash
export TF_VAR_project_id="my-gcp-project"
terraform init
terraform plan  -out plan.tfplan
terraform apply plan.tfplan
```

## Customization

| Concern                | Where                                                           |
|------------------------|------------------------------------------------------------------|
| Networking (VPC, subnet) | Add `google_compute_network` / `subnetwork` and wire to cluster |
| KMS / Confidential GKE | Add `database_encryption {}` and `confidential_nodes {}` blocks  |
| Logging / Monitoring   | `monitoring_config {}` / `logging_config {}` on the cluster     |
| Org policy / SCC       | Apply at folder / org level outside this module                 |

For AWS or Azure variants, replicate the same building blocks: managed K8s,
container registry, secret store, and an IAM role bound via OIDC/Workload
Identity.
