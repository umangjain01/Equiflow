#ifndef ENGINE_H
#define ENGINE_H

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

// Represents a user's net credit or debit amount
struct UserBalance {
    int user_id;
    double balance; // positive = creditor, negative = debtor
};

// Represents a simplified transaction where from_user pays to_user
struct Transaction {
    int from_user_id;
    int to_user_id;
    double amount;
};

extern "C" {
    /**
     * Minimizes cash flow among users using a priority queue (max-heap) approach.
     * Takes an array of UserBalance structs, calculates transactions, and populates
     * the out_transactions buffer.
     *
     * Returns: The number of transactions written to out_transactions.
     */
    EXPORT int minimize_cash_flow(
        const UserBalance* balances, 
        int num_balances, 
        Transaction* out_transactions, 
        int max_out_transactions
    );
}

#endif // ENGINE_H
