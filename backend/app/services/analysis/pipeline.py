"""Unified on/off chain analysis workflow."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List

from ...models import NormalizedTx
from ...schemas import AssetBreakdown, AssetLedgerEntry
from .importers.binance_csv_importer import import_binance_transactions
from .importers.btc_importer import import_btc_addresses
from .importers.evm_importer import import_evm_addresses
from .reconciler import reconcile_internal_transfers
from .pnl_calculator import PnlCalculator
from ...schemas import AssetBreakdown, AssetLedgerEntry


def _ensure_list(values: Iterable[str]) -> List[str]:
    return [value.strip() for value in values if value and value.strip()]


def run_combined_analysis(
    binance_csv: bytes | None,
    btc_addresses: Iterable[str],
    evm_addresses: Iterable[str],
    chains: Iterable[str],
) -> dict:
    csv_text = binance_csv.decode("utf-8") if binance_csv else ""
    binance_txs = import_binance_transactions(csv_text)
    btc_txs = import_btc_addresses(_ensure_list(btc_addresses))
    evm_txs = import_evm_addresses(_ensure_list(evm_addresses), _ensure_list(chains))

    unified: List[NormalizedTx] = binance_txs + btc_txs + evm_txs
    unified.sort(key=lambda tx: tx.timestamp)
    reconcile_internal_transfers(unified)

    calculator = PnlCalculator()
    calculator.process(unified)
    breakdown = _build_asset_breakdown(unified)

    return {
        "normalizedTxs": [tx.__dict__ for tx in unified],
        "pnlSummary": calculator.summary(),
        "balancesByLocation": calculator.balances_by_location(),
        "operationsTimeline": [tx.__dict__ for tx in unified],
        "valueTimeline": calculator.timeline(),
        "assetHistory": calculator.history(),
        "assetBreakdown": breakdown,
    }


def _build_asset_breakdown(transactions: List[NormalizedTx]) -> List[AssetBreakdown]:
    entries: dict[str, list[AssetLedgerEntry]] = defaultdict(list)
    totals: dict[str, dict[str, float]] = defaultdict(lambda: {"in": 0.0, "out": 0.0, "fees": 0.0})

    for tx in transactions:
        ledger_entry = AssetLedgerEntry(
            id=tx.id,
            timestamp=tx.timestamp,
            location=tx.location,
            type=tx.type,
            amount=tx.amount,
            fee=tx.fee,
            fee_asset=tx.fee_asset,
            source_system=tx.source_system,
            raw=tx.raw,
        )
        entries[tx.asset].append(ledger_entry)
        if tx.amount > 0:
            totals[tx.asset]["in"] += tx.amount
        else:
            totals[tx.asset]["out"] += abs(tx.amount)
        totals[tx.asset]["fees"] += tx.fee

    breakdown: List[AssetBreakdown] = []
    for asset, ledger_entries in entries.items():
        data = totals[asset]
        breakdown.append(
            AssetBreakdown(
                asset=asset,
                total_in=data["in"],
                total_out=data["out"],
                net_amount=data["in"] - data["out"],
                fees_paid=data["fees"],
                entries=ledger_entries,
            )
        )
    breakdown.sort(key=lambda item: item.asset)
    return breakdown
