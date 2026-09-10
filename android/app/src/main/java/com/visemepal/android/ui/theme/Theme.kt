package com.visemepal.android.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val ColorScheme = lightColorScheme(
    primary = TealPrimary,
    onPrimary = Cream,
    secondary = Coral,
    background = Cream,
    surface = Cream,
    onBackground = Ink,
    onSurface = Ink,
)

@Composable
fun VisemePalTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = ColorScheme,
        typography = Typography,
        content = content,
    )
}
