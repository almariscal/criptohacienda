from datetime import datetime, date
from typing import Dict, List, Literal

from pydantic import BaseModel, Field


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

    class Config:
        orm_mode = True


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
    session_id: str = Field(..., description="Identifier for the uploaded session")
    operations_count: int
    realized_gains_count: int
