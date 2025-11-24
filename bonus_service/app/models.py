from sqlalchemy import Column, String, DateTime, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from .database import Base

class TransactionType(str, enum.Enum):
    ACCRUAL = "ACCRUAL"
    WRITE_OFF = "WRITE_OFF"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    delivery_id = Column(UUID(as_uuid=True), nullable=True)
    reason = Column(String, nullable=False)
    created_date = Column(DateTime, nullable=False)

class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    current_balance = Column(Float, default=0.0, nullable=False)
    as_of_date = Column(DateTime, nullable=False)