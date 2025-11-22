from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .models import SessionData
from .schemas import (
    GroupBy,
    HoldingsResponse,
    OperationsResponse,
    RealizedGainsResponse,
    SummaryItem,
    SummaryResponse,
    UploadResponse,
)
from .services import parser, pricing
from .services.tax_engine import TaxEngine
from .session_store import session_store

app = FastAPI(title="Cripto Hacienda Tax Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_session_or_404(session_id: str) -> SessionData:
    data = session_store.get(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data


def _group_label(dt: datetime, group_by: GroupBy) -> date:
    if group_by == "day":
        return dt.date()
    if group_by == "week":
        start_of_week = dt.date() - timedelta(days=dt.weekday())
        return start_of_week
    if group_by == "month":
        return dt.date().replace(day=1)
    if group_by == "year":
        return dt.date().replace(month=1, day=1)
    return dt.date()


@app.post("/api/upload/binance-csv", response_model=UploadResponse)
async def upload_binance_csv(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required")

    content = (await file.read()).decode("utf-8")
    try:
        operations = parser.parse_binance_csv(content)
    except parser.CSVFormatError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    engine = TaxEngine(pricing.get_price_eur)
    try:
        engine.process_operations(operations)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session_id = str(uuid4())
    session_store.set(
        session_id,
        SessionData(
            operations=operations,
            realized_gains=engine.realized_gains,
            holdings={asset: lots for asset, lots in engine.holdings.items()},
        ),
    )

    return UploadResponse(
        session_id=session_id,
        operations_count=len(operations),
        realized_gains_count=len(engine.realized_gains),
    )


@app.get("/api/sessions/{session_id}/operations", response_model=OperationsResponse)
async def list_operations(session_id: str) -> OperationsResponse:
    session = _get_session_or_404(session_id)
    return OperationsResponse(operations=session.operations)


@app.get("/api/sessions/{session_id}/realized-gains", response_model=RealizedGainsResponse)
async def list_realized_gains(session_id: str) -> RealizedGainsResponse:
    session = _get_session_or_404(session_id)
    return RealizedGainsResponse(realized_gains=session.realized_gains)


@app.get("/api/sessions/{session_id}/holdings", response_model=HoldingsResponse)
async def get_holdings(session_id: str) -> HoldingsResponse:
    session = _get_session_or_404(session_id)
    return HoldingsResponse(holdings=session.holdings)


@app.get("/api/sessions/{session_id}/summaries", response_model=SummaryResponse)
async def get_summaries(session_id: str, group_by: GroupBy = "year") -> SummaryResponse:
    session = _get_session_or_404(session_id)
    summary_map: dict[date, SummaryItem] = {}

    for gain in session.realized_gains:
        key = _group_label(gain.timestamp, group_by)
        if key not in summary_map:
            summary_map[key] = SummaryItem(
                period_start=key,
                proceeds_eur=0.0,
                cost_basis_eur=0.0,
                fees_eur=0.0,
                gain_eur=0.0,
            )
        item = summary_map[key]
        item.proceeds_eur += gain.proceeds_eur
        item.cost_basis_eur += gain.cost_basis_eur
        item.fees_eur += gain.fees_eur
        item.gain_eur += gain.gain_eur

    items = [summary_map[k] for k in sorted(summary_map.keys())]
    return SummaryResponse(group_by=group_by, items=items)


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    removed = session_store.delete(session_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}
