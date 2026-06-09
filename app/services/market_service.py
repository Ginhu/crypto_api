from datetime import datetime, timezone

VALID_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}


def to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def map_candle(raw: list) -> dict:
    open_time = datetime.fromtimestamp(raw[0] / 1000, tz=timezone.utc)
    return {
        "open_time": open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "open": raw[1],
        "high": raw[2],
        "low": raw[3],
        "close": raw[4],
        "volume": raw[5],
    }
