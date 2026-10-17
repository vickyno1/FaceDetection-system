"""
Unit and Integration Tests for System Health Endpoint.
"""

def test_health_check_returns_200(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "status" in data
    assert data["service"] == "student-attendance-face-recognition"
    assert "models" in data
    assert "configured_timezone" in data
    assert data["configured_timezone"] == "Asia/Kolkata"

def test_health_check_cors_headers(client):
    res = client.options("/api/health")
    assert res.status_code == 200
    assert "Access-Control-Allow-Origin" in res.headers
