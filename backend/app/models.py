from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Literal, Optional


@dataclass
class CashMovement:
    timestamp: datetime
    asset: str
    amount: float
    type: Literal["deposit", "withdraw"]
    origin: str = ""


@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    total_value: float
    asset_values: Dict[str, float]
    asset_quantities: Dict[str, float]
    total_deposited_eur: float = 0.0
    total_withdrawn_eur: float = 0.0


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
class OperationView:
    id: str
    date: date
    asset: str
    type: str
    amount: float
    price: float
    fee: Optional[float] = None
    total: Optional[float] = None


@dataclass
class SessionData:
    operations: List[Operation] = field(default_factory=list)
    realized_gains: List[RealizedGain] = field(default_factory=list)
    holdings: Dict[str, List[Dict[str, float]]] = field(default_factory=dict)
    operation_views: List[OperationView] = field(default_factory=list)
    total_invested_eur: float = 0.0
    total_fees_eur: float = 0.0
    cash_movements: List[CashMovement] = field(default_factory=list)
    total_deposited_eur: float = 0.0
    total_withdrawn_eur: float = 0.0
    portfolio_snapshots: List[PortfolioSnapshot] = field(default_factory=list)


@dataclass
class ProcessingStepState:
    id: str
    label: str
    status: Literal["pending", "running", "completed", "error"] = "pending"


@dataclass
class ProcessingJob:
    id: str
    status: Literal["pending", "running", "completed", "error"] = "pending"
    steps: List[ProcessingStepState] = field(default_factory=list)
    session_id: Optional[str] = None
    error: Optional[str] = None
    messages: List[str] = field(default_factory=list)
