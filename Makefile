# =====================================================
# Warranty Intelligence Agent — Developer Makefile
# =====================================================

PY ?= python
PIP ?= pip
COMPOSE ?= docker compose
IMAGE ?= warranty-intel/api
TAG ?= dev

.PHONY: help install dev lint format typecheck test test-unit test-integration eval \
        run docker-build docker-up docker-down k8s-apply k8s-delete data-synth \
        ingest clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime + dev dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev: ## Run FastAPI in hot-reload dev mode
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint: ## Ruff lint
	ruff check app tests

format: ## Black + Ruff format
	black app tests
	ruff check --fix app tests

typecheck: ## mypy static check
	mypy app

test: test-unit ## Run unit tests (default)

test-unit: ## Run unit tests only
	pytest -m unit

test-integration: ## Run integration tests
	pytest -m integration

eval: ## Run evaluation pipeline tests
	pytest -m evaluation

run: ## Run with gunicorn workers (prod-like)
	gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000

docker-build: ## Build API container image
	docker build -t $(IMAGE):$(TAG) -f Dockerfile .

docker-up: ## Bring up full stack (API + Redis + Prom + Grafana + MLflow + OTel)
	$(COMPOSE) up -d --build

docker-down: ## Stop full stack
	$(COMPOSE) down -v

k8s-apply: ## Apply Kubernetes manifests
	kubectl apply -f infrastructure/kubernetes/

k8s-delete: ## Delete Kubernetes manifests
	kubectl delete -f infrastructure/kubernetes/ --ignore-not-found

data-synth: ## Generate synthetic warranty + telemetry + docs datasets
	$(PY) scripts/generate_synthetic_data.py

ingest: ## Run end-to-end ingestion pipeline (chunk + embed + index)
	$(PY) scripts/run_ingestion.py

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage build dist *.egg-info
