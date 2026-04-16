from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List
import math
from ..database import get_db
from ..models import User, Order, OrderStatus
from ..schemas import UserCreate, UserUpdate, UserOut, OrderOut, PaginatedOrders

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not db_user.is_active:
        return {"message": "User already inactive"}

    # Rule 1 — Soft-Delete Propagation
    db_user.is_active = False
    
    # Cancel pending orders in the same transaction
    await db.execute(
        update(Order)
        .where(Order.user_id == user_id)
        .where(Order.status == OrderStatus.PENDING)
        .values(status=OrderStatus.CANCELLED)
    )

    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.get("/{user_id}/orders", response_model=PaginatedOrders)
async def list_user_orders(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    offset = (page - 1) * page_size
    
    # Rule 5: Single round-trip pagination using window functional for count
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

@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    
    # Keep Rule 1 logic if updated via PATCH too
    if update_data.get("is_active") is False and db_user.is_active is True:
        await db.execute(
            update(Order)
            .where(Order.user_id == user_id)
            .where(Order.status == OrderStatus.PENDING)
            .values(status=OrderStatus.CANCELLED)
        )
    
    for key, value in update_data.items():
        setattr(db_user, key, value)

    await db.commit()
    await db.refresh(db_user)
    return db_user
