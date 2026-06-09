from motor.motor_asyncio import AsyncIOMotorClient

DB_NAME = "crypto_api"
COLLECTION_NAME = "market_data"

_client: AsyncIOMotorClient | None = None


async def init_db(uri: str) -> None:
    global _client
    _client = AsyncIOMotorClient(uri)
    try:
        await get_collection().create_index(
            [("symbol", 1), ("interval", 1)], unique=True
        )
    except Exception as e:
        print(f"Warning: could not create MongoDB index at startup: {e}")


def get_collection():
    return _client[DB_NAME][COLLECTION_NAME]


async def replace_dataset(document: dict) -> None:
    collection = get_collection()
    await collection.replace_one(
        {"symbol": document["symbol"], "interval": document["interval"]},
        document,
        upsert=True,
    )


JOBS_COLLECTION = "backtest_jobs"


async def create_job(job: dict) -> None:
    await _client[DB_NAME][JOBS_COLLECTION].insert_one(job)


async def update_job(job_id: str, update: dict) -> None:
    await _client[DB_NAME][JOBS_COLLECTION].update_one(
        {"job_id": job_id}, {"$set": update}
    )


async def get_job(job_id: str) -> dict | None:
    return await _client[DB_NAME][JOBS_COLLECTION].find_one(
        {"job_id": job_id}, {"_id": 0}
    )
