from datetime import datetime
from typing import Dict, Tuple, Set

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
_MISSING_ASSETS: Set[str] = set()


class PricingError(RuntimeError):
    pass


def _coingecko_id(symbol: str) -> str:
    upper = symbol.upper()
    if upper in ("EUR",):
        return "EUR"
    return SYMBOL_TO_ID.get(upper, upper.lower())


def _fetch_coingecko_history(asset_id: str, date_key: str) -> float:
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


def _fetch_coingecko_spot(asset_id: str) -> float:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": asset_id, "vs_currencies": "eur"}
    try:
        response = requests.get(url, params=params, timeout=15)
    except requests.RequestException as exc:  # noqa: BLE001
        raise PricingError(f"Failed to reach spot pricing service for {asset_id}") from exc
    if response.status_code != 200:
        raise PricingError(
            f"Failed to fetch current price for {asset_id}: {response.status_code}"
        )
    data = response.json()
    try:
        return float(data[asset_id]["eur"])
    except Exception as exc:  # noqa: BLE001
        raise PricingError(f"Missing EUR spot price for {asset_id}") from exc


def _fetch_cryptocompare_day_avg(symbol: str, timestamp: datetime) -> float:
    if symbol.upper() == "EUR":
        return 1.0
    url = "https://min-api.cryptocompare.com/data/dayAvg"
    params = {
        "fsym": symbol.upper(),
        "tsym": "EUR",
        "toTs": int(timestamp.timestamp()),
        "avgType": "MidHighLow",
    }
    try:
        response = requests.get(url, params=params, timeout=15)
    except requests.RequestException as exc:  # noqa: BLE001
        raise PricingError(f"Failed to reach CryptoCompare day average for {symbol}") from exc
    data = response.json()
    if response.status_code != 200 or data.get("Response") == "Error":
        raise PricingError(f"CryptoCompare day average error for {symbol}: {data.get('Message')}")
    value = data.get("EUR")
    if value is None:
        raise PricingError(f"Missing EUR day average for {symbol}")
    return float(value)


def _fetch_cryptocompare_spot(symbol: str) -> float:
    if symbol.upper() == "EUR":
        return 1.0
    url = "https://min-api.cryptocompare.com/data/price"
    params = {"fsym": symbol.upper(), "tsyms": "EUR"}
    try:
        response = requests.get(url, params=params, timeout=15)
    except requests.RequestException as exc:  # noqa: BLE001
        raise PricingError(f"Failed to reach CryptoCompare spot for {symbol}") from exc
    data = response.json()
    if response.status_code != 200 or data.get("Response") == "Error":
        raise PricingError(f"CryptoCompare spot error for {symbol}: {data.get('Message')}")
    value = data.get("EUR")
    if value is None:
        raise PricingError(f"Missing EUR spot price for {symbol}")
    return float(value)


def _fetch_price_eur(symbol: str, asset_id: str, timestamp: datetime, date_key: str) -> float:
    providers = [
        lambda: _fetch_coingecko_history(asset_id, date_key),
        lambda: _fetch_cryptocompare_day_avg(symbol, timestamp),
        lambda: _fetch_coingecko_spot(asset_id),
        lambda: _fetch_cryptocompare_spot(symbol),
    ]

    errors = []
    for provider in providers:
        try:
            return provider()
        except PricingError as exc:
            errors.append(str(exc))
            continue
    _record_missing(symbol)
    return 0.0


def _cache_key(symbol: str, timestamp: datetime) -> Tuple[str, str]:
    date_key = timestamp.strftime("%d-%m-%Y")
    return symbol.upper(), date_key


def _normalize_timestamp(timestamp: datetime) -> datetime:
    now = datetime.utcnow()
    if timestamp > now:
        return now
    return timestamp


def get_price_eur(symbol: str, timestamp: datetime) -> float:
    asset_id = _coingecko_id(symbol)
    normalized_ts = _normalize_timestamp(timestamp)
    symbol_key, date_key = _cache_key(symbol, normalized_ts)
    cache_key = (symbol_key, date_key)

    if cache_key in _CACHE:
        return _CACHE[cache_key]

    price = _fetch_price_eur(symbol, asset_id, normalized_ts, date_key)
    _CACHE[cache_key] = price
    return price


def _record_missing(symbol: str) -> None:
    _MISSING_ASSETS.add(symbol.upper())


def reset_missing_assets() -> None:
    _MISSING_ASSETS.clear()


def get_missing_assets() -> list[str]:
    return sorted(_MISSING_ASSETS)
