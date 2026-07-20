package com.equiflow.model

import com.google.gson.annotations.SerializedName

/**
 * Request payload for user authentication.
 */
data class LoginRequest(
    @SerializedName("username") val username: String,
    @SerializedName("password") val password: String
)

/**
 * Response payload containing the security token.
 */
data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String
)

/**
 * Model representing how an individual participant shares an expense.
 */
data class SplitInput(
    @SerializedName("user_id") val userId: Int,
    @SerializedName("amount_owed") val amountOwed: Double? = null
)

/**
 * Payload sent to create a group expense transaction.
 */
data class ExpenseCreateRequest(
    @SerializedName("description") val description: String,
    @SerializedName("amount") val amount: Double,
    @SerializedName("paid_by_id") val paidById: Int,
    @SerializedName("split_type") val splitType: String, // "EQUAL" or "EXACT"
    @SerializedName("category") val category: String? = null,
    @SerializedName("splits") val splits: List<SplitInput>
)

/**
 * Individual split response representation.
 */
data class SplitResponse(
    @SerializedName("user_id") val userId: Int,
    @SerializedName("amount_owed") val amountOwed: Double
)

/**
 * Structure of a successfully added group expense response.
 */
data class ExpenseResponse(
    @SerializedName("id") val id: Int,
    @SerializedName("group_id") val groupId: Int,
    @SerializedName("description") val description: String,
    @SerializedName("amount") val amount: Double,
    @SerializedName("paid_by_id") val paidById: Int,
    @SerializedName("split_type") val splitType: String,
    @SerializedName("category") val category: String?,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("splits") val splits: List<SplitResponse>
)

/**
 * Instruction mapping returned by the C++ engine to optimize group cash flow.
 * Shows who owes whom, and how much to pay.
 */
data class TransactionResponse(
    @SerializedName("from_user_id") val fromUserId: Int,
    @SerializedName("to_user_id") val toUserId: Int,
    @SerializedName("amount") val amount: Double
)

/**
 * Output data containing aggregated group analytics.
 */
data class InsightsResponse(
    @SerializedName("total_spending_by_category") val totalSpendingByCategory: Map<String, Double>,
    @SerializedName("month_over_month_spend") val monthOverMonthSpend: Map<String, Double>
)
