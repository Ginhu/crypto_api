from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FAKE_RAW_CANDLES = [
    [1715299200000, "67000.00", "67450.00", "66800.00", "67200.00", "123.45",
     1715299499999, "456.78", 100, "50.00", "23.45", "0"]
]


def test_get_klines_default_params():
    with patch(
        "app.api.v1.routes.market.fetch_klines",
        new_callable=AsyncMock,
        return_value=FAKE_RAW_CANDLES,
    ):
        response = client.get("/api/v1/market/BTCUSDT/klines")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "BTCUSDT"
    assert body["interval"] == "5m"
    assert len(body["candles"]) == 1
    assert body["candles"][0]["open"] == "67000.00"


def test_get_klines_custom_params():
    with patch(
        "app.api.v1.routes.market.fetch_klines",
        new_callable=AsyncMock,
        return_value=FAKE_RAW_CANDLES,
    ):
        response = client.get(
            "/api/v1/market/ETHUSDT/klines",
            params={"interval": "1h", "start": "2026-01-01", "end": "2026-01-31"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "ETHUSDT"
    assert body["interval"] == "1h"
    assert body["start"] == "2026-01-01"
    assert body["end"] == "2026-01-31"


def test_get_klines_invalid_interval_returns_400():
    response = client.get("/api/v1/market/BTCUSDT/klines?interval=99x")
    assert response.status_code == 400
    assert "interval" in response.json()["detail"].lower()


def test_get_klines_start_after_end_returns_400():
    response = client.get(
        "/api/v1/market/BTCUSDT/klines",
        params={"start": "2026-06-01", "end": "2026-05-01"},
    )
    assert response.status_code == 400


def test_get_klines_binance_400_returns_400():
    from app.clients.binance_client import BinanceClientError

    with patch(
        "app.api.v1.routes.market.fetch_klines",
        new_callable=AsyncMock,
        side_effect=BinanceClientError("Invalid symbol.", status_code=400),
    ):
        response = client.get("/api/v1/market/FAKE/klines")
    assert response.status_code == 400
    assert "Invalid symbol." in response.json()["detail"]


def test_get_klines_binance_unreachable_returns_502():
    from app.clients.binance_client import BinanceClientError

    with patch(
        "app.api.v1.routes.market.fetch_klines",
        new_callable=AsyncMock,
        side_effect=BinanceClientError("Binance API error", status_code=502),
    ):
        response = client.get("/api/v1/market/BTCUSDT/klines")
    assert response.status_code == 502
