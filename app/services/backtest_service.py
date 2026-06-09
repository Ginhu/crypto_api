import asyncio
import statistics
from datetime import datetime, timezone

from app.clients import mongo_client
from app.clients.binance_client import fetch_klines
from app.services.market_service import map_candle, save_dataset, to_ms
from app.strategies import REGISTRY
from app.strategies.base import Trade


def _compute_metrics(trades: list[Trade]) -> dict:
    if not trades:
        return {
            "total_return_pct": 0.0,
            "win_rate_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
            "num_trades": 0,
        }

    returns = [(t.exit_price - t.entry_price) / t.entry_price for t in trades]
    total_return_pct = round(sum(returns) * 100, 2)
    win_rate_pct = round(sum(1 for r in returns if r > 0) / len(trades) * 100, 2)

    equity, peak, max_dd = 1.0, 1.0, 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        dd = (equity - peak) / peak
        max_dd = min(max_dd, dd)
    max_drawdown_pct = round(max_dd * 100, 2)

    if len(returns) < 2:
        sharpe = 0.0
    else:
        mean_r = statistics.mean(returns)
        std_r = statistics.stdev(returns)
        sharpe = round((mean_r / std_r * 252 ** 0.5) if std_r > 0 else 0.0, 4)

    return {
        "total_return_pct": total_return_pct,
        "win_rate_pct": win_rate_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "sharpe_ratio": sharpe,
        "num_trades": len(trades),
    }


async def _get_candles(symbol: str, interval: str, start: str, end: str) -> list[dict]:
    collection = mongo_client.get_collection()
    doc = await collection.find_one({"symbol": symbol, "interval": interval})

    if doc and doc.get("start", "") <= start and doc.get("end", "") >= end:
        return [
            c for c in doc["candles"]
            if c["open_time"][:10] >= start and c["open_time"][:10] <= end
        ]

    start_dt = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_ms = to_ms(start_dt)
    end_ms = to_ms(datetime(end_dt.year, end_dt.month, end_dt.day, 23, 59, 59, tzinfo=timezone.utc))

    raw = await fetch_klines(symbol, interval, start_ms, end_ms)
    candles = [map_candle(c) for c in raw]
    await save_dataset(symbol, interval, start, end, candles)
    return candles


async def _run_one_strategy(name: str, candles: list[dict]) -> dict:
    fn = REGISTRY[name]
    trades = await asyncio.to_thread(fn, candles)
    return {"strategy": name, **_compute_metrics(trades)}


async def run_backtest(
    job_id: str,
    symbol: str,
    interval: str,
    start: str,
    end: str,
    strategy_names: list[str],
) -> None:
    await mongo_client.update_job(job_id, {"status": "running"})
    try:
        candles = await _get_candles(symbol, interval, start, end)
        if not candles:
            raise ValueError(f"No candles for {symbol} {interval} {start}..{end}")
        results = await asyncio.gather(
            *[_run_one_strategy(name, candles) for name in strategy_names]
        )
        await mongo_client.update_job(
            job_id, {"status": "completed", "results": list(results)}
        )
    except Exception as exc:
        await mongo_client.update_job(job_id, {"status": "failed", "error": str(exc)})
