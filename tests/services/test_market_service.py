from datetime import datetime, timezone
from app.services.market_service import to_ms, map_candle, VALID_INTERVALS


def test_to_ms_epoch_is_zero():
    epoch = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert to_ms(epoch) == 0


def test_to_ms_one_second_is_1000ms():
    dt = datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    assert to_ms(dt) == 1000


def test_map_candle_returns_named_fields():
    raw = [
        1715299200000, "67000.00", "67450.00", "66800.00", "67200.00", "123.45",
        1715299499999, "456.78", 100, "50.00", "23.45", "0"
    ]
    result = map_candle(raw)
    assert result["open_time"] == "2024-05-10T00:00:00Z"
    assert result["open"] == "67000.00"
    assert result["high"] == "67450.00"
    assert result["low"] == "66800.00"
    assert result["close"] == "67200.00"
    assert result["volume"] == "123.45"


def test_valid_intervals_contains_expected():
    assert "5m" in VALID_INTERVALS
    assert "1d" in VALID_INTERVALS
    assert "1h" in VALID_INTERVALS
    assert "99x" not in VALID_INTERVALS
