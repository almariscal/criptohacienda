import csv
from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from io import StringIO
from typing import Iterable, List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import CashMovement, Operation, OperationView, PortfolioSnapshot, RealizedGain, SessionData
from .schemas import (
    DashboardGainPoint,
    DashboardHolding,
    DashboardOperation,
    DashboardResponse,
    DashboardSummary,
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


def _fee_eur(amount: float, asset: str, timestamp: datetime) -> float:
    if amount <= 0 or not asset or asset.upper() == "UNKNOWN":
        return 0.0
    return amount * pricing.get_price_eur(asset, timestamp)


def _build_operation_views(operations: List[Operation]) -> tuple[List[OperationView], float, float]:
    views: List[OperationView] = []
    total_invested = 0.0
    total_fees = 0.0

    for idx, op in enumerate(sorted(operations, key=lambda o: o.timestamp)):
        quote_rate = pricing.get_price_eur(op.quote_asset, op.timestamp)
        price_eur = op.price * quote_rate
        total_eur = op.quote_amount * quote_rate
        fee_eur = _fee_eur(op.fee_amount, op.fee_asset, op.timestamp)
        op_type = op.side.upper()

        views.append(
            OperationView(
                id=f"{idx}-{int(op.timestamp.timestamp())}",
                date=op.timestamp.date(),
                asset=op.base_asset.upper(),
                type=op_type,
                amount=op.amount,
                price=price_eur,
                fee=fee_eur or None,
                total=total_eur,
            )
        )

        if op_type == "BUY":
            if op.fee_asset.upper() == op.base_asset.upper():
                total_invested += total_eur + fee_eur
            else:
                total_invested += total_eur
        total_fees += fee_eur

    return views, total_invested, total_fees


def _filter_operation_views(
    operations: Iterable[OperationView],
    start_date: Optional[date],
    end_date: Optional[date],
    asset: Optional[str],
    type_filter: Optional[str],
) -> List[OperationView]:
    asset_filter = asset.upper() if asset else None
    type_value = type_filter.upper() if type_filter else None
    filtered: List[OperationView] = []
    for op in operations:
        if start_date and op.date < start_date:
            continue
        if end_date and op.date > end_date:
            continue
        if asset_filter and op.asset.upper() != asset_filter:
            continue
        if type_value and op.type != type_value:
            continue
        filtered.append(op)
    return filtered


def _filter_realized_gains(
    gains: Iterable[RealizedGain], start_date: Optional[date], end_date: Optional[date], asset: Optional[str]
) -> List[RealizedGain]:
    asset_filter = asset.upper() if asset else None
    filtered: List[RealizedGain] = []
    for gain in gains:
        gain_date = gain.timestamp.date()
        if start_date and gain_date < start_date:
            continue
        if end_date and gain_date > end_date:
            continue
        if asset_filter and gain.asset.upper() != asset_filter:
            continue
        filtered.append(gain)
    return filtered


def _format_period_label(period_start: date, group_by: GroupBy) -> str:
    if group_by == "week":
        year, week, _ = period_start.isocalendar()
        return f"{year}-W{week:02d}"
    if group_by == "month":
        return period_start.strftime("%Y-%m")
    if group_by == "year":
        return str(period_start.year)
    return period_start.isoformat()


def _build_gain_points(gains: Iterable[RealizedGain], group_by: GroupBy) -> List[DashboardGainPoint]:
    buckets: dict[str, float] = {}
    for gain in gains:
        period_start = _group_label(gain.timestamp, group_by)
        label = _format_period_label(period_start, group_by)
        buckets[label] = buckets.get(label, 0.0) + gain.gain_eur

    return [
        DashboardGainPoint(period=period, gain=buckets[period])
        for period in sorted(buckets.keys())
    ]


def _serialize_operations(operations: Iterable[OperationView]) -> List[DashboardOperation]:
    return [
        DashboardOperation(
            id=op.id,
            date=op.date,
            asset=op.asset,
            type=op.type,
            amount=op.amount,
            price=op.price,
            fee=op.fee,
            total=op.total,
        )
        for op in operations
    ]


def _build_portfolio_snapshots(
    operations: List[Operation],
    cash_movements: List[CashMovement],
) -> List[PortfolioSnapshot]:
    events: List[tuple[str, datetime, int, object]] = []
    for idx, op in enumerate(sorted(operations, key=lambda item: item.timestamp)):
        events.append(("operation", op.timestamp, idx, op))
    offset = len(events)
    for idx, movement in enumerate(sorted(cash_movements, key=lambda item: item.timestamp)):
        events.append(("cash", movement.timestamp, offset + idx, movement))

    events.sort(key=lambda item: (item[1], 0 if item[0] == "cash" else 1, item[2]))

    balances: dict[str, float] = defaultdict(float)
    price_cache: dict[tuple[str, str], float] = {}
    snapshots: List[PortfolioSnapshot] = []

    for event_type, timestamp, _, payload in events:
        if event_type == "operation":
            _apply_operation_to_balances(balances, payload)  # type: ignore[arg-type]
        else:
            _apply_cash_movement_to_balances(balances, payload)  # type: ignore[arg-type]
        snapshots.append(_snapshot_from_balances(balances, timestamp, price_cache))

    return snapshots


def _apply_operation_to_balances(balances: dict[str, float], operation: Operation) -> None:
    base = operation.base_asset.upper()
    quote = operation.quote_asset.upper()
    fee_asset = operation.fee_asset.upper() if operation.fee_asset else "UNKNOWN"

    if operation.side == "BUY":
        balances[base] += operation.amount
        balances[quote] -= operation.quote_amount
    else:
        balances[base] -= operation.amount
        balances[quote] += operation.quote_amount

    if operation.fee_amount and fee_asset != "UNKNOWN":
        balances[fee_asset] -= operation.fee_amount

    _clean_balance(balances, base)
    _clean_balance(balances, quote)
    if fee_asset != "UNKNOWN":
        _clean_balance(balances, fee_asset)


def _apply_cash_movement_to_balances(balances: dict[str, float], movement: CashMovement) -> None:
    asset = movement.asset.upper()
    delta = movement.amount if movement.type == "deposit" else -movement.amount
    balances[asset] += delta
    _clean_balance(balances, asset)


def _clean_balance(balances: dict[str, float], asset: str) -> None:
    if abs(balances.get(asset, 0.0)) <= 1e-9:
        balances.pop(asset, None)


def _snapshot_from_balances(
    balances: dict[str, float],
    timestamp: datetime,
    price_cache: dict[tuple[str, str], float],
) -> PortfolioSnapshot:
    asset_quantities: dict[str, float] = {}
    asset_values: dict[str, float] = {}
    total_value = 0.0
    for asset, quantity in balances.items():
        if quantity <= 0:
            continue
        asset_key = asset.upper()
        asset_quantities[asset_key] = quantity
        price = 1.0 if asset_key == "EUR" else _price_with_cache(asset_key, timestamp, price_cache)
        value = quantity * price
        asset_values[asset_key] = value
        total_value += value

    return PortfolioSnapshot(timestamp=timestamp, total_value=total_value, asset_values=asset_values, asset_quantities=asset_quantities)


def _price_with_cache(asset: str, timestamp: datetime, cache: dict[tuple[str, str], float]) -> float:
    date_key = timestamp.strftime("%d-%m-%Y")
    cache_key = (asset.upper(), date_key)
    if cache_key not in cache:
        cache[cache_key] = pricing.get_price_eur(asset, timestamp)
    return cache[cache_key]


def _cash_total_eur(
    movements: Iterable[CashMovement],
    movement_type: Literal["deposit", "withdraw"],
    allowed_origins: set[str] | None = None,
) -> float:
    total = 0.0
    for movement in movements:
        if movement.type != movement_type:
            continue
        if allowed_origins and movement.origin not in allowed_origins:
            continue
        rate = pricing.get_price_eur(movement.asset, movement.timestamp)
        total += movement.amount * rate
    return total


def _summarize_holdings(
    session: SessionData,
    asset_filter: Optional[str],
) -> tuple[List[DashboardHolding], float, float]:
    if not session.portfolio_snapshots:
        return [], 0.0, 0.0

    latest = session.portfolio_snapshots[-1]
    asset_value = asset_filter.upper() if asset_filter else None
    now = datetime.utcnow()
    holdings: List[DashboardHolding] = []
    total_market_value = 0.0
    total_unrealized = 0.0

    for asset, quantity in latest.asset_quantities.items():
        asset_key = asset.upper()
        if quantity <= 0:
            continue
        if asset_value and asset_key != asset_value:
            continue
        price = 1.0 if asset_key == "EUR" else pricing.get_price_eur(asset_key, now)
        current_value = quantity * price
        cost_basis_total = _cost_basis_total(session.holdings, asset_key, quantity)
        average_price = cost_basis_total / quantity if quantity else 0.0

        total_market_value += current_value
        total_unrealized += current_value - cost_basis_total

        holdings.append(
            DashboardHolding(
                asset=asset_key,
                quantity=quantity,
                averagePrice=average_price,
                currentValue=current_value,
            )
        )

    holdings.sort(key=lambda item: item.asset)
    return holdings, total_market_value, total_unrealized


def _cost_basis_total(holdings_data: dict[str, List[dict[str, float]]], asset: str, quantity: float) -> float:
    lots = holdings_data.get(asset.upper(), [])
    total = sum(lot.get("amount", 0.0) * lot.get("cost_per_unit", 0.0) for lot in lots)
    total_amount = sum(lot.get("amount", 0.0) for lot in lots)
    if total_amount <= 0:
        if asset.upper() == "EUR":
            return quantity
        return 0.0
    if abs(total_amount - quantity) <= 1e-6:
        return total
    ratio = quantity / total_amount
    return total * ratio


def _ensure_operation_views(session: SessionData) -> None:
    if session.operation_views:
        return
    views, _, total_fees = _build_operation_views(session.operations)
    session.operation_views = views
    session.total_fees_eur = total_fees


@app.post("/api/upload/binance-csv", response_model=UploadResponse)
async def upload_binance_csv(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required")

    content = (await file.read()).decode("utf-8")
    try:
        operations, cash_movements = parser.parse_binance_csv(content)
    except parser.CSVFormatError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    engine = TaxEngine(pricing.get_price_eur)
    try:
        engine.process_operations(operations)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        operation_views, total_invested, total_fees = _build_operation_views(operations)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        total_deposited = _cash_total_eur(cash_movements, "deposit", allowed_origins={"deposit"})
        total_withdrawn = _cash_total_eur(cash_movements, "withdraw")
        portfolio_snapshots = _build_portfolio_snapshots(operations, cash_movements)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    session_id = str(uuid4())
    session_store.set(
        session_id,
        SessionData(
            operations=operations,
            realized_gains=engine.realized_gains,
            holdings={asset: lots for asset, lots in engine.holdings.items()},
            operation_views=operation_views,
            total_invested_eur=total_deposited,
            total_fees_eur=total_fees,
            cash_movements=cash_movements,
            total_deposited_eur=total_deposited,
            total_withdrawn_eur=total_withdrawn,
            portfolio_snapshots=portfolio_snapshots,
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


@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    session_id: str = Query(..., alias="session_id"),
    group_by: GroupBy = Query("month", alias="group_by"),
    start_date: date | None = Query(None, alias="start_date"),
    end_date: date | None = Query(None, alias="end_date"),
    asset: str | None = Query(None, alias="asset"),
    type_filter: str | None = Query(None, alias="type"),
) -> DashboardResponse:
    session = _get_session_or_404(session_id)
    try:
        _ensure_operation_views(session)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    filtered_operations = _filter_operation_views(
        session.operation_views, start_date, end_date, asset, type_filter
    )
    filtered_realized = _filter_realized_gains(session.realized_gains, start_date, end_date, asset)
    gain_points = _build_gain_points(filtered_realized, group_by)
    try:
        holdings, current_balance, unrealized_gains = _summarize_holdings(session, asset)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    summary = DashboardSummary(
        totalInvested=session.total_deposited_eur,
        totalWithdrawn=session.total_withdrawn_eur,
        currentBalance=current_balance,
        totalFees=session.total_fees_eur,
        realizedGains=sum(gain.gain_eur for gain in session.realized_gains),
        unrealizedGains=unrealized_gains,
    )

    operations_payload = _serialize_operations(filtered_operations)
    portfolio_history = [
        {
            "timestamp": snapshot.timestamp,
            "totalValue": snapshot.total_value,
            "assetValues": snapshot.asset_values,
        }
        for snapshot in session.portfolio_snapshots
    ]
    return DashboardResponse(
        summary=summary,
        gains=gain_points,
        operations=operations_payload,
        holdings=holdings,
        portfolioHistory=portfolio_history,
    )


@app.get("/api/export/operations")
async def export_operations(
    session_id: str = Query(..., alias="session_id"),
    start_date: date | None = Query(None, alias="start_date"),
    end_date: date | None = Query(None, alias="end_date"),
    asset: str | None = Query(None, alias="asset"),
    type_filter: str | None = Query(None, alias="type"),
) -> StreamingResponse:
    session = _get_session_or_404(session_id)
    try:
        _ensure_operation_views(session)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    filtered_operations = _filter_operation_views(
        session.operation_views, start_date, end_date, asset, type_filter
    )

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["date", "asset", "type", "amount", "price_eur", "fee_eur", "total_eur"],
    )
    writer.writeheader()
    for op in filtered_operations:
        writer.writerow(
            {
                "date": op.date.isoformat(),
                "asset": op.asset,
                "type": op.type,
                "amount": op.amount,
                "price_eur": op.price,
                "fee_eur": op.fee or 0.0,
                "total_eur": op.total or 0.0,
            }
        )

    output.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="operations.csv"'}
    return StreamingResponse(iter([output.getvalue().encode("utf-8")]), media_type="text/csv", headers=headers)


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    removed = session_store.delete(session_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}
