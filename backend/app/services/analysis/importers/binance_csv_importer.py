"""Binance CSV importer that converts operations into NormalizedTx entries."""
from __future__ import annotations

from typing import List
from uuid import uuid4

from ....models import NormalizedTx
from ... import parser


def import_binance_transactions(content: str | None) -> List[NormalizedTx]:
    if not content or not content.strip():
        return []
    operations, cash_movements = parser.parse_binance_csv(content)
    normalized: List[NormalizedTx] = []
    for idx, op in enumerate(operations):
        tx_id_base = f"binance-{idx}-base"
        tx_id_quote = f"binance-{idx}-quote"
        base_amount = op.amount if op.side.upper() == "BUY" else -op.amount
        quote_amount = -op.quote_amount if op.side.upper() == "BUY" else op.quote_amount

        common_raw = {
            "side": op.side,
            "pair": f"{op.base_asset}/{op.quote_asset}",
            "price": op.price,
            "quote_amount": op.quote_amount,
        }
        normalized.append(
            NormalizedTx(
                id=tx_id_base,
                timestamp=op.timestamp,
                asset=op.base_asset.upper(),
                chain=None,
                amount=base_amount,
                fee=0.0,
                fee_asset=op.base_asset.upper(),
                location="binance_spot",
                address=None,
                src_address=None,
                dst_address=None,
                type="trade",
                source_system="binance_csv",
                raw=common_raw,
            )
        )
        normalized.append(
            NormalizedTx(
                id=tx_id_quote,
                timestamp=op.timestamp,
                asset=op.quote_asset.upper(),
                chain=None,
                amount=quote_amount,
                fee=0.0,
                fee_asset=op.quote_asset.upper(),
                location="binance_spot",
                address=None,
                src_address=None,
                dst_address=None,
                type="trade",
                source_system="binance_csv",
                raw=common_raw,
            )
        )

        if op.fee_amount and op.fee_asset:
            normalized.append(
                NormalizedTx(
                    id=f"binance-{idx}-fee",
                    timestamp=op.timestamp,
                    asset=op.fee_asset.upper(),
                    chain=None,
                    amount=-abs(op.fee_amount),
                    fee=0.0,
                    fee_asset=op.fee_asset.upper(),
                    location="binance_spot",
                    address=None,
                    src_address=None,
                    dst_address=None,
                    type="trade",
                    source_system="binance_csv",
                    raw={"fee_asset": op.fee_asset, "fee_amount": op.fee_amount},
                )
            )

    for movement in cash_movements:
        normalized.append(
            NormalizedTx(
                id=str(uuid4()),
                timestamp=movement.timestamp,
                asset=movement.asset.upper(),
                chain=None,
                amount=movement.amount,
                fee=0.0,
                fee_asset=movement.asset.upper(),
                location="binance_spot",
                address=None,
                src_address=None,
                dst_address=None,
                type="deposit" if movement.type == "deposit" else "withdrawal",
                source_system="binance_csv",
                raw={"origin": movement.origin},
            )
        )

    return normalized
