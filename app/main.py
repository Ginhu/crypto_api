from fastapi import FastAPI
from app.api.v1.routes import health, market

app = FastAPI(title="CryptoAPI", version="0.1.0")

app.include_router(health.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
