package com.visemepal.android.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.visemepal.android.ui.VisemeUiState

@Composable
fun VisemeScreen(state: VisemeUiState) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("口型与舌位", style = MaterialTheme.typography.headlineMedium)
        when {
            state.loading -> CircularProgressIndicator()
            state.error != null -> Text(state.error)
            state.viseme != null -> {
                val viseme = state.viseme
                Text("/${viseme.phoneme}/", style = MaterialTheme.typography.displaySmall)
                Text("口型：${viseme.mouthShape}")
                Text("舌位：${viseme.tonguePosition}")
                Text(viseme.childTip)
                Text(
                    "数字人动画资源：${viseme.animationKey}",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}
