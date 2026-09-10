package com.visemepal.android.audio

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File

class PracticeRecorder(private val context: Context) {
    private var recorder: MediaRecorder? = null
    var outputFile: File? = null
        private set

    fun start() {
        val file = File(context.cacheDir, "practice.m4a")
        val mediaRecorder = createRecorder().apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setOutputFile(file.absolutePath)
            prepare()
            start()
        }
        recorder = mediaRecorder
        outputFile = file
    }

    fun stop() {
        runCatching {
            recorder?.apply {
                stop()
                release()
            }
        }
        recorder = null
    }

    @Suppress("DEPRECATION")
    private fun createRecorder(): MediaRecorder {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            MediaRecorder()
        }
    }
}
