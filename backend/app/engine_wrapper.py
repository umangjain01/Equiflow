import os
import ctypes
import logging

logger = logging.getLogger("equiflow.engine")

# 1. Define ctypes structural mappings
class UserBalance(ctypes.Structure):
    _fields_ = [
        ("user_id", ctypes.c_int),
        ("balance", ctypes.c_double),
    ]

class Transaction(ctypes.Structure):
    _fields_ = [
        ("from_user_id", ctypes.c_int),
        ("to_user_id", ctypes.c_int),
        ("amount", ctypes.c_double),
    ]

# 2. Try loading the C++ Shared Library (.so for Linux/Render, .dylib for macOS)
lib = None
lib_filenames = ["libengine.so", "libengine.dylib", "libengine.dll"]
possible_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    os.path.abspath(os.path.dirname(__file__)),
]

for d in possible_dirs:
    for filename in lib_filenames:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            try:
                lib = ctypes.CDLL(path)
                logger.info(f"Successfully loaded C++ Core Engine from {path}")
                break
            except Exception as e:
                logger.error(f"Failed to load compiled library at {path}: {e}")
    if lib:
        break

if lib:
    # Bind arguments & return types
    lib.minimize_cash_flow.argtypes = [
        ctypes.POINTER(UserBalance),  # input balances array
        ctypes.c_int,                 # number of users/balances
        ctypes.POINTER(Transaction),  # output transactions array buffer
        ctypes.c_int                  # max number of elements in output buffer
    ]
    lib.minimize_cash_flow.restype = ctypes.c_int
else:
    logger.warning("C++ Engine (.dylib) not found or failed to load. Falling back to pure Python execution.")

def minimize_cash_flow_python(balances_dict: dict[int, float]) -> list[dict]:
    """Pure Python fallback implementation using heap queues."""
    import heapq
    
    # Filter and separate creditors and debtors
    # Store balances as (neg_value, user_id) to simulate a Max-Heap in Python
    cred_heap = []
    deb_heap = []
    
    for user_id, amount in balances_dict.items():
        if amount > 1e-4:
            heapq.heappush(cred_heap, (-amount, user_id))
        elif amount < -1e-4:
            heapq.heappush(deb_heap, (amount, user_id))  # amount is negative, so this naturally represents max absolute debit
            
    transactions = []
    while cred_heap and deb_heap:
        neg_cred_val, cred_id = heapq.heappop(cred_heap)
        neg_deb_val, deb_id = heapq.heappop(deb_heap)
        
        cred_val = -neg_cred_val
        deb_val = -neg_deb_val
        
        settle_amt = min(cred_val, deb_val)
        transactions.append({
            "from_user_id": deb_id,
            "to_user_id": cred_id,
            "amount": round(settle_amt, 2)
        })
        
        cred_val -= settle_amt
        deb_val -= settle_amt
        
        if cred_val > 1e-4:
            heapq.heappush(cred_heap, (-cred_val, cred_id))
        if deb_val > 1e-4:
            heapq.heappush(deb_heap, (-deb_val, deb_id))
            
    return transactions

def solve_settlements(balances_dict: dict[int, float]) -> list[dict]:
    """
    Solves debt optimization.
    Delegates to C++ engine if loaded, otherwise falls back to Python execution.
    """
    if not lib:
        return minimize_cash_flow_python(balances_dict)
    
    # 1. Convert input dict into ctypes UserBalance array
    num_balances = len(balances_dict)
    if num_balances == 0:
        return []
        
    balance_array_type = UserBalance * num_balances
    c_balances = balance_array_type()
    
    for i, (user_id, val) in enumerate(balances_dict.items()):
        c_balances[i].user_id = user_id
        c_balances[i].balance = val

    # 2. Allocate output buffer (maximum possible transactions is num_balances - 1)
    max_transactions = max(0, num_balances - 1)
    if max_transactions == 0:
        return []
        
    transaction_array_type = Transaction * max_transactions
    c_transactions = transaction_array_type()

    # 3. Call the C++ Shared Library function
    try:
        num_transactions = lib.minimize_cash_flow(
            c_balances,
            num_balances,
            c_transactions,
            max_transactions
        )
        
        # 4. Parse results back to list of dicts
        results = []
        for i in range(num_transactions):
            results.append({
                "from_user_id": c_transactions[i].from_user_id,
                "to_user_id": c_transactions[i].to_user_id,
                "amount": round(c_transactions[i].amount, 2)
            })
        return results
    except Exception as e:
        logger.error(f"Error executing C++ minimize_cash_flow, using Python fallback: {e}")
        return minimize_cash_flow_python(balances_dict)
