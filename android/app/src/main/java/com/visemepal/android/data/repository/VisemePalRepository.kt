package com.visemepal.android.data.repository

import com.visemepal.android.data.api.VisemePalApi
import com.visemepal.android.data.model.EvaluateResult
import com.visemepal.android.data.model.Lesson
import com.visemepal.android.data.model.PracticeRecord
import com.visemepal.android.data.model.RecommendPlan
import com.visemepal.android.data.model.Viseme
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class VisemePalRepository(private val api: VisemePalApi) {
    suspend fun lessons(): List<Lesson> = api.listLessons()

    suspend fun lesson(id: Int): Lesson = api.getLesson(id)

    suspend fun evaluate(lessonId: Int, audio: File): EvaluateResult {
        val lessonBody = lessonId.toString().toRequestBody("text/plain".toMediaType())
        val audioPart = MultipartBody.Part.createFormData(
            "audio",
            audio.name,
            audio.asRequestBody("audio/mp4".toMediaType()),
        )
        return api.evaluate(lessonBody, audioPart)
    }

    suspend fun viseme(phoneme: String): Viseme = api.getViseme(phoneme)

    suspend fun recommend(): RecommendPlan = api.recommend()

    suspend fun records(): List<PracticeRecord> = api.listRecords()
}
