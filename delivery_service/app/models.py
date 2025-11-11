from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from .database import Base

class DeliveryStatus(str, enum.Enum):
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    DELIVERED = "DELIVERED"

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    address_from = Column(String, nullable=False)
    address_to = Column(String, nullable=False)
    recipient_name = Column(String, nullable=False)
    recipient_phone = Column(String, nullable=False)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.CREATED)
    courier_id = Column(UUID(as_uuid=True), nullable=True)
    created_date = Column(DateTime, nullable=False)
    assigned_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)