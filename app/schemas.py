from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from .models import OrderStatus, TransactionStatus

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    user_id: int
    total: float

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: OrderStatus

class OrderOut(OrderBase):
    id: int
    paid_amount: float
    status: OrderStatus
    version: int
    created_at: datetime
    class Config:
        from_attributes = True

class PaginatedOrders(BaseModel):
    items: List[OrderOut]
    total: int
    page: int
    page_size: int
    pages: int

class TransactionBase(BaseModel):
    order_id: int
    amount: float
    idempotency_key: str

class TransactionCreate(TransactionBase):
    status: TransactionStatus

class TransactionOut(TransactionBase):
    id: int
    status: TransactionStatus
    created_at: datetime
    class Config:
        from_attributes = True

class ReportTopUser(BaseModel):
    user_id: int
    user_name: str
    order_count: int
    total_spent: float

class OrderReport(BaseModel):
    total_orders: int
    total_revenue: float
    avg_order_value: float
    confirmed_orders: int
    cancelled_orders: int
    pending_orders: int
    top_users: List[ReportTopUser]
