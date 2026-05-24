"""Application settings.

Uses pydantic-settings for typed, validated, environment-driven configuration.
Treat this as the single source of truth for runtime config across the platform.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from environment variables.

    All secrets use `SecretStr` so they never accidentally render in logs.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Service ----
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "warranty-intelligence-agent"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 2

    # ---- Security ----
    api_key: SecretStr = SecretStr("dev-local-key-change-me")
    allowed_origins: str = "*"

    # ---- LLM Providers ----
    llm_provider: Literal["openai", "vertexai", "local"] = "openai"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"

    vertex_project_id: str = ""
    vertex_location: str = "us-central1"
    vertex_model: str = "gemini-1.5-pro"

    local_inference_base_url: str = "http://vllm:8000/v1"
    local_inference_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    # ---- Vector Store ----
    vector_backend: Literal["pinecone", "faiss"] = "pinecone"
    pinecone_api_key: SecretStr = SecretStr("")
    pinecone_environment: str = "us-east-1-aws"
    pinecone_index_warranty: str = "warranty-claims"
    pinecone_index_docs: str = "technical-docs"

    # ---- Caching / Redis ----
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 3600

    # ---- Observability ----
    otel_exporter_otlp_endpoint: str = "http://otel-collector:4317"
    otel_service_name: str = "warranty-intel-api"
    prometheus_metrics_path: str = "/metrics"
    mlflow_tracking_uri: str = "http://mlflow:5000"
    mlflow_experiment: str = "warranty-intel"

    langchain_tracing_v2: bool = False
    langchain_api_key: SecretStr = SecretStr("")
    langchain_project: str = "warranty-intelligence-agent"

    # ---- Evaluation / Governance ----
    enable_guardrails: bool = True
    enable_pii_redaction: bool = True
    hallucination_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    grounding_threshold: float = Field(default=0.70, ge=0.0, le=1.0)

    # ---- Ray ----
    ray_address: str = "auto"

    # ---- Feature flags ----
    feature_hybrid_retrieval: bool = True
    feature_reranker: bool = True
    feature_mcp_tools: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor; safe to call from anywhere."""
    return Settings()
