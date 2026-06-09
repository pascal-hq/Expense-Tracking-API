from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional

from database import get_db, engine
from models import Base, UserModel, ExpenseModel
from schemas import ExpenseCreate, ExpenseResponse, UserCreate, UserResponse, TokenResponse
from auth import hash_password, verify_password, create_access_token, get_current_user

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Expense API with Authentication"}

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    db_expense = ExpenseModel(**expense.dict(), owner_id=current_user.id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

# UPDATED: GET endpoint with filtering and pagination
@app.get("/expenses")
def get_my_expenses(
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

@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(
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
def update_expense(
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
def delete_expense(
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