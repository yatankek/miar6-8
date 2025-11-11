from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from enum import Enum

class DeliveryStatus(str, Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    DELIVERED = "DELIVERED"

class DeliveryCreate(BaseModel):
    order_id: UUID
    address_from: str
    address_to: str
    recipient_name: str
    recipient_phone: str

class DeliveryUpdate(BaseModel):
    courier_id: UUID | None = None
    status: DeliveryStatus | None = None

class DeliveryResponse(BaseModel):
    id: UUID
    order_id: UUID
    status: DeliveryStatus
    address_from: str
    address_to: str
    recipient_name: str
    recipient_phone: str
    courier_id: UUID | None = None
    created_date: datetime
    assigned_date: datetime | None = None
    delivered_date: datetime | None = None

    class Config:
        from_attributes = True