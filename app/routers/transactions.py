from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from ..models import Transaction, Order, User, OrderStatus, TransactionStatus
from ..schemas import TransactionCreate, TransactionOut

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/", response_model=TransactionOut)
async def create_transaction(transaction: TransactionCreate, db: AsyncSession = Depends(get_db)):
    # Rule 2 — Idempotent Transactions
    # Check if key already exists
    existing_stmt = select(Transaction).where(Transaction.idempotency_key == transaction.idempotency_key)
    existing_result = await db.execute(existing_stmt)
    existing_tx = existing_result.scalar_one_or_none()
    
    if existing_tx:
        # Return 200 OK with original transaction
        return existing_tx

    # Rule 4 — Order Guards
    # Get order and user status
    order_stmt = select(Order, User).join(User).where(Order.id == transaction.order_id)
    order_result = await db.execute(order_stmt)
    row = order_result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_obj, user_obj = row.Order, row.User
    
    # Validation Rules
    if order_obj.status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="A cancelled order must not accept new transactions")
    
    if not user_obj.is_active:
        raise HTTPException(status_code=403, detail="An order belonging to a soft-deleted user must not accept new transactions")

    # Start business logic for transaction creation
    db_tx = Transaction(**transaction.model_dump())
    
    try:
        db.add(db_tx)
        
        # Rule 3 — Paid Amount Tracking & Auto-Confirmation
        if transaction.status == TransactionStatus.SUCCESS:
            new_paid_amount = order_obj.paid_amount + transaction.amount
            new_status = order_obj.status
            
            if new_paid_amount >= order_obj.total_amount:
                new_status = OrderStatus.CONFIRMED
            
            # Optimistic Locking update
            update_stmt = (
                update(Order)
                .where(and_(Order.id == order_obj.id, Order.version == order_obj.version))
                .values(
                    paid_amount=new_paid_amount,
                    status=new_status,
                    version=Order.version + 1
                )
            )
            
            result = await db.execute(update_stmt)
            if result.rowcount == 0:
                await db.rollback()
                raise HTTPException(status_code=409, detail="Concurrent update detected (Conflict)")
        
        await db.commit()
        await db.refresh(db_tx)
        return db_tx
    
    except IntegrityError:
        # Handle race condition for idempotency key if two requests pass the initial check
        await db.rollback()
        existing_result = await db.execute(existing_stmt)
        existing_tx = existing_result.scalar_one_or_none()
        if existing_tx:
            return existing_tx
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        await db.rollback()
        raise e
