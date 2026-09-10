package com.visemepal.android.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Lesson(
    val id: Int,
    val title: String,
    val text: String,
    val ipa: String,
    @SerialName("audio_url") val audioUrl: String? = null,
    @SerialName("target_phonemes") val targetPhonemes: List<String> = emptyList(),
    val level: String,
    val tip: String = "",
)

@Serializable
data class PhonemeError(
    val phoneme: String,
    val expected: String,
    val actual: String? = null,
    val severity: String = "medium",
    val tip: String = "",
)

@Serializable
data class EvaluateResult(
    @SerialName("lesson_id") val lessonId: Int,
    @SerialName("overall_score") val overallScore: Double,
    val accuracy: Double,
    val fluency: Double,
    val completeness: Double,
    @SerialName("error_phonemes") val errorPhonemes: List<PhonemeError> = emptyList(),
    val tips: List<String> = emptyList(),
    @SerialName("record_id") val recordId: Int? = null,
)

@Serializable
data class Viseme(
    val phoneme: String,
    @SerialName("mouth_shape") val mouthShape: String,
    @SerialName("tongue_position") val tonguePosition: String,
    @SerialName("animation_key") val animationKey: String,
    val description: String,
    @SerialName("child_tip") val childTip: String,
)

@Serializable
data class PracticeRecord(
    val id: Int,
    @SerialName("lesson_id") val lessonId: Int,
    @SerialName("overall_score") val overallScore: Double,
    @SerialName("error_phonemes") val errorPhonemes: List<String> = emptyList(),
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class RecommendItem(
    @SerialName("lesson_id") val lessonId: Int? = null,
    val title: String,
    val text: String,
    val reason: String,
    @SerialName("focus_phonemes") val focusPhonemes: List<String> = emptyList(),
)

@Serializable
data class RecommendPlan(
    @SerialName("plan_title") val planTitle: String,
    val summary: String,
    val items: List<RecommendItem> = emptyList(),
)
