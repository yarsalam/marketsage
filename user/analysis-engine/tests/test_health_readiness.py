from fastapi.testclient import TestClient

import price_service


client = TestClient(price_service.app)


def test_health_is_liveness_and_does_not_claim_source_approval():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "analysis-engine",
        "check": "liveness",
    }


def test_ready_reports_research_only_scope_and_disabled_ranking():
    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["readiness_scope"] == "research_only"
    assert payload["checks"] == {
        "source_registry": "ready",
        "research_snapshot_pipeline": "ready",
    }
    assert payload["registered_source_count"] > 0
    assert payload["production_approved_source_count"] == 0
    assert payload["investment_ranking_enabled"] is False


def test_ready_returns_503_if_source_registry_is_empty(monkeypatch):
    monkeypatch.setattr(
        price_service,
        "source_catalog",
        lambda: {
            "summary": {"total_sources": 0, "production_approved": 0},
            "sources": [],
        },
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "not_ready",
        "reason": "critical_local_dependency_unavailable",
    }
