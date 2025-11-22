import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Dict, Iterable, List, Literal

from dateutil import parser as date_parser

from ..models import CashMovement, Operation

EXPECTED_HEADERS = [
    "Date(UTC)",
    "Pair",
    "Side",
    "Price",
    "Executed",
    "Amount",
    "Fee",
    "Fee Asset",
]

MOVEMENTS_HEADERS = [
    "User_ID",
    "UTC_Time",
    "Account",
    "Operation",
    "Coin",
    "Change",
    "Remark",
]

FIAT_ASSETS = {
    "EUR",
    "USD",
    "USDT",
    "BUSD",
    "USDC",
    "GBP",
    "TRY",
}


class CSVFormatError(ValueError):
    pass


def _parse_pair(raw_pair: str) -> tuple[str, str]:
    if "/" in raw_pair:
        base, quote = raw_pair.split("/", 1)
        return base.strip().upper(), quote.strip().upper()

    candidates = ["USDT", "BUSD", "USDC", "EUR", "USD", "GBP", "TRY", "BNB", "BTC", "ETH"]
    token = raw_pair.strip().upper()
    for suffix in candidates:
        if token.endswith(suffix) and len(token) > len(suffix):
            return token[: -len(suffix)], suffix
    if len(token) < 6:
        raise CSVFormatError(f"Could not parse trading pair: {raw_pair}")
    midpoint = len(token) // 2
    return token[:midpoint], token[midpoint:]


def parse_binance_csv(content: str) -> tuple[List[Operation], List[CashMovement]]:
    preview_reader = csv.DictReader(StringIO(content))
    headers = preview_reader.fieldnames or []
    normalized_headers = {h.strip() for h in headers}

    if all(header in normalized_headers for header in EXPECTED_HEADERS):
        return _parse_trade_history_csv(content), []
    if all(header in normalized_headers for header in MOVEMENTS_HEADERS):
        return _parse_account_statement_csv(content)

    raise CSVFormatError(
        "CSV headers do not match supported Binance export formats."
    )


def _parse_trade_history_csv(content: str) -> List[Operation]:
    reader = csv.DictReader(StringIO(content))
    headers = reader.fieldnames
    if headers is None or any(h not in headers for h in EXPECTED_HEADERS):
        raise CSVFormatError(
            "CSV headers do not match expected Binance export format."
        )

    operations: List[Operation] = []
    for row in reader:
        try:
            timestamp = date_parser.parse(row["Date(UTC)"])
            side = row["Side"].strip().upper()
            price = float(row["Price"])
            executed_qty = float(row["Executed"])
            amount_quote = float(row.get("Amount") or price * executed_qty)
            fee_amount = float(row.get("Fee") or 0)
            fee_asset = row.get("Fee Asset", "").strip().upper() or "UNKNOWN"
            base_asset, quote_asset = _parse_pair(row["Pair"])
        except Exception as exc:  # noqa: BLE001
            raise CSVFormatError(f"Invalid row detected: {row}") from exc

        operations.append(
            Operation(
                timestamp=timestamp,
                base_asset=base_asset,
                quote_asset=quote_asset,
                side=side,
                price=price,
                amount=executed_qty,
                quote_amount=amount_quote,
                fee_amount=fee_amount,
                fee_asset=fee_asset,
            )
        )

    return operations


@dataclass
class MovementEntry:
    timestamp: datetime
    order: int
    operation: str
    coin: str
    change: Decimal


@dataclass
class MovementTrade:
    timestamp: datetime
    base_asset: str
    base_amount: Decimal
    quote_asset: str
    quote_amount: Decimal
    side: str
    fee_amount: Decimal = Decimal("0")
    fee_asset: str = "UNKNOWN"

    @property
    def price(self) -> Decimal:
        if self.base_amount == 0:
            return Decimal("0")
        return self.quote_amount / self.base_amount


