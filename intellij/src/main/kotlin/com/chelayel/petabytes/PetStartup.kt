package com.chelayel.petabytes

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.ProjectActivity
import kotlinx.coroutines.delay

class PetStartup : ProjectActivity {
    override suspend fun execute(project: Project) {
        ApplicationManager.getApplication().invokeLater({ project.service<PetService>().refresh() }, project.disposed)
        // Not as the IDE opens: a few minutes into the first project.
        delay(3 * 60 * 1000L)
        if (!project.isDisposed) SupportReminder.askIfDue(project)
    }
}
