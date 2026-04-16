from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from ..database import get_db
from ..models import User, Order, OrderStatus
from ..schemas import UserCreate, UserUpdate, UserOut

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

@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    
    # Rule 1 — Soft-Delete Propagation
    if update_data.get("is_active") is False and db_user.is_active is True:
        # Update user status
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        # Cancel pending orders in the same transaction
        await db.execute(
            update(Order)
            .where(Order.user_id == user_id)
            .where(Order.status == OrderStatus.PENDING)
            .values(status=OrderStatus.CANCELLED)
        )
    else:
        for key, value in update_data.items():
            setattr(db_user, key, value)

    await db.commit()
    await db.refresh(db_user)
    return db_user
