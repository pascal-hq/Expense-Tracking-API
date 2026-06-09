from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
import time
import logging
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

# Rate limiting imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import get_db, engine
from models import Base, UserModel, ExpenseModel
from schemas import ExpenseCreate, ExpenseResponse, UserCreate, UserResponse, TokenResponse
from auth import hash_password, verify_password, create_access_token, get_current_user

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming: {request.method} {request.url.path}")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    
    # Log response details
    logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    # Add custom header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.get("/")
def hello():
    return {"message": "Expense API with Authentication"}

@app.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")  # Limit registrations
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hash_password(user.password)
    db_user = UserModel(email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=TokenResponse)
@limiter.limit("10/minute")  # Limit login attempts
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/expenses", response_model=ExpenseResponse)
@limiter.limit("10/minute")  # Max 10 expenses per minute
def create_expense(
    request: Request,
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    db_expense = ExpenseModel(**expense.dict(), owner_id=current_user.id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

# GET endpoint with filtering and pagination
@app.get("/expenses")
@limiter.limit("30/minute")  # Higher limit for reads
def get_my_expenses(
    request: Request,
    # Pagination parameters
    skip: int = 0,
    limit: int = 10,
    
    # Filtering parameters
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Base query: only this user's expenses
    query = db.query(ExpenseModel).filter(ExpenseModel.owner_id == current_user.id)
    
    # Apply filters (only if provided)
    if category:
        query = query.filter(ExpenseModel.category == category)
    
    if start_date:
        query = query.filter(ExpenseModel.date >= start_date)
    
    if end_date:
        query = query.filter(ExpenseModel.date <= end_date)
    
    if min_amount:
        query = query.filter(ExpenseModel.amount >= min_amount)
    
    if max_amount:
        query = query.filter(ExpenseModel.amount <= max_amount)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and execute
    expenses = query.offset(skip).limit(limit).all()
    
    return {
        "data": expenses,
        "total": total,
        "skip": skip,
        "limit": limit
    }

# ANALYTICS ENDPOINT
@app.get("/expenses/analytics/summary")
@limiter.limit("5/minute")  # Stricter limit for analytics (heavier query)
def get_expense_analytics(
    request: Request,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Base query
    query = db.query(ExpenseModel).filter(ExpenseModel.owner_id == current_user.id)
    
    # Apply same filters as main endpoint
    if category:
        query = query.filter(ExpenseModel.category == category)
    if start_date:
        query = query.filter(ExpenseModel.date >= start_date)
    if end_date:
        query = query.filter(ExpenseModel.date <= end_date)
    
    # Get all expenses
    expenses = query.all()
    
    if not expenses:
        return {
            "message": "No expenses found",
            "total_expenses": 0,
            "average_expense": 0,
            "highest_expense": 0,
            "lowest_expense": 0,
            "total_count": 0,
            "by_category": {},
            "by_month": {}
        }
    
    # Calculate analytics
    amounts = [e.amount for e in expenses]
    total = sum(amounts)
    average = total / len(amounts)
    highest = max(amounts)
    lowest = min(amounts)
    
    # Spending by category
    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount
    
    # Spending by month (YYYY-MM format)
    by_month = {}
    for e in expenses:
        month_key = e.date.strftime("%Y-%m")
        by_month[month_key] = by_month.get(month_key, 0) + e.amount
    
    return {
        "total_expenses": round(total, 2),
        "average_expense": round(average, 2),
        "highest_expense": highest,
        "lowest_expense": lowest,
        "total_count": len(expenses),
        "by_category": by_category,
        "by_month": by_month
    }

# CSV EXPORT ENDPOINT
@app.get("/expenses/export/csv")
@limiter.limit("3/minute")  # Strictest limit for file generation
def export_expenses_csv(
    request: Request,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Build query with same filters
    query = db.query(ExpenseModel).filter(ExpenseModel.owner_id == current_user.id)
    
    if category:
        query = query.filter(ExpenseModel.category == category)
    if start_date:
        query = query.filter(ExpenseModel.date >= start_date)
    if end_date:
        query = query.filter(ExpenseModel.date <= end_date)
    
    expenses = query.all()
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["ID", "Amount", "Description", "Category", "Date"])
    
    # Write data rows
    for expense in expenses:
        writer.writerow([
            expense.id,
            expense.amount,
            expense.description,
            expense.category,
            expense.date.strftime("%Y-%m-%d")
        ])
    
    # Prepare response
    output.seek(0)
    filename = f"expenses_{date.today()}.csv"
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
@limiter.limit("30/minute")
def get_expense(
    request: Request,
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    expense = db.query(ExpenseModel).filter(
        ExpenseModel.id == expense_id,
        ExpenseModel.owner_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
@limiter.limit("10/minute")
def update_expense(
    request: Request,
    expense_id: int,
    updated: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    expense = db.query(ExpenseModel).filter(
        ExpenseModel.id == expense_id,
        ExpenseModel.owner_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    for key, value in updated.dict().items():
        setattr(expense, key, value)
    
    db.commit()
    db.refresh(expense)
    return expense

@app.delete("/expenses/{expense_id}")
@limiter.limit("10/minute")
def delete_expense(
    request: Request,
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    expense = db.query(ExpenseModel).filter(
        ExpenseModel.id == expense_id,
        ExpenseModel.owner_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted"}