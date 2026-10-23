package com.chelayel.tidepets

import com.chelayel.tidepets.pet.PetCatalog
import com.intellij.openapi.options.BoundConfigurable
import com.intellij.openapi.ui.DialogPanel
import com.intellij.ui.dsl.builder.bindItem
import com.intellij.ui.dsl.builder.bindSelected
import com.intellij.ui.dsl.builder.bindText
import com.intellij.ui.dsl.builder.panel
import com.intellij.ui.dsl.listCellRenderer.textListCellRenderer

/** Settings → Tools → Tide Pets. */
class PetConfigurable : BoundConfigurable("Tide Pets") {
    override fun createPanel(): DialogPanel {
        val settings = PetSettings.get().state
        val pets = PetCatalog.load().pets.values.toList()
        return panel {
            row { checkBox("Show a pet along the bottom of the editor").bindSelected(settings::enabled) }
            row("Pet:") {
                comboBox(pets.map { it.id }, textListCellRenderer { id -> pets.find { it.id == id }?.let { "${it.label} (${it.name})" } })
                    .bindItem({ settings.pet ?: "turtle" }, { settings.pet = it ?: "turtle" })
            }
            row("Name:") {
                textField().bindText({ settings.name ?: "" }, { settings.name = it.trim() })
                    .comment("Leave empty for the pet's own name.")
            }
        }
    }

    override fun apply() {
        super.apply()
        PetService.refreshAll()
    }
}
