import pytest


@pytest.mark.integration
def test_health_endpoint(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "components" in body


@pytest.mark.integration
def test_readiness_endpoint(api_client):
    resp = api_client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"ok", "degraded"}


@pytest.mark.integration
def test_metrics_endpoint(api_client):
    # Hit a route so something is recorded.
    api_client.get("/health")
    resp = api_client.get("/metrics")
    assert resp.status_code == 200
    assert "warranty_request_duration_seconds" in resp.text or "process_cpu_seconds_total" in resp.text


@pytest.mark.integration
def test_root(api_client):
    resp = api_client.get("/")
    assert resp.status_code == 200
    assert "version" in resp.json()


@pytest.mark.integration
def test_openapi_schema(api_client):
    resp = api_client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    paths = schema["paths"]
    for required in ("/health", "/query", "/retrieve", "/analyze", "/summarize", "/evaluate"):
        assert required in paths
