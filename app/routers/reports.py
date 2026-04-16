from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
from ..schemas import OrderReport

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/orders-summary", response_model=OrderReport)
async def get_orders_summary(db: AsyncSession = Depends(get_db)):
    # Rule 4: Raw SQL Requirement
    # Aggregated stats in a single query using CTEs
    # Note: Using text() to execute raw SQL as requested, bypassing ORM query builder
    raw_query = """
    WITH order_stats AS (
        SELECT 
            COUNT(*)::int AS total_orders,
            COALESCE(SUM(total), 0)::float AS total_revenue,
            COALESCE(AVG(total), 0)::float AS avg_order_value,
            COUNT(*) FILTER (WHERE status = 'confirmed')::int AS confirmed_orders,
            COUNT(*) FILTER (WHERE status = 'cancelled')::int AS cancelled_orders,
            COUNT(*) FILTER (WHERE status = 'pending')::int AS pending_orders
        FROM orders
    ),
    user_successful_transactions AS (
        SELECT 
            u.id AS user_id,
            u.name AS user_name,
            COUNT(DISTINCT o.id)::int AS order_count,
            COALESCE(SUM(t.amount), 0)::float AS total_spent
        FROM users u
        JOIN orders o ON u.id = o.user_id
        JOIN transactions t ON o.id = t.order_id
        WHERE t.status = 'success'
        GROUP BY u.id, u.name
        ORDER BY total_spent DESC
        LIMIT 5
    ),
    top_users_agg AS (
        SELECT COALESCE(json_agg(ust), '[]'::json) AS top_users
        FROM user_successful_transactions ust
    )
    SELECT 
        os.total_orders,
        os.total_revenue,
        os.avg_order_value,
        os.confirmed_orders,
        os.cancelled_orders,
        os.pending_orders,
        tua.top_users
    FROM order_stats os, top_users_agg tua;
    """
    
    result = await db.execute(text(raw_query))
    row = result.first()
    
    if not row:
        return {
            "total_orders": 0,
            "total_revenue": 0.0,
            "avg_order_value": 0.0,
            "confirmed_orders": 0,
            "cancelled_orders": 0,
            "pending_orders": 0,
            "top_users": []
        }
    
    return {
        "total_orders": row.total_orders,
        "total_revenue": row.total_revenue,
        "avg_order_value": row.avg_order_value,
        "confirmed_orders": row.confirmed_orders,
        "cancelled_orders": row.cancelled_orders,
        "pending_orders": row.pending_orders,
        "top_users": row.top_users
    }
