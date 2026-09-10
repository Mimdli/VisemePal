package com.visemepal.android.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.visemepal.android.data.model.Lesson
import com.visemepal.android.ui.HomeUiState

@Composable
fun HomeScreen(
    state: HomeUiState,
    onRetry: () -> Unit,
    onOpenLesson: (Lesson) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
    ) {
        Text("今日跟读", style = MaterialTheme.typography.headlineMedium)
        Text(
            "先听示范，再对着小镜子一样的数字人练习口型。",
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.padding(top = 8.dp, bottom = 16.dp),
        )
        when {
            state.loading -> CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
            state.error != null -> ErrorPane(state.error, onRetry)
            else -> LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 24.dp),
            ) {
                items(state.lessons, key = { it.id }) { lesson ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onOpenLesson(lesson) },
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(lesson.title, style = MaterialTheme.typography.titleMedium)
                            Text(lesson.text, style = MaterialTheme.typography.headlineSmall)
                            Text(lesson.ipa, color = MaterialTheme.colorScheme.primary)
                            Text(lesson.tip, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ErrorPane(message: String, onRetry: () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(message)
        Button(onClick = onRetry) { Text("重试") }
    }
}
