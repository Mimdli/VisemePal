package com.visemepal.android.ui.screens

import android.Manifest
import android.media.MediaPlayer
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.visemepal.android.audio.PracticeRecorder
import com.visemepal.android.data.model.EvaluateResult
import com.visemepal.android.data.model.Lesson
import com.visemepal.android.ui.PracticeUiState
import com.visemepal.android.ui.PracticeViewModel
import kotlinx.coroutines.launch

@Composable
fun PracticeScreen(
    state: PracticeUiState,
    viewModel: PracticeViewModel,
    onEvaluated: (Lesson, EvaluateResult) -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val recorder = remember { PracticeRecorder(context) }
    DisposableEffect(Unit) {
        onDispose { recorder.stop() }
    }

    val permission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) {
            recorder.start()
            viewModel.setRecording(true)
        } else {
            Toast.makeText(context, "需要麦克风权限才能跟读", Toast.LENGTH_SHORT).show()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        when {
            state.loading -> CircularProgressIndicator()
            state.lesson == null -> Text(state.error ?: "没有找到这一课")
            else -> {
                val lesson = state.lesson
                Text(lesson.title, style = MaterialTheme.typography.titleMedium)
                Text(lesson.text, style = MaterialTheme.typography.displaySmall)
                Text(lesson.ipa, color = MaterialTheme.colorScheme.primary)
                Text(lesson.tip)
                OutlinedButton(
                    onClick = {
                        val url = lesson.audioUrl
                        if (url.isNullOrBlank()) {
                            Toast.makeText(context, "示范音频稍后接入", Toast.LENGTH_SHORT).show()
                        } else {
                            runCatching {
                                MediaPlayer().apply {
                                    setDataSource(url)
                                    prepare()
                                    start()
                                }
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("听示范") }
                Button(
                    onClick = {
                        if (state.recording) {
                            recorder.stop()
                            viewModel.setRecording(recording = false, hasAudio = recorder.outputFile != null)
                        } else {
                            permission.launch(Manifest.permission.RECORD_AUDIO)
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text(if (state.recording) "停止录音" else "开始跟读") }
                Button(
                    onClick = {
                        val audio = recorder.outputFile
                        val currentLesson = state.lesson
                        if (audio == null || currentLesson == null) {
                            Toast.makeText(context, "请先录一段跟读", Toast.LENGTH_SHORT).show()
                            return@Button
                        }
                        scope.launch {
                            runCatching { viewModel.submit(audio) }
                                .onSuccess { onEvaluated(currentLesson, it) }
                        }
                    },
                    enabled = state.hasAudio && !state.submitting,
                    modifier = Modifier.fillMaxWidth(),
                ) { Text(if (state.submitting) "正在评测…" else "交给小老师评分") }
                state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        }
    }
}
