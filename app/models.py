from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class TransactionStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    version = Column(Integer, default=1)

    user = relationship("User", back_populates="orders")
    transactions = relationship("Transaction", back_populates="order")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)

    order = relationship("Order", back_populates="transactions")
