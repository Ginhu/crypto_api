from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes import backtest, health, market
from app.clients import mongo_client
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo_client.init_db(settings.mongo_uri)
    yield


app = FastAPI(title="CryptoAPI", version="0.1.0", lifespan=lifespan)

app.include_router(health.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
