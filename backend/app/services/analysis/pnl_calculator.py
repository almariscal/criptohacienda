"""Lightweight inventory + PnL calculator based on normalized transactions."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from ...models import NormalizedTx


class PnlCalculator:
    """Tracking balances per location and naive PnL per asset."""

    def __init__(self) -> None:
        self.balances: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.pnl: Dict[str, float] = defaultdict(float)
        self.value_timeline: Dict[str, float] = {}
        self.asset_history: Dict[str, List[Dict[str, float]]] = defaultdict(list)
        self._asset_totals: Dict[str, float] = defaultdict(float)

    def process(self, transactions: List[NormalizedTx]) -> None:
        total_value = 0.0
        for tx in sorted(transactions, key=lambda item: item.timestamp):
            self.balances[tx.location][tx.asset] += tx.amount
            self._asset_totals[tx.asset] += tx.amount
            total_value = sum(self._asset_totals.values())
            self.value_timeline[tx.id] = total_value
            self.asset_history[tx.asset].append(
                {"timestamp": tx.timestamp, "balance": self._asset_totals[tx.asset]}
            )
            if tx.type == "trade":
                self.pnl[tx.asset] -= tx.fee
            if tx.type in {"withdrawal", "transfer_out"}:
                self.pnl[tx.asset] -= abs(tx.amount)
            elif tx.type in {"deposit", "transfer_in"}:
                self.pnl[tx.asset] += abs(tx.amount)

    def summary(self) -> Dict[str, float]:
        return dict(self.pnl)

    def balances_by_location(self) -> Dict[str, Dict[str, float]]:
        return {loc: dict(assets) for loc, assets in self.balances.items()}

    def timeline(self) -> Dict[str, float]:
        return dict(self.value_timeline)

    def history(self) -> Dict[str, List[Dict[str, float]]]:
        return {asset: list(entries) for asset, entries in self.asset_history.items()}
