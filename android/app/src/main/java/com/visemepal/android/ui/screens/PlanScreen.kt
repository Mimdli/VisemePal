package com.visemepal.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.visemepal.android.ui.PlanUiState

@Composable
fun PlanScreen(state: PlanUiState, onRetry: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("训练计划", style = MaterialTheme.typography.headlineMedium)
        when {
            state.loading -> CircularProgressIndicator()
            state.error != null -> ErrorPane(state.error, onRetry)
            state.plan != null -> {
                Text(state.plan.planTitle, style = MaterialTheme.typography.titleLarge)
                Text(state.plan.summary)
                state.plan.items.forEach { item ->
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(item.title, style = MaterialTheme.typography.titleMedium)
                            Text(item.text)
                            Text(item.reason, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
    }
}
