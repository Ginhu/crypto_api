import pytest
from unittest.mock import AsyncMock, patch
from app.clients.mongo_client import replace_dataset


@pytest.mark.asyncio
async def test_replace_dataset_calls_replace_one_with_correct_filter():
    document = {
        "symbol": "BTCUSDT",
        "interval": "5m",
        "start": "2026-05-10",
        "end": "2026-06-09",
        "fetched_at": "2026-06-09T12:00:00Z",
        "candles": [],
    }
    mock_collection = AsyncMock()
    with patch("app.clients.mongo_client.get_collection", return_value=mock_collection):
        await replace_dataset(document)
    mock_collection.replace_one.assert_called_once_with(
        {"symbol": "BTCUSDT", "interval": "5m"},
        document,
        upsert=True,
    )


@pytest.mark.asyncio
async def test_replace_dataset_propagates_motor_exceptions():
    mock_collection = AsyncMock()
    mock_collection.replace_one.side_effect = Exception("connection refused")
    with patch("app.clients.mongo_client.get_collection", return_value=mock_collection):
        with pytest.raises(Exception, match="connection refused"):
            await replace_dataset({"symbol": "BTCUSDT", "interval": "5m", "candles": []})