def _parse_account_statement_csv(content: str) -> tuple[List[Operation], List[CashMovement]]:
    reader = csv.DictReader(StringIO(content))
    headers = reader.fieldnames
    if headers is None or any(h not in headers for h in MOVEMENTS_HEADERS):
        raise CSVFormatError("CSV headers do not match Binance movimientos export.")

    groups, cash_movements = _group_movements(reader)
    merged_groups = _merge_complementary_groups(groups)
    operations: List[Operation] = []

    for entries in merged_groups:
        trades = _build_trades_from_group(entries)
        for trade in trades:
            operations.append(
                Operation(
                    timestamp=trade.timestamp,
                    base_asset=trade.base_asset,
                    quote_asset=trade.quote_asset,
                    side=trade.side,
                    price=float(trade.price),
                    amount=float(trade.base_amount),
                    quote_amount=float(trade.quote_amount),
                    fee_amount=float(trade.fee_amount),
                    fee_asset=trade.fee_asset if trade.fee_amount > 0 else "UNKNOWN",
                )
            )

    if not operations:
        raise CSVFormatError("No se encontraron operaciones válidas en el CSV proporcionado.")

    return operations, cash_movements


@dataclass
class MovementGroup:
    key: str
    entries: List[MovementEntry]

    def sorted_entries(self) -> List[MovementEntry]:
        return sorted(self.entries, key=lambda e: e.order)


CASH_OPERATIONS = {"deposit", "withdraw", "airdrop assets"}


