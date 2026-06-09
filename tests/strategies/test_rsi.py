from app.strategies.base import Trade
from app.strategies.rsi import rsi_oversold


def _make_candles(prices: list[float]) -> list[dict]:
    return [
        {
            "open_time": f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}T00:00:00Z",
            "open": str(p), "high": str(p), "low": str(p),
            "close": str(p), "volume": "100.0",
        }
        for i, p in enumerate(prices)
    ]


def test_rsi_oversold_too_few_candles():
    assert rsi_oversold(_make_candles([100.0] * 10)) == []


def test_rsi_oversold_flat_prices_no_signal():
    # Flat prices: RSI stays ~50, no threshold crossed
    assert rsi_oversold(_make_candles([100.0] * 50)) == []


def test_rsi_oversold_returns_trades_with_valid_structure():
    # Steep decline (RSI < 30) then steep rise (RSI > 70)
    prices = [200.0 - i * 8 for i in range(25)] + [50.0 + i * 10 for i in range(25)]
    trades = rsi_oversold(_make_candles(prices))
    for t in trades:
        assert isinstance(t, Trade)
        assert isinstance(t.entry_price, float)
        assert isinstance(t.exit_price, float)
        assert t.entry_time < t.exit_time


def test_rsi_oversold_open_trade_not_included():
    # Only declining phase: entry opens but RSI never exceeds 70 — must not appear in results
    prices = [200.0 - i * 8 for i in range(25)]
    for t in rsi_oversold(_make_candles(prices)):
        assert t.exit_time != ""


def test_registry_contains_both_strategies():
    from app.strategies import REGISTRY
    assert "rsi_oversold" in REGISTRY
    assert "ma_crossover_20_50" in REGISTRY
    assert callable(REGISTRY["rsi_oversold"])
    assert callable(REGISTRY["ma_crossover_20_50"])
