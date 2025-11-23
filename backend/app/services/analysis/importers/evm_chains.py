"""Configuration for supported EVM chains."""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ChainConfig:
    chain_id: str
    base_url: str
    symbol: str
    decimals: int
    api_key: str
    env_var: str
    api_chain: str
    chain_identifier: str


def _api_key(env_name: str, default: str = "") -> str:
    return os.getenv(env_name, default)


CHAIN_CONFIG: dict[str, ChainConfig] = {
    "ethereum": ChainConfig("ethereum", "https://api.etherscan.io/v2/api", "ETH", 18, _api_key("ETHERSCAN_API_KEY", ""), "ETHERSCAN_API_KEY", "eth", "1"),
    "arbitrum": ChainConfig("arbitrum", "https://api.arbiscan.io/v2/api", "ETH", 18, _api_key("ARBISCAN_API_KEY", ""), "ARBISCAN_API_KEY", "arb", "42161"),
    "base": ChainConfig("base", "https://api.basescan.org/v2/api", "ETH", 18, _api_key("BASESCAN_API_KEY", ""), "BASESCAN_API_KEY", "base", "8453"),
    "polygon": ChainConfig("polygon", "https://api.polygonscan.com/v2/api", "MATIC", 18, _api_key("POLYGONSCAN_API_KEY", ""), "POLYGONSCAN_API_KEY", "matic", "137"),
    "optimism": ChainConfig("optimism", "https://api-optimistic.etherscan.io/v2/api", "ETH", 18, _api_key("OPTIMISTICSCAN_API_KEY", ""), "OPTIMISTICSCAN_API_KEY", "opt", "10"),
    "bsc": ChainConfig("bsc", "https://api.bscscan.com/v2/api", "BNB", 18, _api_key("BSCSCAN_API_KEY", ""), "BSCSCAN_API_KEY", "bsc", "56"),
    "avalanche": ChainConfig("avalanche", "https://api.snowtrace.io/v2/api", "AVAX", 18, _api_key("SNOWTRACE_API_KEY", ""), "SNOWTRACE_API_KEY", "avax", "43114"),
}
