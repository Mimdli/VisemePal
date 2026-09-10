package com.visemepal.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.visemepal.android.ui.navigation.AppNav
import com.visemepal.android.ui.theme.VisemePalTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            VisemePalTheme {
                AppNav()
            }
        }
    }
}
