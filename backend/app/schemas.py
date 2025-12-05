from datetime import datetime, date
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


GroupBy = Literal["day", "week", "month", "year"]


class OperationSchema(BaseModel):
    timestamp: datetime
    base_asset: str
    quote_asset: str
    side: str
    price: float
    amount: float
    quote_amount: float
    fee_amount: float
    fee_asset: str

    model_config = ConfigDict(from_attributes=True)


class RealizedGainSchema(BaseModel):
    timestamp: datetime
    asset: str
    quantity: float
    proceeds_eur: float
    cost_basis_eur: float
    fees_eur: float
    gain_eur: float
    note: str = ""


class HoldingLotSchema(BaseModel):
    amount: float
    cost_per_unit: float


class HoldingsResponse(BaseModel):
    holdings: Dict[str, List[HoldingLotSchema]]


class OperationsResponse(BaseModel):
    operations: List[OperationSchema]


class RealizedGainsResponse(BaseModel):
    realized_gains: List[RealizedGainSchema]


class SummaryItem(BaseModel):
    period_start: date
    proceeds_eur: float
    cost_basis_eur: float
    fees_eur: float
    gain_eur: float


class SummaryResponse(BaseModel):
    group_by: GroupBy
    items: List[SummaryItem]


class UploadResponse(BaseModel):
    job_id: str = Field(..., description="Identifier for the processing job")


class SessionResponse(BaseModel):
    session_id: str


class UploadJobStep(BaseModel):
    id: str
    label: str
    status: Literal["pending", "running", "completed", "error"]


class UploadJobStatus(BaseModel):
    job_id: str
    status: Literal["pending", "running", "completed", "error"]
    steps: List[UploadJobStep]
    session_id: Optional[str] = None
    error: Optional[str] = None
    messages: List[str] = Field(default_factory=list)


class NormalizedTxSchema(BaseModel):
    id: str
    timestamp: datetime
    asset: str
    amount: float
    fee: float
    fee_asset: str
    location: str
    type: str
    source_system: str
    chain: Optional[str] = None
    token_address: Optional[str] = None
    address: Optional[str] = None
    src_address: Optional[str] = None
    dst_address: Optional[str] = None
    raw: Optional[dict] = None
    wallet_id: Optional[str] = None
    source_label: Optional[str] = None


class DashboardOperation(BaseModel):
    id: str
    date: date
    asset: str
    type: str
    amount: float
    price: float
    fee: float | None = None
    total: float | None = None


class DashboardHolding(BaseModel):
    asset: str
    quantity: float
    averagePrice: float
    currentValue: float


class DashboardGainDetail(BaseModel):
    timestamp: datetime
    asset: str
    quantity: float
    proceeds: float
    gain: float


class DashboardGainPoint(BaseModel):
    period: str
    gain: float
    details: List[DashboardGainDetail]


class PortfolioSnapshotPoint(BaseModel):
    timestamp: datetime
    totalValue: float
    assetValues: Dict[str, float]
    totalDeposited: float
    totalWithdrawn: float


class DashboardSummary(BaseModel):
    totalInvested: float
    totalWithdrawn: float
    currentBalance: float
    totalFees: float
    realizedGains: float
    unrealizedGains: float


class AssetPerformancePoint(BaseModel):
    asset: str
    gains: float
    operations: int


class AssetLedgerEntry(BaseModel):
    id: str
    timestamp: datetime
    location: str
    type: str
    amount: float
    fee: float
    fee_asset: str
    source_system: str
    raw: Optional[dict] = None


class AssetBreakdown(BaseModel):
    asset: str
    total_in: float
    total_out: float
    net_amount: float
    fees_paid: float
    entries: List[AssetLedgerEntry]


class AssetHistoryPoint(BaseModel):
    timestamp: datetime
    balance: float


class FlowEntry(BaseModel):
    tx_id: str
    timestamp: datetime
    asset: str
    amount: float
    location: str
    chain: Optional[str] = None
    counterparty: Optional[str] = None
    type: str


class FlowHistory(BaseModel):
    inflows: List[FlowEntry]
    outflows: List[FlowEntry]
    movements: List[FlowEntry]


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    gains: List[DashboardGainPoint]
    operations: List[DashboardOperation]
    holdings: List[DashboardHolding]
    portfolioHistory: List[PortfolioSnapshotPoint]
    assetPerformance: List[AssetPerformancePoint]
    missingPrices: List[str] = []


class AnalyzeResponse(BaseModel):
    normalizedTxs: List[NormalizedTxSchema]
    pnlSummary: Dict[str, float]
    balancesByLocation: Dict[str, Dict[str, float]]
    operationsTimeline: List[NormalizedTxSchema]
    valueTimeline: Dict[str, float]
    assetHistory: Dict[str, List[AssetHistoryPoint]]
    assetBreakdown: List[AssetBreakdown]
    flowHistory: FlowHistory
