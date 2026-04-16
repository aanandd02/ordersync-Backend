from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import math
from ..database import get_db
from ..models import Order, User, OrderStatus
from ..schemas import OrderCreate, OrderOut, PaginatedOrders, OrderUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists and is active
    result = await db.execute(select(User).where(User.id == order.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create order for inactive user")

    db_order = Order(**order.model_dump())
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order

@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalar_one_or_none()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.patch("/{order_id}", response_model=OrderOut)
async def update_order_status(order_id: int, order_update: OrderUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    db_order = result.scalar_one_or_none()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Rule 4: A confirmed order must not have its status manually changed back to pending
    if db_order.status == OrderStatus.CONFIRMED and order_update.status == OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="A confirmed order must not have its status manually changed back to pending")

    db_order.status = order_update.status
    db_order.version += 1 # Standard version increment
    await db.commit()
    await db.refresh(db_order)
    return db_order

# Separation for user orders as per Rule 5
@router.get("/user/{user_id}", response_model=PaginatedOrders)
async def list_user_orders(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * page_size
    
    # Rule 5: Single round-trip pagination using window functional for count
    # Note: SQLAlchemy's select(..., func.count().over())
    stmt = (
        select(Order, func.count().over().label("total_count"))
        .where(Order.user_id == user_id)
        .offset(offset)
        .limit(page_size)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    if not rows:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "pages": 0
        }
    
    total = rows[0].total_count
    items = [row.Order for row in rows]
    pages = math.ceil(total / page_size)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }
