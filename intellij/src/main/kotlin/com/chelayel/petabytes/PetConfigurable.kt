package com.chelayel.petabytes

import com.chelayel.petabytes.pet.PetCatalog
import com.intellij.openapi.options.BoundConfigurable
import com.intellij.openapi.ui.DialogPanel
import com.intellij.ui.dsl.builder.bindItem
import com.intellij.ui.dsl.builder.bindSelected
import com.intellij.ui.dsl.builder.bindText
import com.intellij.ui.dsl.builder.panel
import com.intellij.ui.dsl.listCellRenderer.textListCellRenderer
import javax.swing.JLabel
import javax.swing.JTextField

/** Settings → Tools → Petabytes. */
class PetConfigurable : BoundConfigurable("Petabytes") {
    override fun createPanel(): DialogPanel {
        val settings = PetSettings.get().state
        val catalog = PetCatalog.load()
        fun chosen() = catalog.pet(settings.pet).let { "${it.name} the ${it.label.lowercase()}" }
        lateinit var chosenLabel: JLabel
        lateinit var nameField: JTextField
        return panel {
            row { checkBox("Show a pet along the bottom of the editor").bindSelected(settings::enabled) }
            row("Pet:") {
                chosenLabel = label(chosen()).component
                button("Choose…") {
                    ChoosePetDialog(null).show()
                    chosenLabel.text = chosen()
                    // Choosing a pet resets its name; don't let Apply put the old one back.
                    nameField.text = settings.name ?: ""
                }
            }
            row("Where:") {
                comboBox(listOf("right", "bottom"), textListCellRenderer { if (it == "bottom") "Bottom edge of the editor" else "Right edge, swimming up and down" })
                    .bindItem({ settings.position ?: "right" }, { settings.position = it ?: "right" })
            }
            row { checkBox("Swim along the edge (off: stay where it was dropped)").bindSelected(settings::roam) }
                .rowComment("Drag the pet to move it; dropping it turns swimming off. It fades and lets clicks through while you work on a line it covers.")
            row("Size:") {
                comboBox(listOf("small", "medium", "large"), textListCellRenderer { it?.replaceFirstChar(Char::uppercase) })
                    .bindItem({ settings.size ?: "medium" }, { settings.size = it ?: "medium" })
            }
            row("Name:") {
                nameField = textField().bindText({ settings.name ?: "" }, { settings.name = it.trim() })
                    .comment("Leave empty for the pet's own name.").component
            }
        }
    }

    override fun apply() {
        super.apply()
        PetService.refreshAll()
    }
}
