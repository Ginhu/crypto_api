from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.clients.binance_client import BinanceClientError, fetch_klines
from app.services.market_service import VALID_INTERVALS, map_candle, save_dataset, to_ms

router = APIRouter(tags=["market"])


def _resolve_params(symbol, interval, start, end):
    symbol = symbol.upper()
    if interval not in VALID_INTERVALS:
        raise HTTPException(status_code=400, detail=f"Invalid interval: {interval}")
    today = date.today()
    end = end or today
    start = start or (end - timedelta(days=30))
    if start > end:
        raise HTTPException(status_code=400, detail="start must be before end")
    return symbol, start, end


@router.get("/market/{symbol}/klines")
async def get_klines(
    symbol: str,
    interval: str = Query(default="5m"),
    start: date = Query(default=None),
    end: date = Query(default=None),
):
    symbol, start, end = _resolve_params(symbol, interval, start, end)
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


@router.post("/market/{symbol}/klines")
async def save_klines(
    symbol: str,
    interval: str = Query(default="5m"),
    start: date = Query(default=None),
    end: date = Query(default=None),
):
    symbol, start, end = _resolve_params(symbol, interval, start, end)
    start_ms = to_ms(datetime(start.year, start.month, start.day, tzinfo=timezone.utc))
    end_ms = to_ms(datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc))

    try:
        raw = await fetch_klines(symbol, interval, start_ms, end_ms)
    except BinanceClientError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    candles = [map_candle(c) for c in raw]

    try:
        await save_dataset(symbol, interval, start.isoformat(), end.isoformat(), candles)
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

    return {
        "symbol": symbol,
        "interval": interval,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "candles_saved": len(candles),
    }
