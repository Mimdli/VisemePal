package com.visemepal.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.visemepal.android.ui.RecordsUiState

@Composable
fun RecordsScreen(state: RecordsUiState, onRetry: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("练习记录", style = MaterialTheme.typography.headlineMedium)
        when {
            state.loading -> CircularProgressIndicator()
            state.error != null -> ErrorPane(state.error, onRetry)
            state.records.isEmpty() -> Text("还没有练习，先去跟读一课吧。")
            else -> LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                items(state.records, key = { it.id }) { record ->
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("课程 #${record.lessonId}  分数 ${record.overallScore.toInt()}")
                            Text("错误音素：${record.errorPhonemes.joinToString()}")
                            Text(record.createdAt, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
    }
}
