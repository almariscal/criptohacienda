"""Importer for BTC addresses using Blockstream API."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

import requests

from ....models import NormalizedTx

BLOCKSTREAM_API = "https://blockstream.info/api"
SATOSHI = 100_000_000


def _fetch_address_txs(address: str) -> List[dict]:
    resp = requests.get(f"{BLOCKSTREAM_API}/address/{address}/txs", timeout=30)
    resp.raise_for_status()
    return resp.json()


def _address_value_change(address: str, tx: dict) -> float:
    spent = 0
    for vin in tx.get("vin", []):
        prev = vin.get("prevout") or {}
        if prev.get("scriptpubkey_address") == address:
            spent += prev.get("value", 0)
    received = 0
    for vout in tx.get("vout", []):
        if vout.get("scriptpubkey_address") == address:
            received += vout.get("value", 0)
    return (received - spent) / SATOSHI


def _tx_timestamp(tx: dict) -> datetime:
    status = tx.get("status") or {}
    block_time = status.get("block_time")
    if block_time:
        return datetime.fromtimestamp(block_time)
    return datetime.utcnow()


def import_btc_addresses(addresses: Iterable[str]) -> List[NormalizedTx]:
    normalized: List[NormalizedTx] = []
    for address in addresses:
        if not address:
            continue
        raw_txs = _fetch_address_txs(address)
        for tx in raw_txs:
            change = _address_value_change(address, tx)
            if abs(change) <= 0:
                continue
            tx_type = "transfer_in" if change > 0 else "transfer_out"
            fee_btc = tx.get("fee", 0) / SATOSHI if change < 0 else 0.0
            src = None
            if tx.get("vin"):
                src = tx["vin"][0].get("prevout", {}).get("scriptpubkey_address")
            dst = None
            if tx.get("vout"):
                for output in tx["vout"]:
                    if output.get("scriptpubkey_address") != address:
                        dst = output.get("scriptpubkey_address")
                        break
            normalized.append(
                NormalizedTx(
                    id=f"btc-{tx['txid']}-{address}",
                    timestamp=_tx_timestamp(tx),
                    asset="BTC",
                    chain="bitcoin",
                    amount=change,
                    fee=fee_btc,
                    fee_asset="BTC",
                    location="wallet_btc",
                    address=address,
                    src_address=src,
                    dst_address=dst,
                    type=tx_type,
                    source_system="btc_chain",
                    raw={"hash": tx["txid"], "balance_change": change},
                )
            )
    return normalized
