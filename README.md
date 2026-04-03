# Finance Tracking System Backend (FastAPI)


This is a clean, interview-ready backend for tracking financial transactions.
It demonstrates practical backend fundamentals: authentication, authorization, validation,
clear architecture, and dynamic financial summaries.

## Tech Stack


- **FastAPI**
- **SQLite** + **SQLAlchemy ORM**
- **Pydantic** (request validation + response models)
- **JWT** (`python-jose`)
- **Password hashing** (`passlib[bcrypt]`)
- **Uvicorn**

## Project Structure


```
finance_app/
  app/
    main.py          # app wiring and startup
    db.py            # SQLAlchemy engine + session dependency
    core/
      security.py    # password hashing
      jwt.py         # token create/decode
      dependencies.py # current user + role/ownership checks
    models/          # SQLAlchemy ORM models
    schemas/
      common.py
      user.py
      transaction.py
      summary.py
    services/
      user_service.py
      auth_service.py
      transaction_service.py
    routes/          # API endpoints
    utils/           # helpers (logging, response formatting)
requirements.txt
README.md
```

`.venv/` is your local Python virtual environment. It contains installed packages and should not be committed.

## Setup


```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn finance_app.app.main:app --reload
```

The database file (`finance.db`) is created automatically on startup (see `finance_app/app/main.py`).

## Authentication (JWT)

### Register

- **POST** `/auth/register`
- Creates a new user.
- For simplicity, new users default to role **viewer**.

### Login

- **POST** `/auth/login`
- Uses OAuth2 password form:
  - `username` = email
  - `password` = password
- Returns an access token. Use it as:


```http
Authorization: Bearer <token>
```

## Roles & Permissions

This project keeps roles simple and explainable:

- **viewer**: can read their own transactions
- **analyst**: can create/update/delete their own transactions + use summary endpoint
- **admin**: full access (can read/update/delete any user's transactions)

Ownership rules are enforced in the transaction service layer:

- Non-admins can only modify **their own** transactions
- Admins can modify **all** transactions

Authorization uses both role checks and ownership checks:
- role check answers "can this user perform this type of action?"
- ownership check answers "can this user perform this action on this record?"

## Transactions API

### Create transaction (analyst/admin)

- **POST** `/transactions/`

Body:

```json
{
  "amount": 1200,
  "type": "income",
  "category": "salary",
  "date": "2026-04-03",
  "description": "April salary"
}
```

### List transactions (viewer/analyst/admin)

- **GET** `/transactions/`
- Supports filtering + pagination:
  - `type=income|expense`
  - `category=<string>`
  - `date_from=YYYY-MM-DD`
  - `date_to=YYYY-MM-DD`
  - `limit` (1..100)
  - `offset` (>=0)

### Get transaction by id (viewer/analyst/admin)

- **GET** `/transactions/{transaction_id}`

### Update transaction (analyst/admin)

- **PUT** `/transactions/{transaction_id}`
- Ownership enforced (admin can update any; analyst only their own).

### Delete transaction (analyst/admin)

- **DELETE** `/transactions/{transaction_id}`
- Ownership enforced.

## Financial Summary (analyst/admin)

- **GET** `/transactions/summary`
- Supports the same filters as list.

Returns:

- `total_income`
- `total_expense`
- `balance` (= income - expense)
- `category_breakdown`
- `monthly_summary`

### Why balance is calculated dynamically (important design decision)

We do **not** store balance in the database because it is derived from the source-of-truth data (transactions).  
Derived values like balance are not stored to avoid inconsistency and race conditions.

- **Avoids inconsistency**: if a transaction is updated/deleted, a stored balance can easily become wrong if some code path forgets to update it.
- **Concurrency safety**: with concurrent writes, derived fields are prone to race conditions. Recomputing from committed transaction data keeps reads correct and predictable.

## Consistent API Response Format

All endpoints return:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

Errors use the same envelope via a global HTTP exception handler.

## SQLite choice & migration to PostgreSQL

SQLite is used because it is:

- simple to run locally
- perfect for a 2–3 day project demo

To migrate to PostgreSQL:

- replace the SQLAlchemy database URL in `finance_app/app/db.py`
- introduce migrations (commonly **Alembic**) instead of auto-creating tables on startup
- add connection pooling and production DB configuration

## Architecture in one line

`routes -> services -> models/db`  
Routes only handle HTTP input/output. Services hold business logic. Models + DB layer persist data.

## Scaling path


When traffic/data grows, common next steps are:
- switch SQLite to PostgreSQL
- add caching for expensive summaries
- add background jobs for heavy reporting
- add monitoring and alerting

## Assumptions


- Single currency (amount is a plain number)
- Simple roles (no fine-grained permission matrix)
- SQLite is sufficient for this demo; production would use Postgres + migrations

## Future Improvements


- Add tests (pytest)
- Add Alembic migrations
- Add pagination metadata (total count)
- Add refresh tokens + token rotation
- Add rate limiting (login brute-force protection)
- Switch `amount` from float → decimal for stricter money handling

