package com.visemepal.android

import android.app.Application
import com.visemepal.android.data.api.NetworkModule
import com.visemepal.android.data.model.EvaluateResult
import com.visemepal.android.data.model.Lesson
import com.visemepal.android.data.repository.VisemePalRepository

class VisemePalApp : Application() {
    val repository: VisemePalRepository by lazy { VisemePalRepository(NetworkModule.api) }

    var lastLesson: Lesson? = null
    var lastResult: EvaluateResult? = null
}
