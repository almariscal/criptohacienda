# Cripto Hacienda

Cripto Hacienda is a small two-service app that parses Binance trade exports, calculates realized gains, and visualizes the results in a simple dashboard.

## Architecture

- **Backend (FastAPI)**: Handles CSV ingestion, parses Binance trade history, calculates holdings and realized gains with the tax engine, and exposes session-based APIs. Key parts include:
  - `app/main.py` with the FastAPI routes for uploads, session data, summaries, and deletion.
  - `app/services/parser.py` which validates Binance CSV headers and converts rows into operations.
  - `app/services/tax_engine.py` for FIFO-style lot accounting and gain calculation, powered by the CoinGecko-backed price service in `app/services/pricing.py`.
  - `app/session_store.py` keeps uploaded sessions in-memory.
- **Frontend (Vite + React + TypeScript)**: Provides a CSV upload screen and a dashboard with charts, summary cards, holdings, filters, and CSV export. Components live under `frontend/src` with routing set up in `App.tsx`.
- **Containerization**: `docker-compose.yml` builds separate backend and frontend images and wires them together on a shared bridge network.

## Running with Docker Compose

1. Ensure Docker is available locally.
2. From the repository root, run:
   ```bash
   docker-compose up --build
   ```
   - Backend: http://localhost:8000 (FastAPI docs at http://localhost:8000/docs)
   - Frontend: http://localhost:3000 (configured to talk to the backend service via `VITE_API_BASE_URL`)
3. Press `Ctrl+C` to stop; containers are named `criptohacienda-backend` and `criptohacienda-frontend` if you need to clean up.

## API Endpoints

Backend routes are session-oriented; upload a CSV first to obtain a `session_id`.

- `POST /api/upload/binance-csv` — Upload a Binance CSV. Returns `{ session_id, operations_count, realized_gains_count }`.
- `GET /api/sessions/{session_id}/operations` — List parsed operations for the session.
- `GET /api/sessions/{session_id}/realized-gains` — List realized gains calculated by the tax engine.
- `GET /api/sessions/{session_id}/holdings` — Current FIFO lots per asset.
- `GET /api/sessions/{session_id}/summaries?group_by=day|week|month|year` — Aggregated proceeds, cost basis, fees, and gains per period (defaults to yearly).
- `DELETE /api/sessions/{session_id}` — Drop a session and its cached data.

## Expected Binance CSV Format

The parser expects Binance trade exports with the following headers:

```
Date(UTC),Pair,Side,Price,Executed,Amount,Fee,Fee Asset
```

- `Pair` can be `BASE/QUOTE` (e.g., `BTC/EUR`) or concatenated symbols (e.g., `BTCEUR`, `BTCUSDT`).
- `Side` must be `BUY` or `SELL`.
- `Executed` is the base asset quantity; `Amount` is the quote amount (if missing, it is derived from `Price * Executed`).
- `Fee` and `Fee Asset` are optional; missing fees default to zero and an `UNKNOWN` asset placeholder.

Rows outside this shape or with unparsable pairs raise a `400` with a descriptive error.

## Using the UI

1. Open http://localhost:3000.
2. On **Subir CSV**, choose your Binance CSV export and upload it. On success, you are redirected to the dashboard with the new session.
3. In the **Dashboard**:
   - Review summary cards (invested capital, fees, realized/unrealized gains).
   - Explore the gains chart grouped by day, month, or year.
   - Filter the operations table by date range, asset, or type, and export the filtered set to CSV.
   - Inspect current holdings with average price and estimated EUR value.
4. To start over, delete the session via the backend API or upload another CSV to create a new session.
