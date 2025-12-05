from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional

from .models import (
    CashMovement,
    Operation,
    OperationView,
    PortfolioSnapshot,
    RealizedGain,
    SessionData,
)
from .runtime_paths import get_data_dir

logger = logging.getLogger(__name__)


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _serialize_date(value: date) -> str:
    return value.isoformat()


def _operation_to_dict(op: Operation) -> dict:
    return {
        "timestamp": _serialize_datetime(op.timestamp),
        "base_asset": op.base_asset,
        "quote_asset": op.quote_asset,
        "side": op.side,
        "price": op.price,
        "amount": op.amount,
        "quote_amount": op.quote_amount,
        "fee_amount": op.fee_amount,
        "fee_asset": op.fee_asset,
    }


def _operation_from_dict(payload: dict) -> Operation:
    return Operation(
        timestamp=datetime.fromisoformat(payload["timestamp"]),
        base_asset=payload["base_asset"],
        quote_asset=payload["quote_asset"],
        side=payload["side"],
        price=payload["price"],
        amount=payload["amount"],
        quote_amount=payload["quote_amount"],
        fee_amount=payload.get("fee_amount", 0.0),
        fee_asset=payload.get("fee_asset", "UNKNOWN"),
    )


def _realized_gain_to_dict(gain: RealizedGain) -> dict:
    return {
        "timestamp": _serialize_datetime(gain.timestamp),
        "asset": gain.asset,
        "quantity": gain.quantity,
        "proceeds_eur": gain.proceeds_eur,
        "cost_basis_eur": gain.cost_basis_eur,
        "fees_eur": gain.fees_eur,
        "gain_eur": gain.gain_eur,
        "note": gain.note,
    }


def _realized_gain_from_dict(payload: dict) -> RealizedGain:
    return RealizedGain(
        timestamp=datetime.fromisoformat(payload["timestamp"]),
        asset=payload["asset"],
        quantity=payload["quantity"],
        proceeds_eur=payload["proceeds_eur"],
        cost_basis_eur=payload["cost_basis_eur"],
        fees_eur=payload["fees_eur"],
        gain_eur=payload["gain_eur"],
        note=payload.get("note", ""),
    )


def _cash_movement_to_dict(movement: CashMovement) -> dict:
    return {
        "timestamp": _serialize_datetime(movement.timestamp),
        "asset": movement.asset,
        "amount": movement.amount,
        "type": movement.type,
        "origin": movement.origin,
    }


def _cash_movement_from_dict(payload: dict) -> CashMovement:
    return CashMovement(
        timestamp=datetime.fromisoformat(payload["timestamp"]),
        asset=payload["asset"],
        amount=payload["amount"],
        type=payload["type"],
        origin=payload.get("origin", ""),
    )


def _operation_view_to_dict(view: OperationView) -> dict:
    return {
        "id": view.id,
        "date": _serialize_date(view.date),
        "asset": view.asset,
        "type": view.type,
        "amount": view.amount,
        "price": view.price,
        "fee": view.fee,
        "total": view.total,
    }


def _operation_view_from_dict(payload: dict) -> OperationView:
    return OperationView(
        id=payload["id"],
        date=date.fromisoformat(payload["date"]),
        asset=payload["asset"],
        type=payload["type"],
        amount=payload["amount"],
        price=payload["price"],
        fee=payload.get("fee"),
        total=payload.get("total"),
    )


def _portfolio_snapshot_to_dict(snapshot: PortfolioSnapshot) -> dict:
    return {
        "timestamp": _serialize_datetime(snapshot.timestamp),
        "total_value": snapshot.total_value,
        "asset_values": snapshot.asset_values,
        "asset_quantities": snapshot.asset_quantities,
        "total_deposited_eur": snapshot.total_deposited_eur,
        "total_withdrawn_eur": snapshot.total_withdrawn_eur,
    }


def _portfolio_snapshot_from_dict(payload: dict) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        timestamp=datetime.fromisoformat(payload["timestamp"]),
        total_value=payload["total_value"],
        asset_values=payload.get("asset_values", {}),
        asset_quantities=payload.get("asset_quantities", {}),
        total_deposited_eur=payload.get("total_deposited_eur", 0.0),
        total_withdrawn_eur=payload.get("total_withdrawn_eur", 0.0),
    )


def _session_to_payload(session: SessionData) -> dict:
    return {
        "operations": [_operation_to_dict(op) for op in session.operations],
        "realized_gains": [_realized_gain_to_dict(item) for item in session.realized_gains],
        "holdings": session.holdings,
        "operation_views": [_operation_view_to_dict(op) for op in session.operation_views],
        "total_invested_eur": session.total_invested_eur,
        "total_fees_eur": session.total_fees_eur,
        "cash_movements": [_cash_movement_to_dict(item) for item in session.cash_movements],
        "total_deposited_eur": session.total_deposited_eur,
        "total_withdrawn_eur": session.total_withdrawn_eur,
        "portfolio_snapshots": [_portfolio_snapshot_to_dict(item) for item in session.portfolio_snapshots],
        "missing_prices": session.missing_prices,
    }


def _session_from_payload(payload: dict) -> SessionData:
    return SessionData(
        operations=[_operation_from_dict(item) for item in payload.get("operations", [])],
        realized_gains=[_realized_gain_from_dict(item) for item in payload.get("realized_gains", [])],
        holdings=payload.get("holdings", {}),
        operation_views=[_operation_view_from_dict(item) for item in payload.get("operation_views", [])],
        total_invested_eur=payload.get("total_invested_eur", 0.0),
        total_fees_eur=payload.get("total_fees_eur", 0.0),
        cash_movements=[_cash_movement_from_dict(item) for item in payload.get("cash_movements", [])],
        total_deposited_eur=payload.get("total_deposited_eur", 0.0),
        total_withdrawn_eur=payload.get("total_withdrawn_eur", 0.0),
        portfolio_snapshots=[
            _portfolio_snapshot_from_dict(item) for item in payload.get("portfolio_snapshots", [])
        ],
        missing_prices=payload.get("missing_prices", []),
    )


class SessionStore:
    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._sessions: Dict[str, SessionData] = {}
        self._lock = threading.Lock()
        data_dir = storage_dir or get_data_dir()
        self._sessions_dir = data_dir / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        safe_id = session_id.replace("/", "_")
        return self._sessions_dir / f"{safe_id}.json"

    def _write_to_disk(self, session_id: str, data: SessionData) -> None:
        file_path = self._session_file(session_id)
        payload = _session_to_payload(data)
        tmp_path = file_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp_path.replace(file_path)

    def _load_from_disk(self, session_id: str) -> Optional[SessionData]:
        file_path = self._session_file(session_id)
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            return _session_from_payload(payload)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            logger.warning("Session file %s is corrupted; ignoring", file_path)
            return None
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error loading session %s", session_id)
            return None

    def set(self, session_id: str, data: SessionData) -> None:
        with self._lock:
            self._sessions[session_id] = data
        self._write_to_disk(session_id, data)

    def get(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            data = self._sessions.get(session_id)
        if data:
            return data
        loaded = self._load_from_disk(session_id)
        if loaded:
            with self._lock:
                self._sessions[session_id] = loaded
        return loaded

    def delete(self, session_id: str) -> bool:
        removed = False
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                removed = True
        file_path = self._session_file(session_id)
        try:
            file_path.unlink()
            removed = True
        except FileNotFoundError:
            pass
        return removed

    def exists(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                return True
        return self._session_file(session_id).exists()


session_store = SessionStore()
