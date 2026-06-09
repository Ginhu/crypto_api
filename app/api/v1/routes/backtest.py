import asyncio
import uuid
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.clients import mongo_client
from app.services.backtest_service import run_backtest
from app.services.market_service import VALID_INTERVALS
from app.strategies import REGISTRY

router = APIRouter(tags=["backtest"])


class BacktestRequest(BaseModel):
    symbol: str
    interval: str = "5m"
    start: date
    end: date
    strategies: list[str]


@router.post("/backtest", status_code=202)
async def submit_backtest(body: BacktestRequest):
    symbol = body.symbol.upper()
    if body.interval not in VALID_INTERVALS:
        raise HTTPException(status_code=400, detail=f"Invalid interval: {body.interval}")
    if body.start > body.end:
        raise HTTPException(status_code=400, detail="start must be before end")
    unknown = [s for s in body.strategies if s not in REGISTRY]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown strategies: {unknown}")

    job_id = str(uuid.uuid4())
    await mongo_client.create_job({
        "job_id": job_id,
        "status": "pending",
        "symbol": symbol,
        "interval": body.interval,
        "start": body.start.isoformat(),
        "end": body.end.isoformat(),
        "strategies": body.strategies,
    })
    asyncio.create_task(
        run_backtest(
            job_id, symbol, body.interval,
            body.start.isoformat(), body.end.isoformat(),
            body.strategies,
        )
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/backtest/{job_id}")
async def get_backtest(job_id: str):
    job = await mongo_client.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
