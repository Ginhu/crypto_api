from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_submit_backtest_returns_202():
    with patch("app.api.v1.routes.backtest.mongo_client") as mock_mongo, \
         patch("app.api.v1.routes.backtest.run_backtest", new_callable=AsyncMock):
        mock_mongo.create_job = AsyncMock()
        response = client.post("/api/v1/backtest", json={
            "symbol": "BTCUSDT",
            "interval": "5m",
            "start": "2026-01-01",
            "end": "2026-06-01",
            "strategies": ["rsi_oversold"],
        })
    assert response.status_code == 202
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "pending"


def test_submit_backtest_unknown_strategy_returns_400():
    response = client.post("/api/v1/backtest", json={
        "symbol": "BTCUSDT",
        "interval": "5m",
        "start": "2026-01-01",
        "end": "2026-06-01",
        "strategies": ["nonexistent_strategy"],
    })
    assert response.status_code == 400
    assert "nonexistent_strategy" in response.json()["detail"]


def test_submit_backtest_invalid_interval_returns_400():
    response = client.post("/api/v1/backtest", json={
        "symbol": "BTCUSDT",
        "interval": "99x",
        "start": "2026-01-01",
        "end": "2026-06-01",
        "strategies": ["rsi_oversold"],
    })
    assert response.status_code == 400


def test_submit_backtest_start_after_end_returns_400():
    response = client.post("/api/v1/backtest", json={
        "symbol": "BTCUSDT",
        "interval": "5m",
        "start": "2026-06-01",
        "end": "2026-01-01",
        "strategies": ["rsi_oversold"],
    })
    assert response.status_code == 400


def test_get_backtest_returns_job():
    mock_job = {
        "job_id": "abc123",
        "status": "completed",
        "symbol": "BTCUSDT",
        "interval": "5m",
        "start": "2026-01-01",
        "end": "2026-06-01",
        "results": [],
    }
    with patch("app.api.v1.routes.backtest.mongo_client") as mock_mongo:
        mock_mongo.get_job = AsyncMock(return_value=mock_job)
        response = client.get("/api/v1/backtest/abc123")
    assert response.status_code == 200
    assert response.json()["job_id"] == "abc123"
    assert response.json()["status"] == "completed"


def test_get_backtest_not_found_returns_404():
    with patch("app.api.v1.routes.backtest.mongo_client") as mock_mongo:
        mock_mongo.get_job = AsyncMock(return_value=None)
        response = client.get("/api/v1/backtest/doesnotexist")
    assert response.status_code == 404
