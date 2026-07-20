import sys
import os

# Adjust path to import local app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import logging
logging.basicConfig(level=logging.INFO)

from app import engine_wrapper

def run_verification():
    print("==================================================")
    print("       EQUIFLOW CORE ENGINE VERIFICATION SUITE    ")
    print("==================================================")

    # Test Case 1: Simple 3-user group
    # User 1 owes $30, User 3 owes $30, User 2 is owed $60.
    # Expected optimization: User 1 pays User 2 ($30), User 3 pays User 2 ($30).
    balances_1 = {
        1: -30.0,
        2: 60.0,
        3: -30.0
    }

    print(f"\n[Test Case 1] Input Balances: {balances_1}")
    res_1 = engine_wrapper.solve_settlements(balances_1)
    print(f"[Test Case 1] Optimized Transactions: {res_1}")

    assert len(res_1) == 2, "Test Case 1 failed: Expected 2 transactions."
    for tx in res_1:
        assert tx["to_user_id"] == 2, "Test Case 1 failed: All payments should go to User 2."
        assert tx["amount"] == 30.0, "Test Case 1 failed: All payments should be $30.0."
    print("-> Test Case 1 PASSED.")

    # Test Case 2: Complex 4-user group
    # User 1 owes $100, User 3 owes $20, User 4 owes $30. User 2 is owed $150.
    # Sum: -100 - 20 - 30 + 150 = 0
    balances_2 = {
        1: -100.0,
        2: 150.0,
        3: -20.0,
        4: -30.0
    }

    print(f"\n[Test Case 2] Input Balances: {balances_2}")
    res_2 = engine_wrapper.solve_settlements(balances_2)
    print(f"[Test Case 2] Optimized Transactions: {res_2}")

    # Debits: 100, 30, 20. Credit: 150.
    # Expected: 3 transactions, transferring all funds to User 2.
    assert len(res_2) == 3, "Test Case 2 failed: Expected 3 transactions."
    total_settled = sum(tx["amount"] for tx in res_2)
    assert abs(total_settled - 150.0) < 1e-4, "Test Case 2 failed: Total settled should equal $150.0."
    print("-> Test Case 2 PASSED.")

    # Test Case 3: Empty Group / Settled Group
    balances_3 = {
        1: 0.0,
        2: 0.0
    }
    print(f"\n[Test Case 3] Input Balances: {balances_3}")
    res_3 = engine_wrapper.solve_settlements(balances_3)
    print(f"[Test Case 3] Optimized Transactions: {res_3}")
    assert len(res_3) == 0, "Test Case 3 failed: Expected 0 transactions."
    print("-> Test Case 3 PASSED.")

    print("\n==================================================")
    print("       ALL CORE ENGINE TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
