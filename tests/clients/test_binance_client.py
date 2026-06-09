import pytest
import respx
import httpx
from app.clients.binance_client import fetch_klines, BinanceClientError

FAKE_CANDLE = [
    1715299200000, "67000.00", "67450.00", "66800.00", "67200.00", "123.45",
    1715299499999, "456.78", 100, "50.00", "23.45", "0"
]

@pytest.mark.asyncio
@respx.mock
async def test_fetch_klines_single_page():
    respx.get("https://api.binance.com/api/v3/klines").mock(
        return_value=httpx.Response(200, json=[FAKE_CANDLE])
    )
    result = await fetch_klines("BTCUSDT", "5m", 1715299200000, 1715385600000)
    assert len(result) == 1
    assert result[0][1] == "67000.00"

@pytest.mark.asyncio
@respx.mock
async def test_fetch_klines_paginates():
    batch = [FAKE_CANDLE] * 1000

    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(200, json=batch)
        return httpx.Response(200, json=[FAKE_CANDLE])

    respx.get("https://api.binance.com/api/v3/klines").mock(side_effect=side_effect)
    result = await fetch_klines("BTCUSDT", "5m", 1715299200000, 1715385600000)
    assert call_count == 2
    assert len(result) == 1001

@pytest.mark.asyncio
@respx.mock
async def test_fetch_klines_binance_400_raises_client_error():
    respx.get("https://api.binance.com/api/v3/klines").mock(
        return_value=httpx.Response(400, json={"msg": "Invalid symbol."})
    )
    with pytest.raises(BinanceClientError) as exc:
        await fetch_klines("INVALID", "5m", 1715299200000, 1715385600000)
    assert exc.value.status_code == 400
    assert "Invalid symbol." in str(exc.value)

@pytest.mark.asyncio
@respx.mock
async def test_fetch_klines_binance_500_raises_502():
    respx.get("https://api.binance.com/api/v3/klines").mock(
        return_value=httpx.Response(500, json={})
    )
    with pytest.raises(BinanceClientError) as exc:
        await fetch_klines("BTCUSDT", "5m", 1715299200000, 1715385600000)
    assert exc.value.status_code == 502
