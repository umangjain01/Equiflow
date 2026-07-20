package com.equiflow.api

import com.equiflow.model.*
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

/**
 * Retrofit interface defining EquiFlow client-server API interactions.
 */
interface ApiService {

    /**
     * Authenticates user credentials and retrieves JWT auth token.
     */
    @POST("login")
    suspend fun login(
        @Body loginRequest: LoginRequest
    ): Response<TokenResponse>

    /**
     * Submits an expense with complex split requirements to a specific group.
     */
    @POST("groups/{group_id}/add-expense")
    suspend fun addExpense(
        @Path("group_id") groupId: Int,
        @Body expenseRequest: ExpenseCreateRequest
    ): Response<ExpenseResponse>

    /**
     * Triggers the optimization engine, returning simplified transactions list.
     */
    @GET("groups/{group_id}/settle-up")
    suspend fun settleUp(
        @Path("group_id") groupId: Int
    ): Response<List<TransactionResponse>>

    /**
     * Gathers spending aggregations and MoM statistics.
     */
    @GET("groups/{group_id}/insights")
    suspend fun getInsights(
        @Path("group_id") groupId: Int
    ): Response<InsightsResponse>
}
