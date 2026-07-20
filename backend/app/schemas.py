from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, model_validator

class UserCreate(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=4)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class SplitCreate(BaseModel):
    user_id: int
    amount_owed: Optional[float] = None  # Populated based on split_type

class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    paid_by_id: int
    split_type: str = Field(..., description="Must be 'EQUAL' or 'EXACT'")
    category: Optional[str] = None
    splits: List[SplitCreate]

    @model_validator(mode="after")
    def validate_splits(self):
        if self.split_type not in ["EQUAL", "EXACT"]:
            raise ValueError("split_type must be either 'EQUAL' or 'EXACT'")
        
        if not self.splits:
            raise ValueError("splits list cannot be empty")
        
        if self.split_type == "EXACT":
            total_split_amount = sum(s.amount_owed for s in self.splits if s.amount_owed is not None)
            # Check if all splits have amount_owed
            if any(s.amount_owed is None for s in self.splits):
                raise ValueError("For EXACT split_type, each split must specify amount_owed")
            if abs(total_split_amount - self.amount) > 1e-2:
                raise ValueError(f"Sum of splits ({total_split_amount}) must equal total expense amount ({self.amount})")
        return self

class SplitResponse(BaseModel):
    user_id: int
    amount_owed: float

    class Config:
        from_attributes = True

class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    description: str
    amount: float
    paid_by_id: int
    split_type: str
    category: Optional[str]
    created_at: datetime
    splits: List[SplitResponse]

    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: float

    class Config:
        from_attributes = True
