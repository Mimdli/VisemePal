package com.visemepal.android.ui

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.visemepal.android.data.model.EvaluateResult
import com.visemepal.android.data.model.Lesson
import com.visemepal.android.data.model.PracticeRecord
import com.visemepal.android.data.model.RecommendPlan
import com.visemepal.android.data.model.Viseme
import com.visemepal.android.data.repository.VisemePalRepository
import kotlinx.coroutines.launch
import java.io.File

data class HomeUiState(
    val loading: Boolean = true,
    val lessons: List<Lesson> = emptyList(),
    val error: String? = null,
)

class HomeViewModel(private val repository: VisemePalRepository) : ViewModel() {
    var uiState by mutableStateOf(HomeUiState())
        private set

    init {
        refresh()
    }

    fun refresh() {
        uiState = uiState.copy(loading = true, error = null)
        viewModelScope.launch {
            runCatching { repository.lessons() }
                .onSuccess { uiState = HomeUiState(loading = false, lessons = it) }
                .onFailure { uiState = HomeUiState(loading = false, error = it.message ?: "加载失败") }
        }
    }

    companion object {
        fun factory(repository: VisemePalRepository) = simpleFactory { HomeViewModel(repository) }
    }
}

data class PracticeUiState(
    val loading: Boolean = true,
    val lesson: Lesson? = null,
    val recording: Boolean = false,
    val hasAudio: Boolean = false,
    val submitting: Boolean = false,
    val error: String? = null,
)

class PracticeViewModel(
    private val lessonId: Int,
    private val repository: VisemePalRepository,
) : ViewModel() {
    var uiState by mutableStateOf(PracticeUiState())
        private set

    init {
        viewModelScope.launch {
            runCatching { repository.lesson(lessonId) }
                .onSuccess { uiState = PracticeUiState(loading = false, lesson = it) }
                .onFailure {
                    uiState = PracticeUiState(loading = false, error = it.message ?: "课程加载失败")
                }
        }
    }

    fun setRecording(recording: Boolean, hasAudio: Boolean = uiState.hasAudio) {
        uiState = uiState.copy(recording = recording, hasAudio = hasAudio, error = null)
    }

    suspend fun submit(audio: File): EvaluateResult {
        uiState = uiState.copy(submitting = true, error = null)
        return try {
            repository.evaluate(lessonId, audio).also {
                uiState = uiState.copy(submitting = false)
            }
        } catch (error: Exception) {
            uiState = uiState.copy(submitting = false, error = error.message ?: "评测失败")
            throw error
        }
    }

    companion object {
        fun factory(lessonId: Int, repository: VisemePalRepository) =
            simpleFactory { PracticeViewModel(lessonId, repository) }
    }
}

data class VisemeUiState(
    val loading: Boolean = true,
    val viseme: Viseme? = null,
    val error: String? = null,
)

class VisemeViewModel(
    phoneme: String,
    repository: VisemePalRepository,
) : ViewModel() {
    var uiState by mutableStateOf(VisemeUiState())
        private set

    init {
        viewModelScope.launch {
            runCatching { repository.viseme(phoneme) }
                .onSuccess { uiState = VisemeUiState(loading = false, viseme = it) }
                .onFailure {
                    uiState = VisemeUiState(loading = false, error = it.message ?: "可视化资源加载失败")
                }
        }
    }

    companion object {
        fun factory(phoneme: String, repository: VisemePalRepository) =
            simpleFactory { VisemeViewModel(phoneme, repository) }
    }
}

data class PlanUiState(
    val loading: Boolean = true,
    val plan: RecommendPlan? = null,
    val error: String? = null,
)

class PlanViewModel(private val repository: VisemePalRepository) : ViewModel() {
    var uiState by mutableStateOf(PlanUiState())
        private set

    init {
        refresh()
    }

    fun refresh() {
        uiState = uiState.copy(loading = true, error = null)
        viewModelScope.launch {
            runCatching { repository.recommend() }
                .onSuccess { uiState = PlanUiState(loading = false, plan = it) }
                .onFailure { uiState = PlanUiState(loading = false, error = it.message ?: "计划加载失败") }
        }
    }

    companion object {
        fun factory(repository: VisemePalRepository) = simpleFactory { PlanViewModel(repository) }
    }
}

data class RecordsUiState(
    val loading: Boolean = true,
    val records: List<PracticeRecord> = emptyList(),
    val error: String? = null,
)

class RecordsViewModel(private val repository: VisemePalRepository) : ViewModel() {
    var uiState by mutableStateOf(RecordsUiState())
        private set

    init {
        refresh()
    }

    fun refresh() {
        uiState = uiState.copy(loading = true, error = null)
        viewModelScope.launch {
            runCatching { repository.records() }
                .onSuccess { uiState = RecordsUiState(loading = false, records = it) }
                .onFailure {
                    uiState = RecordsUiState(loading = false, error = it.message ?: "记录加载失败")
                }
        }
    }

    companion object {
        fun factory(repository: VisemePalRepository) = simpleFactory { RecordsViewModel(repository) }
    }
}

private fun <T : ViewModel> simpleFactory(create: () -> T): ViewModelProvider.Factory {
    return object : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <VM : ViewModel> create(modelClass: Class<VM>): VM = create() as VM
    }
}
