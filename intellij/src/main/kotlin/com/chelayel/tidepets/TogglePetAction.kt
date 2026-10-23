package com.chelayel.tidepets

import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.DumbAwareToggleAction
import com.intellij.openapi.project.ProjectManager
import com.intellij.openapi.wm.ToolWindowManager

/** Tools → Show Tide Pet: shows or hides the pet's tool window in every open project. */
class TogglePetAction : DumbAwareToggleAction() {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT

    override fun isSelected(e: AnActionEvent) = PetSettings.get().state.enabled

    override fun setSelected(e: AnActionEvent, state: Boolean) {
        PetSettings.get().state.enabled = state
        for (project in ProjectManager.getInstance().openProjects) {
            val window = ToolWindowManager.getInstance(project).getToolWindow(PetToolWindowFactory.ID) ?: continue
            window.isAvailable = state
            if (state && project == e.project) window.show()
        }
    }
}
