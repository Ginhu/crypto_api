import pytest
from unittest.mock import AsyncMock, patch
from app.strategies.base import Trade
from app.services.backtest_service import _compute_metrics, _get_candles, run_backtest


def test_compute_metrics_no_trades():
    assert _compute_metrics([]) == {
        "total_return_pct": 0.0,
        "win_rate_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "sharpe_ratio": 0.0,
        "num_trades": 0,
    }


def test_compute_metrics_one_winning_trade():
    trades = [Trade("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", 100.0, 110.0)]
    result = _compute_metrics(trades)
    assert result["num_trades"] == 1
    assert result["total_return_pct"] == 10.0
    assert result["win_rate_pct"] == 100.0
    assert result["max_drawdown_pct"] == 0.0
    assert result["sharpe_ratio"] == 0.0  # single trade: std dev is 0


def test_compute_metrics_mixed_trades():
    trades = [
        Trade("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", 100.0, 110.0),  # +10%
        Trade("2026-01-03T00:00:00Z", "2026-01-04T00:00:00Z", 110.0, 99.0),   # -10%
    ]
    result = _compute_metrics(trades)
    assert result["num_trades"] == 2
    assert result["win_rate_pct"] == 50.0
    assert result["total_return_pct"] == pytest.approx(0.0, abs=0.01)
    assert result["max_drawdown_pct"] < 0


def test_compute_metrics_drawdown_is_negative():
    trades = [
        Trade("t1", "t2", 100.0, 120.0),  # +20%
        Trade("t3", "t4", 120.0, 90.0),   # -25%
    ]
    result = _compute_metrics(trades)
    assert result["max_drawdown_pct"] < 0


FAKE_CANDLES = [
    {
        "open_time": "2026-01-15T00:00:00Z",
        "open": "100", "high": "110", "low": "90",
        "close": "105", "volume": "50",
    }
]


@pytest.mark.asyncio
async def test_get_candles_uses_cached_mongo_data():
    mock_doc = {
        "symbol": "BTCUSDT", "interval": "5m",
        "start": "2026-01-01", "end": "2026-06-01",
        "candles": FAKE_CANDLES,
    }
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = mock_doc
    with patch("app.services.backtest_service.mongo_client") as mock_mongo:
        mock_mongo.get_collection.return_value = mock_collection
        result = await _get_candles("BTCUSDT", "5m", "2026-01-01", "2026-06-01")
    assert result == FAKE_CANDLES
    mock_collection.find_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_candles_fetches_from_binance_when_no_cache():
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = None
    raw = [[1735689600000, "100", "110", "90", "105", "50", 0, "0", 1, "0", "0", "0"]]
    with patch("app.services.backtest_service.mongo_client") as mock_mongo, \
         patch("app.services.backtest_service.fetch_klines", new_callable=AsyncMock, return_value=raw), \
         patch("app.services.backtest_service.save_dataset", new_callable=AsyncMock):
        mock_mongo.get_collection.return_value = mock_collection
        result = await _get_candles("BTCUSDT", "5m", "2026-01-01", "2026-01-31")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_run_backtest_completes_job_successfully():
    with patch("app.services.backtest_service.mongo_client") as mock_mongo, \
         patch("app.services.backtest_service._get_candles", new_callable=AsyncMock, return_value=FAKE_CANDLES), \
         patch("app.services.backtest_service.REGISTRY", {"dummy": lambda candles: []}):
        mock_mongo.update_job = AsyncMock()
        await run_backtest("job-1", "BTCUSDT", "5m", "2026-01-01", "2026-01-31", ["dummy"])
    statuses = [call.args[1]["status"] for call in mock_mongo.update_job.call_args_list]
    assert "running" in statuses
    assert "completed" in statuses


@pytest.mark.asyncio
async def test_run_backtest_marks_failed_on_error():
    with patch("app.services.backtest_service.mongo_client") as mock_mongo, \
         patch("app.services.backtest_service._get_candles", new_callable=AsyncMock, side_effect=Exception("binance down")):
        mock_mongo.update_job = AsyncMock()
        await run_backtest("job-2", "BTCUSDT", "5m", "2026-01-01", "2026-01-31", ["rsi_oversold"])
    last_update = mock_mongo.update_job.call_args_list[-1].args[1]
    assert last_update["status"] == "failed"
    assert "binance down" in last_update["error"]
