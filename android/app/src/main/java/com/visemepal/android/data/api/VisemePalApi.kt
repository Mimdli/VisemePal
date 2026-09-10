package com.visemepal.android.data.api

import com.visemepal.android.data.model.EvaluateResult
import com.visemepal.android.data.model.Lesson
import com.visemepal.android.data.model.PracticeRecord
import com.visemepal.android.data.model.RecommendPlan
import com.visemepal.android.data.model.Viseme
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

interface VisemePalApi {
    @GET("lessons")
    suspend fun listLessons(): List<Lesson>

    @GET("lessons/{id}")
    suspend fun getLesson(@Path("id") id: Int): Lesson

    @Multipart
    @POST("evaluate")
    suspend fun evaluate(
        @Part("lesson_id") lessonId: RequestBody,
        @Part audio: MultipartBody.Part,
    ): EvaluateResult

    @GET("visemes/{phoneme}")
    suspend fun getViseme(@Path("phoneme") phoneme: String): Viseme

    @GET("recommend")
    suspend fun recommend(): RecommendPlan

    @GET("records")
    suspend fun listRecords(): List<PracticeRecord>
}
