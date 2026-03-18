"""Health check endpoint tests."""


def test_health_check(client):
    """HEALTH-001: Health endpoint returns ok status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
