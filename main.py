from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users, orders, transactions, reports

app = FastAPI(title="OrderSync API", description="Leapmile Robotics Internship Assignment")

# Dynamic discovery of tables
from app import models

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

app.include_router(users.router)
app.include_router(orders.router)
app.include_router(transactions.router)
app.include_router(reports.router)

@app.get("/")
async def root():
    return {"message": "OrderSync API is running", "docs": "/docs"}
