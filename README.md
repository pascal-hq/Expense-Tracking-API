# Expense Tracker API

A production-ready REST API for personal expense management with JWT authentication, real-time analytics, bulk operations, and CSV export capabilities.

## 🚀 Live Demo

**API Base URL:** https://expense-tracking-api-tc7f.onrender.com

**Interactive Documentation:** https://expense-tracking-api-tc7f.onrender.com/docs

## ✨ Features

- **User Authentication** - Secure JWT-based auth with bcrypt password hashing
- **Full CRUD Operations** - Create, read, update, and delete expenses
- **Bulk Create** - Add multiple expenses in a single API call
- **Filtering & Pagination** - Filter by category, date range, amount with skip/limit
- **Analytics** - Spending summaries by category and month
- **CSV Export** - Download your expense data as CSV files
- **Rate Limiting** - API protection (5-30 requests/minute per endpoint)
- **Request Logging** - Automatic logging with response times
- **Auto Documentation** - Swagger UI at `/docs` and ReDoc at `/redoc`

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Framework | FastAPI |
| Database | SQLite / PostgreSQL-ready |
| ORM | SQLAlchemy |
| Authentication | JWT + bcrypt |
| Rate Limiting | slowapi |
| Logging | Python logging + middleware |
| Deployment | Render |

## 📊 API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/register` | Create new user | 5/min |
| POST | `/token` | Login & get JWT token | 10/min |
| POST | `/expenses` | Create single expense | 10/min |
| POST | `/expenses/bulk` | Create multiple expenses | 5/min |
| GET | `/expenses` | List expenses (filter + pagination) | 30/min |
| GET | `/expenses/{id}` | Get single expense | 30/min |
| PUT | `/expenses/{id}` | Update expense | 10/min |
| DELETE | `/expenses/{id}` | Delete expense | 10/min |
| GET | `/expenses/analytics/summary` | Get spending analytics | 5/min |
| GET | `/expenses/export/csv` | Download CSV export | 3/min |

## 🔍 Filtering & Pagination Example

GET /expenses?category=Food&start_date=2026-06-01&end_date=2026-06-30&min_amount=10&skip=0&limit=20

| Parameter | Type | Description |
|-----------|------|-------------|
| `skip` | int | Records to skip (pagination) |
| `limit` | int | Max records to return (default 10) |
| `category` | string | Filter by category |
| `start_date` | date | Expenses after this date |
| `end_date` | date | Expenses before this date |
| `min_amount` | float | Minimum amount |
| `max_amount` | float | Maximum amount |

## 📊 Analytics Response Example

```json
{
  "total_expenses": 790.5,
  "average_expense": 158.1,
  "highest_expense": 500,
  "lowest_expense": 15,
  "total_count": 5,
  "by_category": {
    "Food": 240.5,
    "Bills": 550
  },
  "by_month": {
    "2026-06": 790.5
  }
}

```
## 🏁 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/pascal-hq/Expense-Tracking-API.git
cd Expense-Tracking-API

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "SECRET_KEY=your-secret-key-here" > .env
echo "ALGORITHM=HS256" >> .env

# Run the server
uvicorn main:app --reload
```
🧪 Testing the API
PowerShell
```powershell
# Register
$body = @{email="test@example.com"; password="secret123"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://expense-tracking-api-tc7f.onrender.com/register" -Method POST -ContentType "application/json" -Body $body

# Login
$body = "username=test@example.com&password=secret123"
$response = Invoke-RestMethod -Uri "https://expense-tracking-api-tc7f.onrender.com/token" -Method POST -ContentType "application/x-www-form-urlencoded" -Body $body
$token = $response.access_token

# Create expense
$headers = @{Authorization = "Bearer $token"}
$body = @{amount=25.50; description="Lunch"; category="Food"; date="2026-06-10"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://expense-tracking-api-tc7f.onrender.com/expenses" -Method POST -Body $body -ContentType "application/json" -Headers $headers

# Get expenses
Invoke-RestMethod -Uri "https://expense-tracking-api-tc7f.onrender.com/expenses" -Headers $headers
```
cURL
```powershell
# Register
curl -X POST https://expense-tracking-api-tc7f.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}'

# Login
curl -X POST https://expense-tracking-api-tc7f.onrender.com/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=secret123"

# Create expense (use the token from login response)
curl -X POST https://expense-tracking-api-tc7f.onrender.com/expenses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":25.50,"description":"Lunch","category":"Food","date":"2026-06-10"}'
```
## 🔒 Security Features

| Feature | Implementation |
|---------|----------------|
| Password Storage | bcrypt hashing |
| Authentication | JWT tokens (60-minute expiration) |
| Authorization | User isolation via `owner_id` |
| Rate Limiting | 5-30 requests/minute |
| Request Logging | All requests with timestamps |

## 📁 Project Structure


📁 Project Structure
expense-tracker-api/
├── main.py              # FastAPI app with all endpoints
├── database.py          # Database connection & session
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic validation schemas
├── auth.py              # JWT & password functions
├── expenses.db          # SQLite database (auto-generated)
├── requirements.txt     # Dependencies
├── .env                 # Environment variables
└── README.md            # This file


## 📚 Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Live:** https://expense-tracking-api-tc7f.onrender.com/docs

## 🚀 Deployment

Deployed on **Render** (free tier):

- Auto-deploys on push to `main` branch
- PostgreSQL upgrade ready with `DATABASE_URL` env var

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License

## 👨‍💻 Author

**Pascal** - [GitHub](https://github.com/pascal-hq)

## 📊 Badges

![FastAPI](https://img.shields.io/badge/FastAPI-0.115-blue) ![Python](https://img.shields.io/badge/Python-3.11-green) ![SQLite](https://img.shields.io/badge/Database-SQLite-blue) ![Render](https://img.shields.io/badge/Deployed-Render-purple) ![Rate Limiting](https://img.shields.io/badge/Rate%20Limiting-slowapi-orange) ![JWT](https://img.shields.io/badge/Auth-JWT-red) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

⭐ Star this repo if you find it useful!
