import csv
from datetime import datetime
from io import StringIO
from typing import List

from dateutil import parser as date_parser

from ..models import Operation

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


def parse_binance_csv(content: str) -> List[Operation]:
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
