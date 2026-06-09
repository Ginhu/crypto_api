# CryptoAPI

A Python REST API built with FastAPI for fetching crypto prices and market data, analysing past data to validate trading strategies, and automating trades via the Binance API.

## Stack

- **Python 3.11+**
- **FastAPI** — web framework
- **Uvicorn** — ASGI server
- **Pydantic Settings** — config management

## Project Structure

```
app/
├── main.py               # App entry point
├── core/
│   └── config.py         # Settings
└── api/
    └── v1/
        └── routes/
            └── health.py # Health check endpoint
```

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env

# Run dev server
uvicorn app.main:app --reload
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |

## Docs

Interactive API docs available at `http://localhost:8000/docs` when running locally.
