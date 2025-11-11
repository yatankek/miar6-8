from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from enum import Enum

class TransactionType(str, Enum):
    ACCRUAL = "ACCRUAL"
    WRITE_OFF = "WRITE_OFF"

# Схемы для операций с баллами
class AccruePointsRequest(BaseModel):
    order_id: UUID
    delivery_id: UUID | None = None
    amount: float
    reason: str

class WriteOffPointsRequest(BaseModel):
    order_id: UUID
    amount: float
    reason: str

class TransactionResponse(BaseModel):
    id: UUID
    account_id: UUID
    type: TransactionType
    amount: float
    order_id: UUID
    delivery_id: UUID | None = None
    reason: str
    created_date: datetime

    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    account_id: UUID
    current_balance: float
    as_of_date: datetime

    class Config:
        from_attributes = True