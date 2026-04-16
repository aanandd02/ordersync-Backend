# OrderSync Backend API

Backend Engineering Intern Assignment for **Leapmile Robotics**. This project is a production-ready FastAPI backend designed to manage a relational system for Users, Orders, and Transactions while enforcing complex business logic and high-performance reporting.

## 🚀 Technology Stack
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous)
- **Database**: PostgreSQL
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (with `asyncpg` for async I/O)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/latest/)
- **Documentation**: Swagger UI / ReDoc (Automatic)

## 🛠️ Features & Business Rules Implementation

### 1. Database Schema
Comprehensive relational design using PostgreSQL:
- **User**: Tracks active status and creation timestamps.
- **Order**: Includes optimistic locking via a `version` field and tracking for `paid_amount`.
- **Transaction**: Unique `idempotency_key` enforcement for distributed consistency.

### 2. Rule 1 — Soft-Delete Propagation
When a user is deactivated (`DELETE /users/{id}` or `is_active = False`), all **pending** orders are automatically cancelled within the same database transaction. Confirmed/Cancelled orders remain intact to preserve history.

### 3. Rule 2 — Idempotent Transactions
The `POST /transactions` endpoint ensures strict atomicity. Using a unique `idempotency_key`, the system guarantees that duplicate requests return the original transaction record (200 OK) without creating duplicate side effects.

### 4. Rule 3 — Paid Amount Tracking & Auto-Confirmation
- Successful transactions automatically increment the order's `paid_amount`.
- If an order is fully paid (`paid_amount >= total`), its status transitions to **Confirmed**.
- **Optimistic Locking**: Uses the `version` field to prevent race conditions during concurrent transaction processing.

### 5. Rule 4 — Order Guards
- **Cancelled Order Guard**: Rejects new transactions for cancelled orders (400).
- **Status Integrity**: Prevents manual status reversion from Confirmed to Pending (400).
- **Soft-Delete Guard**: Rejects transactions for orders belonging to inactive users (403).

### 6. Rule 5 — Efficient Pagination
The `GET /users/{id}/orders` endpoint implements **single round-trip pagination**. Using SQL Window Functions (`COUNT(*) OVER()`), it returns the current page data and the total record count in one efficient query.

### 7. Raw SQL Reporting
Implementation of `GET /reports/orders-summary` bypassing the ORM for maximum performance:
- Uses a **single Raw SQL query** with Common Table Expressions (CTEs).
- Aggregates total revenue, average order value, and status distribution.
- Lists Top 5 Users by total successful transaction volume (math performed entirely in SQL).

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL instance

### Installation
1. Navigate to the project directory:
   ```bash
   cd "OrderSync Backend"
   ```
2. Create and configure your `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
Start the development server:
```bash
uvicorn main:app --reload
```

### API Documentation
Once running, you can access the interactive documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---
*Developed as part of the Leapmile Robotics Backend Engineering Intern Assignment.*
