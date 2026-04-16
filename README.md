# OrderSync Backend API

Backend Engineering Intern Assignment for Leapmile Robotics. This project is a FastAPI-based backend for managing users, orders, and transactions with strict business logic and raw SQL reporting requirements.

## 🚀 Technology Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL (Async)
- **ORM**: SQLAlchemy 2.0 (with `asyncpg`)
- **Validation**: Pydantic v2

## 🛠️ Features & Business Rules Implementation

### 1. Database Schema
Defined explicit relationships between **Users**, **Orders**, and **Transactions**.
- **User**: Managed active status and soft-delete propagation.
- **Order**: Implemented optimistic locking using a `version` field.
- **Transaction**: Unique `idempotency_key` enforcement.

### 2. Rule 1: Soft-Delete Propagation
When a user is deactivated (`is_active = False`), all their **pending** orders are automatically cancelled within the same database transaction. Confirmed/Cancelled orders remain unchanged.

### 3. Rule 2: Idempotent Transactions
The `POST /transactions` endpoint ensures atomicity. If a request arrives with an existing `idempotency_key`, the original transaction is returned without creating a duplicate.

### 4. Rule 3: Paid Amount Tracking & Auto-Confirmation
Successful transactions automatically increment the order's `paid_amount`. If the balance is fully paid, the order status transitions to `confirmed`. Optimistic locking prevents race conditions during concurrent updates.

### 5. Rule 4: Business Logic Guards
- **Cancelled Order Guard**: Rejects transactions for cancelled orders (400).
- **Status Integrity**: Prevents confirmed orders from being set back to pending (400).
- **Soft-Delete Guard**: Rejects transactions for orders belonging to inactive users (403).

### 6. Rule 5: Efficient Pagination
The `/orders/user/{id}` endpoint implement single round-trip pagination using SQL Window Functions (`COUNT(*) OVER()`), returning data and metadata in one query.

### 7. Raw SQL Reporting
The `/reports/orders-summary` endpoint is implemented using a **single raw SQL query** (utilizing CTEs) to aggregate:
- Total orders, revenue, and average order value.
- Status distribution (confirmed, cancelled, pending).
- Top 5 users by successful transaction volume.

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL

### Installation
1. Clone the repository and navigate to the project directory.
2. Create a `.env` file from the template:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally
```bash
uvicorn main:app --reload
```
API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

---
*Developed as part of the Leapmile Robotics Backend Engineering Intern Assignment.*
