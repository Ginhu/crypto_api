import pytest
from app.strategies.base import Trade
from app.services.backtest_service import _compute_metrics


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
