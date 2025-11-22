from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class Operation:
    timestamp: datetime
    base_asset: str
    quote_asset: str
    side: str
    price: float
    amount: float
    quote_amount: float
    fee_amount: float
    fee_asset: str


@dataclass
class RealizedGain:
    timestamp: datetime
    asset: str
    quantity: float
    proceeds_eur: float
    cost_basis_eur: float
    fees_eur: float
    gain_eur: float
    note: str = ""


@dataclass
class SessionData:
    operations: List[Operation] = field(default_factory=list)
    realized_gains: List[RealizedGain] = field(default_factory=list)
    holdings: Dict[str, List[Dict[str, float]]] = field(default_factory=dict)
