from app.strategies.base import Trade
from app.strategies.ma_crossover import ma_crossover_20_50


def _make_candles(prices: list[float]) -> list[dict]:
    return [
        {
            "open_time": f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}T00:00:00Z",
            "open": str(p), "high": str(p), "low": str(p),
            "close": str(p), "volume": "100.0",
        }
        for i, p in enumerate(prices)
    ]


def test_ma_crossover_too_few_candles():
    assert ma_crossover_20_50(_make_candles([100.0] * 40)) == []


def test_ma_crossover_flat_prices_no_signal():
    # MA20 == MA50 always — no crossover
    assert ma_crossover_20_50(_make_candles([100.0] * 100)) == []


def test_ma_crossover_produces_trade_with_valid_structure():
    # 70 low candles → 70 high candles → 70 low candles forces both crossovers
    prices = [100.0] * 70 + [300.0] * 70 + [100.0] * 70
    trades = ma_crossover_20_50(_make_candles(prices))
    assert len(trades) >= 1
    t = trades[0]
    assert isinstance(t, Trade)
    assert t.entry_time < t.exit_time
    assert isinstance(t.entry_price, float)
    assert isinstance(t.exit_price, float)


def test_ma_crossover_open_trade_not_included():
    # Rise but no fall: crossover up fires but no crossover down — no completed trades
    prices = [100.0] * 70 + [300.0] * 70
    for t in ma_crossover_20_50(_make_candles(prices)):
        assert t.exit_time != ""