def _group_movements(reader: csv.DictReader) -> tuple[List[MovementGroup], List[CashMovement]]:
    groups: List[MovementGroup] = []
    cash_movements: List[CashMovement] = []
    row_index = 0

    for row in reader:
        timestamp_raw = (row.get("UTC_Time") or "").strip()
        if not timestamp_raw:
            continue
        try:
            timestamp = datetime.strptime(timestamp_raw, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:  # noqa: BLE001
            raise CSVFormatError(f"Invalid timestamp: {timestamp_raw}") from exc

        operation = (row.get("Operation") or "").strip()
        op_normalized = _normalize_operation(operation)
        coin = (row.get("Coin") or "").strip().upper()
        change_raw = (row.get("Change") or "").strip()
        if not coin or not change_raw:
            continue
        try:
            change = Decimal(change_raw)
        except InvalidOperation as exc:  # noqa: BLE001
            raise CSVFormatError(f"Invalid amount for {coin} at {timestamp_raw}") from exc

        if op_normalized in CASH_OPERATIONS:
            movement_type: Literal["deposit", "withdraw"] = "deposit" if change > 0 else "withdraw"
            cash_movements.append(
                CashMovement(
                    timestamp=timestamp,
                    asset=coin,
                    amount=float(abs(change)),
                    type=movement_type,
                    origin=op_normalized,
                )
            )
            row_index += 1
            continue

        entry = MovementEntry(
            timestamp=timestamp,
            order=row_index,
            operation=operation,
            coin=coin,
            change=change,
        )
        row_index += 1
        group_id = _movement_group_id(timestamp_raw, (row.get("Remark") or "").strip())
        if not groups or groups[-1].key != group_id:
            groups.append(MovementGroup(key=group_id, entries=[]))
        groups[-1].entries.append(entry)

    return groups, cash_movements


def _movement_group_id(timestamp: str, remark: str) -> str:
    remark_value = remark.strip()
    if remark_value:
        return f"remark::{remark_value}"
    return f"time::{timestamp}"


def _merge_complementary_groups(groups: List[MovementGroup]) -> List[List[MovementEntry]]:
    merged: List[List[MovementEntry]] = []
    idx = 0
    while idx < len(groups):
        group = groups[idx]
        if _is_fee_only(group.entries):
            idx += 1
            continue

        if _has_single_side(group.entries):
            partner = _find_partner_group(groups, idx)
            if partner is not None:
                combined = sorted(
                    group.entries + groups[partner].entries,
                    key=lambda entry: entry.order,
                )
                merged.append(combined)
                idx = partner + 1
                continue

        merged.append(group.sorted_entries())
        idx += 1

    return merged


def _find_partner_group(groups: List[MovementGroup], current_index: int) -> int | None:
    current = groups[current_index]
    current_signature = _operation_signature(current.entries)
    if not current_signature:
        return None
    current_has_positive = _has_positive_entries(current.entries)

    next_index = current_index + 1
    while next_index < len(groups):
        candidate = groups[next_index]
        if _is_fee_only(candidate.entries):
            next_index += 1
            continue
        if (
            _operation_signature(candidate.entries) == current_signature
            and _has_positive_entries(candidate.entries) != current_has_positive
            and _has_single_side(candidate.entries)
        ):
            return next_index
        break

    return None


def _operation_signature(entries: Iterable[MovementEntry]) -> frozenset[str]:
    return frozenset(
        _normalize_operation(entry.operation)
        for entry in entries
        if not _is_fee(entry.operation)
    )


def _normalize_operation(operation: str) -> str:
    return operation.strip().lower()


def _has_positive_entries(entries: Iterable[MovementEntry]) -> bool:
    return any(entry.change > 0 and not _is_fee(entry.operation) for entry in entries)


def _has_negative_entries(entries: Iterable[MovementEntry]) -> bool:
    return any(entry.change < 0 and not _is_fee(entry.operation) for entry in entries)


def _has_single_side(entries: Iterable[MovementEntry]) -> bool:
    has_positive = _has_positive_entries(entries)
    has_negative = _has_negative_entries(entries)
    return (has_positive or has_negative) and has_positive != has_negative


def _is_fee_only(entries: Iterable[MovementEntry]) -> bool:
    return all(_is_fee(entry.operation) for entry in entries)


def _build_trades_from_group(entries: Iterable[MovementEntry]) -> List[MovementTrade]:
    positive: List[MovementEntry] = []
    negative: List[MovementEntry] = []
    fees: Dict[str, Decimal] = {}

    for entry in entries:
        if _is_fee(entry.operation):
            fees[entry.coin] = fees.get(entry.coin, Decimal("0")) + abs(entry.change)
            continue
        if entry.change > 0:
            positive.append(entry)
        elif entry.change < 0:
            negative.append(entry)

    if not positive or not negative:
        return []

    if len(positive) != len(negative):
        raise CSVFormatError(
            f"Operaciones desbalanceadas en {positive[0].timestamp.isoformat()}."
        )

    trades: List[MovementTrade] = []
    for pos_entry, neg_entry in zip(positive, negative):
        trades.append(_build_trade_from_entries(pos_entry, neg_entry))

    if fees:
        _apply_fees(trades, fees)

    return trades


def _build_trade_from_entries(pos_entry: MovementEntry, neg_entry: MovementEntry) -> MovementTrade:
    base_asset: str
    quote_asset: str
    side: str

    pos_amount = pos_entry.change
    neg_amount = abs(neg_entry.change)

    if _is_fiat(pos_entry.coin) and not _is_fiat(neg_entry.coin):
        side = "SELL"
        base_asset = neg_entry.coin
        base_amount = neg_amount
        quote_asset = pos_entry.coin
        quote_amount = pos_amount
    else:
        side = "BUY"
        base_asset = pos_entry.coin
        base_amount = pos_amount
        quote_asset = neg_entry.coin
        quote_amount = neg_amount
        if _is_fiat(pos_entry.coin) and _is_fiat(neg_entry.coin):
            # Buying fiat using fiat (e.g., EUR->USDT)
            side = "BUY"

    return MovementTrade(
        timestamp=pos_entry.timestamp,
        base_asset=base_asset,
        base_amount=base_amount,
        quote_asset=quote_asset,
        quote_amount=quote_amount,
        side=side,
    )


def _apply_fees(trades: List[MovementTrade], fees: Dict[str, Decimal]) -> None:
    for asset, total_fee in fees.items():
        candidates: List[tuple[MovementTrade, Decimal]] = []
        for trade in trades:
            if trade.base_asset == asset:
                candidates.append((trade, trade.base_amount))
            elif trade.quote_asset == asset:
                candidates.append((trade, trade.quote_amount))

        weight_sum = sum(weight for _, weight in candidates)
        if weight_sum == 0:
            continue

        for trade, weight in candidates:
            share = (total_fee * weight) / weight_sum
            if share == 0:
                continue
            if trade.fee_asset not in ("UNKNOWN", asset):
                raise CSVFormatError(
                    f"Multiple fee assets detected for transaction at {trade.timestamp.isoformat()}."
                )
            trade.fee_asset = asset
            trade.fee_amount += share

def _is_fee(operation: str) -> bool:
    op = operation.strip().lower()
    return "fee" in op or "commission" in op


def _is_fiat(symbol: str) -> bool:
    return symbol.upper() in FIAT_ASSETS
