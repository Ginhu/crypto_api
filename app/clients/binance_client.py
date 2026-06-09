import httpx

BINANCE_BASE_URL = "https://api.binance.com"
KLINES_ENDPOINT = "/api/v3/klines"
MAX_LIMIT = 1000


class BinanceClientError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


async def fetch_klines(symbol: str, interval: str, start_ms: int, end_ms: int) -> list:
    candles = []
    current_start = start_ms

    async with httpx.AsyncClient() as client:
        while current_start < end_ms:
            response = await client.get(
                f"{BINANCE_BASE_URL}{KLINES_ENDPOINT}",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": current_start,
                    "endTime": end_ms,
                    "limit": MAX_LIMIT,
                },
            )
            if response.status_code == 400:
                msg = response.json().get("msg", "Bad request")
                raise BinanceClientError(msg, status_code=400)
            if response.status_code != 200:
                raise BinanceClientError("Binance API error", status_code=502)

            batch = response.json()
            if not batch:
                break

            candles.extend(batch)

            if len(batch) < MAX_LIMIT:
                break

            current_start = batch[-1][0] + 1

    return candles
