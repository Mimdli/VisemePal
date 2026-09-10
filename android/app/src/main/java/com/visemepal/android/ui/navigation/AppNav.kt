package com.visemepal.android.ui.navigation

import android.net.Uri
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoStories
import androidx.compose.material.icons.outlined.History
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.visemepal.android.VisemePalApp
import com.visemepal.android.ui.HomeViewModel
import com.visemepal.android.ui.PlanViewModel
import com.visemepal.android.ui.PracticeViewModel
import com.visemepal.android.ui.RecordsViewModel
import com.visemepal.android.ui.VisemeViewModel
import com.visemepal.android.ui.screens.HomeScreen
import com.visemepal.android.ui.screens.PlanScreen
import com.visemepal.android.ui.screens.PracticeScreen
import com.visemepal.android.ui.screens.RecordsScreen
import com.visemepal.android.ui.screens.ResultScreen
import com.visemepal.android.ui.screens.VisemeScreen

private const val ROUTE_HOME = "home"
private const val ROUTE_PLAN = "plan"
private const val ROUTE_RECORDS = "records"
private const val ROUTE_PRACTICE = "practice/{lessonId}"
private const val ROUTE_RESULT = "result"
private const val ROUTE_VISEME = "viseme/{phoneme}"

@Composable
fun AppNav() {
    val navController = rememberNavController()
    val app = LocalContext.current.applicationContext as VisemePalApp
    val backStack by navController.currentBackStackEntryAsState()
    val current = backStack?.destination?.route
    val tabs = listOf(ROUTE_HOME, ROUTE_PLAN, ROUTE_RECORDS)

    Scaffold(
        bottomBar = {
            if (current in tabs) {
                NavigationBar {
                    NavigationBarItem(
                        selected = current == ROUTE_HOME,
                        onClick = { navController.navigateTab(ROUTE_HOME) },
                        icon = { Icon(Icons.Outlined.AutoStories, contentDescription = "练习") },
                        label = { Text("练习") },
                    )
                    NavigationBarItem(
                        selected = current == ROUTE_PLAN,
                        onClick = { navController.navigateTab(ROUTE_PLAN) },
                        icon = { Icon(Icons.Outlined.Star, contentDescription = "计划") },
                        label = { Text("计划") },
                    )
                    NavigationBarItem(
                        selected = current == ROUTE_RECORDS,
                        onClick = { navController.navigateTab(ROUTE_RECORDS) },
                        icon = { Icon(Icons.Outlined.History, contentDescription = "记录") },
                        label = { Text("记录") },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = ROUTE_HOME,
            modifier = Modifier.padding(padding),
        ) {
            composable(ROUTE_HOME) {
                val vm = viewModel<HomeViewModel>(factory = HomeViewModel.factory(app.repository))
                HomeScreen(
                    state = vm.uiState,
                    onRetry = vm::refresh,
                    onOpenLesson = { lesson ->
                        app.lastLesson = lesson
                        navController.navigate("practice/${lesson.id}")
                    },
                )
            }
            composable(ROUTE_PLAN) {
                val vm = viewModel<PlanViewModel>(factory = PlanViewModel.factory(app.repository))
                PlanScreen(state = vm.uiState, onRetry = vm::refresh)
            }
            composable(ROUTE_RECORDS) {
                val vm = viewModel<RecordsViewModel>(factory = RecordsViewModel.factory(app.repository))
                RecordsScreen(state = vm.uiState, onRetry = vm::refresh)
            }
            composable(
                ROUTE_PRACTICE,
                arguments = listOf(navArgument("lessonId") { type = NavType.IntType }),
            ) { entry ->
                val lessonId = entry.arguments?.getInt("lessonId") ?: return@composable
                val vm = viewModel<PracticeViewModel>(
                    factory = PracticeViewModel.factory(lessonId, app.repository),
                )
                PracticeScreen(
                    state = vm.uiState,
                    viewModel = vm,
                    onEvaluated = { lesson, result ->
                        app.lastLesson = lesson
                        app.lastResult = result
                        navController.navigate(ROUTE_RESULT)
                    },
                )
            }
            composable(ROUTE_RESULT) {
                ResultScreen(
                    lesson = app.lastLesson,
                    result = app.lastResult,
                    onOpenViseme = { phoneme ->
                        navController.navigate("viseme/${Uri.encode(phoneme)}")
                    },
                )
            }
            composable(
                ROUTE_VISEME,
                arguments = listOf(navArgument("phoneme") { type = NavType.StringType }),
            ) { entry ->
                val phoneme = Uri.decode(entry.arguments?.getString("phoneme").orEmpty())
                val vm = viewModel<VisemeViewModel>(
                    factory = VisemeViewModel.factory(phoneme, app.repository),
                )
                VisemeScreen(state = vm.uiState)
            }
        }
    }
}

private fun NavHostController.navigateTab(route: String) {
    navigate(route) {
        popUpTo(graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
