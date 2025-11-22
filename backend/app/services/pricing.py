from datetime import datetime
from typing import Dict, Tuple

import requests
from cachetools import LRUCache


SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "USDT": "tether",
    "BUSD": "binance-usd",
    "USDC": "usd-coin",
    "ADA": "cardano",
    "XRP": "ripple",
    "DOT": "polkadot",
    "SOL": "solana",
}

_CACHE: LRUCache[Tuple[str, str], float] = LRUCache(maxsize=256)


class PricingError(RuntimeError):
    pass


def _coingecko_id(symbol: str) -> str:
    upper = symbol.upper()
    if upper in ("EUR",):
        return "EUR"
    return SYMBOL_TO_ID.get(upper, upper.lower())


def _fetch_price_eur(asset_id: str, date_key: str) -> float:
    if asset_id == "EUR":
        return 1.0
    url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/history"
    params = {"date": date_key, "localization": "false"}
    try:
        response = requests.get(url, params=params, timeout=15)
    except requests.RequestException as exc:  # noqa: BLE001
        raise PricingError(f"Failed to reach pricing service for {asset_id}") from exc
    if response.status_code != 200:
        raise PricingError(
            f"Failed to fetch price for {asset_id}: {response.status_code}"
        )
    data = response.json()
    try:
        return float(data["market_data"]["current_price"]["eur"])
    except Exception as exc:  # noqa: BLE001
        raise PricingError(f"Missing EUR price for {asset_id}") from exc


def _cache_key(symbol: str, timestamp: datetime) -> Tuple[str, str]:
    date_key = timestamp.strftime("%d-%m-%Y")
    return symbol.upper(), date_key


def get_price_eur(symbol: str, timestamp: datetime) -> float:
    asset_id = _coingecko_id(symbol)
    symbol_key, date_key = _cache_key(symbol, timestamp)
    cache_key = (symbol_key, date_key)

    if cache_key in _CACHE:
        return _CACHE[cache_key]

    price = _fetch_price_eur(asset_id, date_key)
    _CACHE[cache_key] = price
    return price
