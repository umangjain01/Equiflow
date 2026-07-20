#include "engine.h"
#include <queue>
#include <vector>
#include <cmath>
#include <algorithm>

extern "C" {
    int minimize_cash_flow(
        const UserBalance* balances, 
        int num_balances, 
        Transaction* out_transactions, 
        int max_out_transactions
    ) {
        // Validation guards
        if (!balances || num_balances <= 1 || !out_transactions || max_out_transactions <= 0) {
            return 0;
        }

        // Max-heaps sorting by balance value (descending). 
        // pair format: <absolute_value_of_balance, user_id>
        std::priority_queue<std::pair<double, int>> creditors;
        std::priority_queue<std::pair<double, int>> debtors;

        for (int i = 0; i < num_balances; ++i) {
            double bal = balances[i].balance;
            int uid = balances[i].user_id;

            if (bal > 1e-5) {
                creditors.push({bal, uid});
            } else if (bal < -1e-5) {
                debtors.push({std::abs(bal), uid});
            }
        }

        int transaction_count = 0;

        // Greedy matching loop
        while (!creditors.empty() && !debtors.empty() && transaction_count < max_out_transactions) {
            auto cred = creditors.top();
            creditors.pop();

            auto deb = debtors.top();
            debtors.pop();

            double cred_val = cred.first;
            int cred_id = cred.second;

            double deb_val = deb.first;
            int deb_id = deb.second;

            // Determine the settlement amount
            double settle_amt = std::min(cred_val, deb_val);

            // Record transaction: Debtor pays Creditor
            out_transactions[transaction_count].from_user_id = deb_id;
            out_transactions[transaction_count].to_user_id = cred_id;
            out_transactions[transaction_count].amount = settle_amt;
            transaction_count++;

            // Subtract settled amount
            cred_val -= settle_amt;
            deb_val -= settle_amt;

            // Re-queue remaining balances if they exceed floating point epsilon
            if (cred_val > 1e-5) {
                creditors.push({cred_val, cred_id});
            }
            if (deb_val > 1e-5) {
                debtors.push({deb_val, deb_id});
            }
        }

        return transaction_count;
    }
}
