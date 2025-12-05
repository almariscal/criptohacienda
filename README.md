# Cripto Hacienda

Cripto Hacienda is a small two-service app that parses Binance trade exports, calculates realized gains, and visualizes the results in a simple dashboard.

## Architecture

- **Backend (FastAPI)**: Handles CSV ingestion, parses Binance trade history, calculates holdings and realized gains with the tax engine, and exposes session-based APIs. Key parts include:
  - `app/main.py` with the FastAPI routes for uploads, session data, summaries, and deletion.
  - `app/services/parser.py` which validates Binance CSV headers and converts rows into operations.
  - `app/services/tax_engine.py` for FIFO-style lot accounting and gain calculation, powered by the CoinGecko-backed price service in `app/services/pricing.py`.
  - `app/session_store.py` keeps uploaded sessions in-memory.
- **Frontend (Vite + React + TypeScript)**: Provides a CSV upload screen and a dashboard with charts, summary cards, holdings, filters, and CSV export. Components live under `frontend/src` with routing set up in `App.tsx`.
- **Desktop shell (Electron)**: Lives under `desktop/` and bundles the compiled frontend together with a packaged backend binary. It spawns the backend service automatically, exposes it on `http://127.0.0.1:8000`, and wraps the UI so it can be distributed as an AppImage or Windows installer.
- **Containerization**: `docker-compose.yml` builds separate backend and frontend images and wires them together on a shared bridge network.
- **Data directory**: Runtime sessions are now persisted under `data/` (or any folder you point `CRIPTOHACIENDA_DATA_DIR` to), so processed uploads survive restarts across Docker, desktop builds, and local development.

## Running with Docker Compose

1. Ensure Docker is available locally.
2. From the repository root, run:
   ```bash
   docker-compose up --build
   ```
   - Backend: http://localhost:8000 (FastAPI docs at http://localhost:8000/docs)
   - Frontend: http://localhost:3000 (configured to talk to the backend service via `VITE_API_BASE_URL`)
3. Press `Ctrl+C` to stop; containers are named `criptohacienda-backend` and `criptohacienda-frontend` if you need to clean up.

The backend writes session data to `./data` on the host by default. Mount a different folder by setting `CRIPTOHACIENDA_DATA_DIR` on the backend service.

## Data persistence outside Docker

- During local development (running `uvicorn` manually), session JSON files are written to `<repo>/data/sessions`. Override the location with `CRIPTOHACIENDA_DATA_DIR=/path/to/storage`.
- Desktop binaries (AppImage or `.exe`) attempt to write next to the executable in a folder named `criptohacienda-data`. If that path is read-only, the app falls back to the OS user data directory.
- You can safely back up or delete individual session files under `data/sessions` to manage disk usage.

## Desktop builds (AppImage / Windows .exe)

The `desktop/` folder wraps the project with Electron so it can run without Docker. The shell builds the frontend, launches the backend automatically, and exposes the FastAPI server on `http://127.0.0.1:8000` for the bundled UI.

### 1. Quick scripts

- **Linux AppImage** (requires `pyinstaller`, Node/npm, and AppImage toolchain):
  ```bash
  ./scripts/build-appimage.sh
  ```
  This script compila el backend con PyInstaller, sincroniza el frontend y ejecuta `npm run build:linux`. El archivo `.AppImage` queda en `desktop/dist/`.

- **Windows installer** (run in PowerShell with PyInstaller + Node + NSIS in PATH):
  ```powershell
  pwsh ./scripts/build-windows.ps1
  ```
  Genera `desktop/dist/CriptoHacienda-Setup-<version>.exe`. Usa `-PyInstaller C:\ruta\pyinstaller.exe` si tu binario se llama distinto.

### 2. Manual build steps (si prefieres ejecutarlos uno por uno)

1. **Backend binary**  
   ```bash
   pyinstaller backend/desktop_main.py \
     --name criptohacienda-backend \
     --onefile \
     --distpath desktop/resources/backend \
     --workpath backend/.pyinstaller-build \
     --clean
   ```
2. **Frontend assets**  
   ```bash
   cd desktop
   npm install
   npm run sync:frontend   # Copia frontend/dist a desktop/resources/ui
   ```
3. **Electron package**
   - Linux: `npm run build:linux`
   - Windows: `npm run build:windows`

### 3. Running the desktop app locally

For quick local testing without installers:

```bash
cd desktop
npm run dev
```

This command rebuilds the frontend, starts the backend with your system Python (`python -m backend.desktop_main`), and opens the Electron window. The backend persists sessions in the same `data/` folder as the CLI/docker workflows unless you override `CRIPTOHACIENDA_DATA_DIR`.

## API Endpoints

Backend routes are session-oriented; upload a CSV first to obtain a `session_id`.

- `POST /api/upload/binance-csv` — Upload a Binance CSV. Returns `{ session_id, operations_count, realized_gains_count }`.
- `GET /api/sessions/{session_id}/operations` — List parsed operations for the session.
- `GET /api/sessions/{session_id}/realized-gains` — List realized gains calculated by the tax engine.
- `GET /api/sessions/{session_id}/holdings` — Current FIFO lots per asset.
- `GET /api/sessions/{session_id}/summaries?group_by=day|week|month|year` — Aggregated proceeds, cost basis, fees, and gains per period (defaults to yearly).
- `GET /api/dashboard?session_id=...` — Convenience endpoint that bundles summary cards, gains series, holdings, and operations already converted a EUR. Supports optional `group_by`, `start_date`, `end_date`, `asset`, and `type` filters (the same filters used in la UI).
- `GET /api/export/operations?session_id=...` — Exports the filtered operations shown in the dashboard table as CSV using the same filter set as `/api/dashboard`.
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
