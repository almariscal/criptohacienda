from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, List

from ..models import Operation, RealizedGain

PriceService = Callable[[str, datetime], float]


class TaxEngine:
    def __init__(self, price_service: PriceService) -> None:
        self.price_service = price_service
        self.holdings: Dict[str, List[Dict[str, float]]] = defaultdict(list)
        self.realized_gains: List[RealizedGain] = []

    def _price_eur(self, asset: str, timestamp: datetime) -> float:
        return 1.0 if asset.upper() == "EUR" else self.price_service(asset, timestamp)

    def _fee_eur(self, fee_amount: float, fee_asset: str, timestamp: datetime) -> float:
        if fee_amount <= 0:
            return 0.0
        return fee_amount * self._price_eur(fee_asset, timestamp)

    def _consume_lots(self, asset: str, amount: float, timestamp: datetime) -> float:
        lots = self.holdings[asset]
        remaining = amount
        cost_total = 0.0

        while remaining > 1e-12 and lots:
            lot = lots[0]
            take = min(remaining, lot["amount"])
            cost_total += take * lot["cost_per_unit"]
            lot["amount"] -= take
            remaining -= take
            if lot["amount"] <= 1e-9:
                lots.pop(0)

        if remaining > 1e-9:
            market_cost = remaining * self._price_eur(asset, timestamp)
            cost_total += market_cost

        return cost_total

    def _add_lot(self, asset: str, amount: float, cost_per_unit: float) -> None:
        if amount <= 0:
            return
        self.holdings[asset].append({"amount": amount, "cost_per_unit": cost_per_unit})

    def _record_gain(
        self,
        timestamp: datetime,
        asset: str,
        quantity: float,
        proceeds_eur: float,
        cost_basis_eur: float,
        fees_eur: float,
        note: str,
    ) -> None:
        gain = proceeds_eur - cost_basis_eur - fees_eur
        self.realized_gains.append(
            RealizedGain(
                timestamp=timestamp,
                asset=asset,
                quantity=quantity,
                proceeds_eur=proceeds_eur,
                cost_basis_eur=cost_basis_eur,
                fees_eur=fees_eur,
                gain_eur=gain,
                note=note,
            )
        )

    def process_operations(self, operations: List[Operation]) -> None:
        for op in sorted(operations, key=lambda o: o.timestamp):
            if op.side == "BUY":
                self._handle_buy(op)
            elif op.side == "SELL":
                self._handle_sell(op)

    def _handle_buy(self, op: Operation) -> None:
        quote_value_eur = op.quote_amount * self._price_eur(op.quote_asset, op.timestamp)
        fee_eur = self._fee_eur(op.fee_amount, op.fee_asset, op.timestamp)

        if op.quote_asset.upper() != "EUR":
            cost_basis_quote = self._consume_lots(op.quote_asset, op.quote_amount, op.timestamp)
            self._record_gain(
                timestamp=op.timestamp,
                asset=op.quote_asset,
                quantity=op.quote_amount,
                proceeds_eur=quote_value_eur,
                cost_basis_eur=cost_basis_quote,
                fees_eur=fee_eur if op.fee_asset == op.quote_asset else 0.0,
                note="Disposed quote asset to buy base asset",
            )

        cost_basis_total = quote_value_eur + (fee_eur if op.fee_asset == op.base_asset else 0.0)
        cost_per_unit = cost_basis_total / op.amount if op.amount else 0.0
        self._add_lot(op.base_asset, op.amount, cost_per_unit)

    def _handle_sell(self, op: Operation) -> None:
        proceeds_quote_eur = op.quote_amount * self._price_eur(op.quote_asset, op.timestamp)
        fee_eur = self._fee_eur(op.fee_amount, op.fee_asset, op.timestamp)

        cost_basis_base = self._consume_lots(op.base_asset, op.amount, op.timestamp)
        self._record_gain(
            timestamp=op.timestamp,
            asset=op.base_asset,
            quantity=op.amount,
            proceeds_eur=proceeds_quote_eur,
            cost_basis_eur=cost_basis_base,
            fees_eur=fee_eur,
            note="Sold base asset",
        )

        net_for_quote = proceeds_quote_eur - (fee_eur if op.fee_asset == op.quote_asset else 0.0)
        quote_units = op.quote_amount if op.quote_amount else 0.0
        if quote_units > 0:
            cost_per_unit = net_for_quote / quote_units if quote_units else 0.0
            self._add_lot(op.quote_asset, quote_units, cost_per_unit)
