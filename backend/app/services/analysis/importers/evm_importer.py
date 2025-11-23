"""Importer for wallet addresses on multiple EVM-compatible chains."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

import requests

from ....models import NormalizedTx
from .evm_chains import CHAIN_CONFIG, ChainConfig


def _fetch_tx_history(cfg: ChainConfig, address: str) -> List[dict]:
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "chain": cfg.api_chain,
        "chainid": cfg.chain_identifier,
        "apikey": cfg.api_key or "YourApiKeyToken",
    }
    resp = requests.get(cfg.base_url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "1":
        result = payload.get("result")
        message = payload.get("message") or "EVM explorer error"
        if isinstance(result, str):
            message = f"{message}: {result}"
        if "API KEY" in message.upper():
            raise RuntimeError(
                f"{cfg.chain_id} explorer requiere una API key válida (define la variable {cfg.env_var})"
            )
        raise RuntimeError(f"{cfg.chain_id} API error: {message}")
    result = payload.get("result", [])
    if not isinstance(result, list):
        raise RuntimeError(f"{cfg.chain_id} API response not understood")
    return result


def _fetch_token_transfers(cfg: ChainConfig, address: str) -> List[dict]:
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "chain": cfg.api_chain,
        "chainid": cfg.chain_identifier,
        "apikey": cfg.api_key or "YourApiKeyToken",
    }
    resp = requests.get(cfg.base_url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "1":
        return []
    result = payload.get("result", [])
    if not isinstance(result, list):
        return []
    return result


def _normalize_tx(cfg: ChainConfig, address: str, tx: dict) -> NormalizedTx:
    decimals = 10 ** cfg.decimals
    value = int(tx.get("value", "0") or "0") / decimals
    gas_price = int(tx.get("gasPrice", "0") or "0")
    gas_used = int(tx.get("gasUsed", "0") or "0")
    fee = (gas_price * gas_used) / decimals
    to_addr = (tx.get("to") or "").lower()
    from_addr = (tx.get("from") or "").lower()
    addr_lower = address.lower()
    incoming = to_addr == addr_lower
    amount = value if incoming else -value
    tx_type = "transfer_in" if incoming else "transfer_out"
    fee_value = fee if not incoming else 0.0
    timestamp = datetime.fromtimestamp(int(tx.get("timeStamp", "0") or "0"))

    return NormalizedTx(
        id=f"{cfg.chain_id}-{tx['hash']}-{address}",
        timestamp=timestamp,
        asset=cfg.symbol,
        chain=cfg.chain_id,
        amount=amount,
        fee=fee_value,
        fee_asset=cfg.symbol,
        location="wallet_evm",
        address=address,
        src_address=tx.get("from"),
        dst_address=tx.get("to"),
        type=tx_type,
        source_system="evm_chain",
        raw={
            "hash": tx["hash"],
            "nonce": tx.get("nonce"),
            "blockNumber": tx.get("blockNumber"),
            "value": value,
            "gasPrice": tx.get("gasPrice"),
            "gasUsed": tx.get("gasUsed"),
        },
    )


def _gas_entry(cfg: ChainConfig, address: str, tx_hash: str, timestamp: datetime, fee: float) -> NormalizedTx:
    return NormalizedTx(
        id=f"{cfg.chain_id}-gas-{tx_hash}-{address}",
        timestamp=timestamp,
        asset=cfg.symbol,
        chain=cfg.chain_id,
        amount=-fee,
        fee=0.0,
        fee_asset=cfg.symbol,
        location="wallet_evm",
        address=address,
        src_address=address,
        dst_address=None,
        type="other",
        source_system="evm_chain",
        raw={"hash": tx_hash, "gas_fee": fee},
    )


def _normalize_token_transfer(cfg: ChainConfig, address: str, tx: dict) -> List[NormalizedTx]:
    decimals = 10 ** int(tx.get("tokenDecimal", "0") or "0")
    if decimals == 0:
        decimals = 1
    value = int(tx.get("value", "0") or "0") / decimals
    to_addr = (tx.get("to") or "").lower()
    from_addr = (tx.get("from") or "").lower()
    addr_lower = address.lower()
    incoming = to_addr == addr_lower
    amount = value if incoming else -value
    fee = 0.0
    fee_entries: List[NormalizedTx] = []
    if not incoming:
        gas_price = int(tx.get("gasPrice", "0") or "0")
        gas_used = int(tx.get("gasUsed", "0") or "0")
        fee = (gas_price * gas_used) / (10 ** cfg.decimals)
        if fee > 0:
            fee_entries.append(_gas_entry(cfg, address, tx["hash"], timestamp, fee))
    timestamp = datetime.fromtimestamp(int(tx.get("timeStamp", "0") or "0"))

    entry = NormalizedTx(
        id=f"{cfg.chain_id}-token-{tx['hash']}-{tx.get('tokenSymbol', '').upper()}-{address}",
        timestamp=timestamp,
        asset=(tx.get("tokenSymbol") or tx.get("tokenName") or "TOKEN").upper(),
        chain=cfg.chain_id,
        amount=amount,
        fee=0.0,
        fee_asset=cfg.symbol,
        location="wallet_evm",
        address=address,
        src_address=tx.get("from"),
        dst_address=tx.get("to"),
        type="transfer_in" if incoming else "transfer_out",
        source_system="evm_chain",
        token_address=tx.get("contractAddress"),
        raw={
            "hash": tx["hash"],
            "tokenName": tx.get("tokenName"),
            "tokenSymbol": tx.get("tokenSymbol"),
            "tokenDecimal": tx.get("tokenDecimal"),
            "value": value,
        },
    )
    return [entry, *fee_entries]


def import_evm_addresses(addresses: Iterable[str], chains: Iterable[str]) -> List[NormalizedTx]:
    normalized: List[NormalizedTx] = []
    for chain_id in chains:
        cfg = CHAIN_CONFIG.get(chain_id)
        if not cfg:
            continue
        for address in addresses:
            if not address:
                continue
            transactions = _fetch_tx_history(cfg, address)
            token_transfers = _fetch_token_transfers(cfg, address)
            for tx in transactions:
                normalized.append(_normalize_tx(cfg, address, tx))
            for token_tx in token_transfers:
                normalized.extend(_normalize_token_transfer(cfg, address, token_tx))
    return normalized
