from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List, Optional

class ExpenseCreate(BaseModel):
    amount: float
    description: str
    category: str
    date: date
    
class ExpenseResponse(ExpenseCreate):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
        
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True
        
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class ExpenseFilters(BaseModel):
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None