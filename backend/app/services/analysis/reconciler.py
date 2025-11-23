"""Detect internal transfers between Binance and wallets."""
from __future__ import annotations

from datetime import timedelta
from typing import List

from ...models import NormalizedTx

MATCH_WINDOW = timedelta(minutes=15)


def reconcile_internal_transfers(transactions: List[NormalizedTx]) -> None:
    candidates = [tx for tx in transactions if tx.type in {"transfer_in", "transfer_out", "deposit", "withdrawal"}]
    candidates.sort(key=lambda tx: tx.timestamp)
    matched: set[str] = set()

    for idx, tx in enumerate(candidates):
        if tx.id in matched:
            continue
        for other in candidates[idx + 1 :]:
            if other.id in matched:
                continue
            if tx.asset != other.asset:
                continue
            dt = abs(tx.timestamp - other.timestamp)
            if dt > MATCH_WINDOW:
                if other.timestamp - tx.timestamp > MATCH_WINDOW:
                    break
                continue
            if tx.amount * other.amount >= 0:
                continue
            amount_diff = abs(abs(tx.amount) - abs(other.amount))
            threshold = max(abs(tx.amount), abs(other.amount)) * 0.02 + 1e-8
            if amount_diff > threshold:
                continue
            if not _locations_match(tx, other):
                continue
            tx.type = "other"
            other.type = "other"
            matched.update({tx.id, other.id})
            break


def _locations_match(tx1: NormalizedTx, tx2: NormalizedTx) -> bool:
    pair = {tx1.location, tx2.location}
    if pair == {"binance_spot", "wallet_btc"}:
        return True
    if pair == {"binance_spot", "wallet_evm"}:
        return True
    if pair == {"wallet_evm"}:
        return True
    return False
