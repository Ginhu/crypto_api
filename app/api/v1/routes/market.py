from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.clients.binance_client import BinanceClientError, fetch_klines
from app.services.market_service import VALID_INTERVALS, map_candle, to_ms

router = APIRouter(tags=["market"])


@router.get("/market/{symbol}/klines")
async def get_klines(
    symbol: str,
    interval: str = Query(default="5m"),
    start: date = Query(default=None),
    end: date = Query(default=None),
):
    if interval not in VALID_INTERVALS:
        raise HTTPException(status_code=400, detail=f"Invalid interval: {interval}")

    today = date.today()
    end = end or today
    start = start or (end - timedelta(days=30))

    if start > end:
        raise HTTPException(status_code=400, detail="start must be before end")

    start_ms = to_ms(datetime(start.year, start.month, start.day, tzinfo=timezone.utc))
    end_ms = to_ms(datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc))

    try:
        raw = await fetch_klines(symbol, interval, start_ms, end_ms)
    except BinanceClientError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    return {
        "symbol": symbol,
        "interval": interval,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "candles": [map_candle(c) for c in raw],
    }
