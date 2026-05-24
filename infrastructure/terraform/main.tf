# =============================================================
# Warranty Intelligence Agent — Cloud Infrastructure (skeleton)
#
# Provides GKE cluster, Artifact Registry, Pinecone API key secret,
# and Vertex AI service-account bindings.  Designed as a starting
# point — adapt to your org's module / module-registry conventions.
# =============================================================

terraform {
  required_version = ">= 1.7"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
  backend "gcs" {
    bucket = "REPLACE-ME-tfstate"
    prefix = "warranty-intel"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "env" {
  type    = string
  default = "prod"
}

# ---------- GKE ----------
resource "google_container_cluster" "warranty" {
  name                     = "warranty-intel-${var.env}"
  location                 = var.region
  remove_default_node_pool = true
  initial_node_count       = 1
  release_channel { channel = "REGULAR" }
  workload_identity_config { workload_pool = "${var.project_id}.svc.id.goog" }
  networking_mode = "VPC_NATIVE"
}

resource "google_container_node_pool" "primary" {
  name       = "primary"
  cluster    = google_container_cluster.warranty.name
  location   = var.region
  node_count = 3

  node_config {
    machine_type = "e2-standard-4"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    workload_metadata_config { mode = "GKE_METADATA" }
    labels = { workload = "warranty-intel" }
  }

  autoscaling {
    min_node_count = 3
    max_node_count = 12
  }
}

# ---------- Artifact Registry ----------
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "warranty-intel"
  description   = "Container images for Warranty Intelligence platform"
  format        = "DOCKER"
}

# ---------- Workload Identity SA for the API ----------
resource "google_service_account" "warranty_api" {
  account_id   = "warranty-api"
  display_name = "Warranty Intelligence API"
}

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.warranty_api.email}"
}

output "cluster_endpoint" {
  value     = google_container_cluster.warranty.endpoint
  sensitive = true
}

output "registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/warranty-intel"
}

output "api_service_account_email" {
  value = google_service_account.warranty_api.email
}
