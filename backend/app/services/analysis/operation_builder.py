from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List, Tuple

from ...models import CashMovement, NormalizedTx, Operation


def build_wallet_operations(transactions: Iterable[NormalizedTx]) -> Tuple[List[Operation], List[CashMovement]]:
    trades: List[Operation] = []
    cash_movements: List[CashMovement] = []
    grouped: dict[str, List[NormalizedTx]] = defaultdict(list)

    for tx in transactions:
        tx_hash = (tx.raw or {}).get("hash") if tx.raw else None
        if tx_hash:
            grouped[tx_hash].append(tx)
        else:
            _append_cash_movement(tx, cash_movements)

    for tx_hash, txs in grouped.items():
        tokens: List[NormalizedTx] = []
        gas_entries: List[NormalizedTx] = []
        for tx in txs:
            if tx.raw and tx.raw.get("gas_fee"):
                gas_entries.append(tx)
            else:
                tokens.append(tx)

        positives = [tx for tx in tokens if tx.amount > 0]
        negatives = [tx for tx in tokens if tx.amount < 0]
        positives.sort(key=lambda item: item.amount, reverse=True)
        negatives.sort(key=lambda item: abs(item.amount), reverse=True)
        num_pairs = min(len(positives), len(negatives))
        total_gas = sum(abs(item.amount) for item in gas_entries)
        gas_share = (total_gas / num_pairs) if num_pairs else 0.0
        gas_asset = gas_entries[0].asset.upper() if gas_entries else None

        for idx in range(num_pairs):
            buy_tx = positives[idx]
            sell_tx = negatives[idx]
            amount = abs(buy_tx.amount)
            quote_amount = abs(sell_tx.amount)
            if amount <= 0 or quote_amount <= 0:
                continue
            trades.append(
                Operation(
                    timestamp=buy_tx.timestamp,
                    base_asset=buy_tx.asset.upper(),
                    quote_asset=sell_tx.asset.upper(),
                    side="BUY",
                    price=quote_amount / amount,
                    amount=amount,
                    quote_amount=quote_amount,
                    fee_amount=gas_share,
                    fee_asset=gas_asset or sell_tx.asset.upper(),
                )
            )

        for leftover in positives[num_pairs:]:
            _append_cash_movement(leftover, cash_movements)
        for leftover in negatives[num_pairs:]:
            _append_cash_movement(leftover, cash_movements)

    return trades, cash_movements


def _append_cash_movement(tx: NormalizedTx, collector: List[CashMovement]) -> None:
    movement_type = "deposit" if tx.amount > 0 else "withdraw"
    collector.append(
        CashMovement(
            timestamp=tx.timestamp,
            asset=tx.asset.upper(),
            amount=abs(tx.amount),
            type=movement_type,
            origin=tx.source_system,
        )
    )
