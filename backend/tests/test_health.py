def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["use_mock"] is True
    assert body["database_connected"] is True
    assert body["pgvector_enabled"] is True
