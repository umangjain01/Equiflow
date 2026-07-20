import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Dict

from .database import engine, Base, get_db
from . import models, schemas, auth, engine_wrapper

# Initialize database schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EquiFlow - Group Expense & Debt Optimization API")

# Setup static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=FileResponse)
def read_root():
    """Serves the EquiFlow Web Dashboard & Interactive Demo."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>EquiFlow API Server Running</h1><p>Visit <a href='/docs'>/docs</a> for API specifications.</p>")

@app.post("/demo/settle-up", response_model=List[schemas.TransactionResponse])
def demo_settle_up(balances: Dict[int, float]):
    """Sandbox endpoint for calculating optimal settlements using the C++ core engine."""
    return engine_wrapper.solve_settlements(balances)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- Authentication Dependency ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """FastAPI dependency to retrieve the authenticated user using JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_410_GONE if False else status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = auth.decode_access_token(token)
    if not payload:
        raise credentials_exception
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    if username is None or user_id is None:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# --- Auth Routes ---
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user and hashes their password."""
    username = user_in.username
    if not username:
        username = user_in.email.split("@")[0]
    if len(username) < 3:
        import time
        username = f"user_{username}_{int(time.time())}"

    # Check if user already exists
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == user_in.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in instead."
        )
    
    hashed_pw = auth.get_password_hash(user_in.password)
    db_user = models.User(
        username=username,
        email=user_in.email,
        hashed_password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=schemas.Token)
def login(login_in: schemas.UserLogin, db: Session = Depends(get_db)):
    """Logs in an existing user and returns a signed JWT."""
    user = db.query(models.User).filter(
        (models.User.username == login_in.username) | (models.User.email == login_in.username)
    ).first()
    
    if not user or not auth.verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
        
    access_token = auth.create_access_token(data={"sub": user.username, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Group Management Helpers (For validation & ease of testing) ---
@app.post("/groups", response_model=schemas.GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group_in: schemas.GroupCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a new group and automatically adds the creator as a member."""
    db_group = models.Group(name=group_in.name, description=group_in.description)
    db_group.members.append(current_user)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.get("/groups", response_model=List[schemas.GroupResponse])
def get_user_groups(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns all groups/trips the current authenticated user belongs to."""
    return current_user.groups

@app.get("/groups/{group_id}", response_model=schemas.GroupResponse)
def get_group_detail(group_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns details for a specific group/trip."""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group or current_user not in group.members:
        raise HTTPException(status_code=404, detail="Group not found or unauthorized")
    return group

@app.post("/groups/{group_id}/members", status_code=status.HTTP_200_OK)
def add_group_member(group_id: int, user_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Adds a registered user to a group (must be group member to do this)."""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not authorized to modify this group")
        
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User to add not found")
        
    if target_user in group.members:
        raise HTTPException(status_code=400, detail="User is already a member of this group")
        
    group.members.append(target_user)
    db.commit()
    return {"message": f"Successfully added {target_user.username} to group {group.name}"}


# --- Expense & Settle Up Routes ---
@app.post("/groups/{group_id}/add-expense", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_expense(
    group_id: int,
    expense_in: schemas.ExpenseCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adds a group expense and records how it is split among members.
    Calculates exact amounts if EQUAL, otherwise validates sum.
    """
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Only group members can add expenses")

    # Verify payee is in group
    payer = db.query(models.User).filter(models.User.id == expense_in.paid_by_id).first()
    if not payer or payer not in group.members:
        raise HTTPException(status_code=400, detail="Payer must be a valid group member")

    # Create Expense base entry
    db_expense = models.Expense(
        group_id=group_id,
        description=expense_in.description,
        amount=expense_in.amount,
        paid_by_id=expense_in.paid_by_id,
        split_type=expense_in.split_type,
        category=expense_in.category
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # Process Splits
    num_splits = len(expense_in.splits)
    for split in expense_in.splits:
        # Verify split target is a group member
        split_user = db.query(models.User).filter(models.User.id == split.user_id).first()
        if not split_user or split_user not in group.members:
            # Clean up created expense
            db.delete(db_expense)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Split user {split.user_id} is not a member of this group")
            
        # Calculate split amount
        if expense_in.split_type == "EQUAL":
            owed = round(expense_in.amount / num_splits, 2)
        else:
            owed = split.amount_owed
            
        db_split = models.ExpenseSplit(
            expense_id=db_expense.id,
            user_id=split.user_id,
            amount_owed=owed
        )
        db.add(db_split)
        
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/groups/{group_id}/settle-up", response_model=List[schemas.TransactionResponse])
def settle_up(
    group_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches the group expenses, calculates net balances for all members,
    and passes them to the C++ core engine via ctypes wrapper to get optimized settlements.
    """
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not authorized to settle up this group")

    # Initialize net balances for all current group members to 0.0
    balances = {member.id: 0.0 for member in group.members}

    # Fetch all expenses for this group
    expenses = db.query(models.Expense).filter(models.Expense.group_id == group_id).all()

    for exp in expenses:
        # Crediting the payer
        if exp.paid_by_id in balances:
            balances[exp.paid_by_id] += exp.amount
            
        # Debiting the participants for their splits
        for split in exp.splits:
            if split.user_id in balances:
                balances[split.user_id] -= split.amount_owed

    # Optimize settlements using the wrapper
    optimized_transactions = engine_wrapper.solve_settlements(balances)
    return optimized_transactions


# --- Analytics Insights Route Stub (To be fully implemented in Module 4) ---
@app.get("/groups/{group_id}/insights")
def get_insights(
    group_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint mapping for Analytics.
    Returns categorized spendings and MoM spending details using Pandas.
    """
    # Verify group & membership
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="Not authorized to view group insights")
        
    from .analytics import generate_group_insights
    try:
        return generate_group_insights(group_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights calculation error: {str(e)}")
