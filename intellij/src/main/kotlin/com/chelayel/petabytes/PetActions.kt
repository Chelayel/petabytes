package com.chelayel.petabytes

import com.chelayel.petabytes.pet.PetCatalog
import com.intellij.openapi.actionSystem.ActionGroup
import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.Separator
import com.intellij.openapi.components.service
import com.intellij.openapi.options.ShowSettingsUtil
import com.intellij.openapi.project.DumbAwareAction
import com.intellij.openapi.project.DumbAwareToggleAction

/** Tools → Petabytes: show or hide the pet, pick one, open the settings. */
class PetMenu : ActionGroup() {
    private val children: Array<AnAction> by lazy {
        val pets = PetCatalog.load().pets.values.map { ChoosePet(it.id, "${it.label} (${it.name})") }
        arrayOf(
            FeedPet(), ShowPet(), Roam(),
            Separator.create("Where"), Position("right", "Right Edge (Up and Down)"), Position("bottom", "Bottom Edge"),
            Separator.create("Pet"), *pets.toTypedArray(), Separator.create(), OpenSettings(),
        )
    }

    override fun getChildren(e: AnActionEvent?) = children
}

/** Drops a snack ({ }, [ ], ( ), < > or ;) for the pet to swim over and eat. */
class FeedPet : DumbAwareAction("Feed Pet") {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT
    override fun update(e: AnActionEvent) { e.presentation.isEnabled = e.project != null && PetSettings.get().state.enabled }
    override fun actionPerformed(e: AnActionEvent) { e.project?.service<PetService>()?.feed() }
}

class ShowPet : DumbAwareToggleAction("Show Pet") {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT
    override fun isSelected(e: AnActionEvent) = PetSettings.get().state.enabled
    override fun setSelected(e: AnActionEvent, state: Boolean) {
        PetSettings.get().state.enabled = state
        PetService.refreshAll()
    }
}

/** On: swims the width of the editor. Off: stays where it was dropped (dragging it turns this off). */
class Roam : DumbAwareToggleAction("Swim Along the Edge") {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT
    override fun isSelected(e: AnActionEvent) = PetSettings.get().state.roam
    override fun setSelected(e: AnActionEvent, state: Boolean) {
        PetSettings.get().state.roam = state
        PetService.refreshAll()
    }
}

class Position(private val id: String, label: String) : DumbAwareToggleAction(label) {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT
    override fun isSelected(e: AnActionEvent) = (PetSettings.get().state.position ?: "right") == id
    override fun setSelected(e: AnActionEvent, state: Boolean) {
        PetSettings.get().state.position = id
        PetService.refreshAll()
    }
}

class ChoosePet(private val id: String, label: String) : DumbAwareToggleAction(label) {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT
    override fun isSelected(e: AnActionEvent) = PetSettings.get().state.pet == id
    override fun setSelected(e: AnActionEvent, state: Boolean) {
        val s = PetSettings.get().state
        s.pet = id
        s.enabled = true
        PetService.refreshAll()
    }
}

class OpenSettings : DumbAwareAction("Settings…") {
    override fun actionPerformed(e: AnActionEvent) {
        ShowSettingsUtil.getInstance().showSettingsDialog(e.project, PetConfigurable::class.java)
    }
}
