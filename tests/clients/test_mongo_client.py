import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.clients.mongo_client import replace_dataset
from app.clients import mongo_client


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


# --- Backtest job helpers ---


@pytest.mark.asyncio
async def test_create_job_inserts_document():
    mock_collection = AsyncMock()
    with patch("app.clients.mongo_client._client") as mock_client:
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        await mongo_client.create_job({"job_id": "abc", "status": "pending"})
    mock_collection.insert_one.assert_called_once_with({"job_id": "abc", "status": "pending"})


@pytest.mark.asyncio
async def test_update_job_sets_fields():
    mock_collection = AsyncMock()
    with patch("app.clients.mongo_client._client") as mock_client:
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        await mongo_client.update_job("abc", {"status": "running"})
    mock_collection.update_one.assert_called_once_with(
        {"job_id": "abc"}, {"$set": {"status": "running"}}
    )


@pytest.mark.asyncio
async def test_get_job_returns_document():
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {"job_id": "abc", "status": "completed"}
    with patch("app.clients.mongo_client._client") as mock_client:
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        result = await mongo_client.get_job("abc")
    assert result == {"job_id": "abc", "status": "completed"}
    mock_collection.find_one.assert_called_once_with({"job_id": "abc"}, {"_id": 0})


@pytest.mark.asyncio
async def test_get_job_returns_none_when_not_found():
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = None
    with patch("app.clients.mongo_client._client") as mock_client:
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        result = await mongo_client.get_job("nonexistent")
    assert result is None
