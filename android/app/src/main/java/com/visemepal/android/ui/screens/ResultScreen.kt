package com.visemepal.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.visemepal.android.data.model.EvaluateResult
import com.visemepal.android.data.model.Lesson

@Composable
fun ResultScreen(
    lesson: Lesson?,
    result: EvaluateResult?,
    onOpenViseme: (String) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (lesson == null || result == null) {
            Text("还没有评测结果，先去跟读一课吧。")
            return
        }
        Text("评测结果", style = MaterialTheme.typography.headlineMedium)
        Text("${lesson.text}  ${lesson.ipa}")
        Text("总分 ${result.overallScore.toInt()}  准确 ${result.accuracy.toInt()}  流畅 ${result.fluency.toInt()}")
        result.tips.forEach { Text(it) }
        result.errorPhonemes.forEach { error ->
            Text("需要注意的音素：/${error.phoneme}/")
            Button(
                onClick = { onOpenViseme(error.phoneme) },
                modifier = Modifier.fillMaxWidth(),
            ) { Text("看 /${error.phoneme}/ 的口型和舌位") }
        }
    }
}
