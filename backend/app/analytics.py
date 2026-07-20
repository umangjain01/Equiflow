import pandas as pd
from sqlalchemy.orm import Session
from . import models

def generate_group_insights(group_id: int, db: Session) -> dict:
    """
    Retrieves all group expenses, loads them into a Pandas DataFrame,
    imputes missing categories, and computes group spending insights:
    1. Total Spending by Category
    2. Month-over-Month Group Spend
    """
    # 1. Fetch raw SQL expense data for the group
    expenses = db.query(
        models.Expense.amount,
        models.Expense.category,
        models.Expense.created_at
    ).filter(models.Expense.group_id == group_id).all()

    # 2. Check for empty expense data
    if not expenses:
        return {
            "total_spending_by_category": {},
            "month_over_month_spend": {}
        }

    # 3. Load database records into a Pandas DataFrame
    # Convert query objects (which act like tuples) into list of dicts/tuples
    data = [{"amount": exp.amount, "category": exp.category, "created_at": exp.created_at} for exp in expenses]
    df = pd.DataFrame(data)

    # 4. Data Imputation: Fill missing categories with a default value 'Uncategorized'
    # and normalize strings to capitalized format for consistent category grouping.
    df["category"] = df["category"].fillna("Uncategorized")
    df["category"] = df["category"].str.strip().str.capitalize()

    # Ensure datetime format for timestamp
    df["created_at"] = pd.to_datetime(df["created_at"])

    # 5. Calculate Total Spending by Category
    category_spend_df = df.groupby("category")["amount"].sum()
    category_spend_dict = {str(k): round(float(v), 2) for k, v in category_spend_df.to_dict().items()}

    # 6. Calculate Month-over-Month Group Spend
    # Extract year-month period string (e.g. '2026-07')
    df["month"] = df["created_at"].dt.to_period("M").astype(str)
    mom_spend_df = df.groupby("month")["amount"].sum()
    
    # Sort months sequentially
    mom_spend_df = mom_spend_df.sort_index()
    mom_spend_dict = {str(k): round(float(v), 2) for k, v in mom_spend_df.to_dict().items()}

    return {
        "total_spending_by_category": category_spend_dict,
        "month_over_month_spend": mom_spend_dict
    }
