from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import TransactionType


class QrisTransactionCreate(BaseModel):
    user_id: UUID
    amount: float
    transaction_type: TransactionType
    transaction_time: datetime
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    customer_hash: Optional[str] = None
    qris_reference: Optional[str] = None
    city: Optional[str] = None
    is_refund: bool = False
    fraud_flag: bool = False


class QrisTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    amount: float
    transaction_type: TransactionType
    merchant_name: Optional[str]
    transaction_time: datetime
    city: Optional[str]
    is_refund: bool
    fraud_flag: bool