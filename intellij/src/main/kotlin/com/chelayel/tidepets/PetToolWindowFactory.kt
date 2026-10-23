package com.chelayel.tidepets

import com.intellij.openapi.project.DumbAware
import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBLabel
import com.intellij.ui.content.ContentFactory
import javax.swing.JComponent

class PetToolWindowFactory : ToolWindowFactory, DumbAware {
    override fun shouldBeAvailable(project: Project) = PetSettings.get().state.enabled

    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val (component, panel) = runCatching { jcefPanel(project) }.getOrElse {
            JBLabel(
                "<html><body style='padding:12px'><b>Tide Pets needs the embedded browser (JCEF).</b><br>" +
                    "This IDE build does not provide it.</body></html>",
            ) to null
        }
        val content = ContentFactory.getInstance().createContent(component, "", false)
        if (panel != null) content.setDisposer(panel)
        toolWindow.contentManager.addContent(content)
    }

    // In its own method so the JCEF classes are only touched when it's used; on an
    // IDE without them the reference throws here, and the fallback above shows.
    private fun jcefPanel(project: Project): Pair<JComponent, PetPanel> {
        check(com.intellij.ui.jcef.JBCefApp.isSupported()) { "JCEF is not supported" }
        val panel = PetPanel(project)
        return panel to panel
    }

    companion object {
        const val ID = "Tide Pets"
    }
}
