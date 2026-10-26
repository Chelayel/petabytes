package com.chelayel.petabytes

import com.chelayel.petabytes.pet.Pet
import com.chelayel.petabytes.pet.PetCatalog
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTabbedPane
import com.intellij.util.ui.JBFont
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import java.awt.AlphaComposite
import java.awt.BasicStroke
import java.awt.BorderLayout
import java.awt.Color
import java.awt.Component
import java.awt.Cursor
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.GridLayout
import java.awt.RenderingHints
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent
import java.awt.geom.Rectangle2D
import java.awt.geom.RoundRectangle2D
import javax.swing.Icon
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.SwingConstants
import kotlin.math.min

/**
 * Choose a Pet: the pets as cards, a tab per set. Clicking a card switches pets straight away; the dialog stays
 * open so you can look around.
 */
class ChoosePetDialog(project: Project?) : DialogWrapper(project) {
    private val catalog = PetCatalog.load()

    init {
        title = "Choose a Pet"
        setOKButtonText("Done")
        init()
    }

    override fun createActions() = arrayOf(okAction)

    override fun createCenterPanel(): JComponent {
        val current = PetSettings.get().state.pet ?: "turtle"
        val cards = mutableListOf<PetCard>()
        val tabs = JBTabbedPane()
        for ((set, title) in SETS) {
            val pets = catalog.pets.values.filter { it.set == set }
            if (pets.isEmpty()) continue
            val grid = JPanel(GridLayout(0, 4, JBUI.scale(10), JBUI.scale(10)))
            grid.border = JBUI.Borders.empty(12)
            for (pet in pets) {
                val card = PetCard(pet) { chosen ->
                    choose(chosen)
                    cards.forEach { it.selected = it.pet.id == chosen.id }
                }
                card.selected = pet.id == current
                cards += card
                grid.add(card)
            }
            // Cards keep their size at the top of the tab instead of stretching to fill it.
            val holder = JPanel(BorderLayout())
            holder.add(grid, BorderLayout.NORTH)
            tabs.addTab(title, JBScrollPane(holder).apply { border = JBUI.Borders.empty() })
            if (set == catalog.pet(current).set) tabs.selectedIndex = tabs.tabCount - 1
        }
        tabs.preferredSize = JBUI.size(660, 470)
        return tabs
    }

    private fun choose(pet: Pet) {
        val s = PetSettings.get().state
        s.pet = pet.id
        s.name = ""
        s.enabled = true
        PetService.refreshAll()
    }

    companion object {
        val SETS = listOf("tide" to "Tide", "home" to "Home", "snacks" to "Snacks", "games" to "Games", "gadgets" to "Gadgets")
    }
}

/** One pet as a card: its picture, name and kind, outlined while it's the chosen one. */
private class PetCard(val pet: Pet, onChoose: (Pet) -> Unit) : JPanel(BorderLayout()) {
    var selected = false
        set(value) { field = value; repaint() }

    init {
        isOpaque = false
        border = JBUI.Borders.empty(8)
        add(JBLabel(PetIcon(pet, 120, 72)).apply { horizontalAlignment = SwingConstants.CENTER }, BorderLayout.CENTER)
        val text = JPanel(GridLayout(2, 1)).apply { isOpaque = false }
        text.add(JBLabel(pet.name, SwingConstants.CENTER).apply { font = JBFont.label().asBold() })
        text.add(JBLabel(pet.label, SwingConstants.CENTER).apply { font = JBFont.small(); foreground = UIUtil.getContextHelpForeground() })
        add(text, BorderLayout.SOUTH)
        cursor = Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)
        toolTipText = "${pet.name} the ${pet.label.lowercase()}"
        addMouseListener(object : MouseAdapter() {
            override fun mouseClicked(e: MouseEvent) = onChoose(pet)
        })
    }

    override fun paintComponent(g: Graphics) {
        val g2 = g.create() as Graphics2D
        try {
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            val arc = JBUI.scale(14).toDouble()
            val box = RoundRectangle2D.Double(1.0, 1.0, width - 2.0, height - 2.0, arc, arc)
            val focus = JBUI.CurrentTheme.Focus.focusColor()
            g2.color = if (selected) Color(focus.red, focus.green, focus.blue, 48) else CARD
            g2.fill(box)
            if (selected) {
                g2.color = focus
                g2.stroke = BasicStroke(JBUI.scale(2).toFloat())
                g2.draw(box)
            }
        } finally {
            g2.dispose()
        }
    }

    companion object {
        private val CARD = JBColor(Color(0, 0, 0, 14), Color(255, 255, 255, 14))
    }
}

/** The pet standing still with its eyes open, as big as fits in the middle of the icon. */
class PetIcon(pet: Pet, private val w: Int, private val h: Int) : Icon {
    private val parts = pet.parts.filter { it.whenFlags == null || "eyesOpen" in it.whenFlags }
    private val box: Rectangle2D = pet.parts.filter { it.whenFlags == null }
        .map { part -> part.shape.bounds2D.also { it.setRect(it.x - part.strokeWidth / 2, it.y - part.strokeWidth / 2, it.width + part.strokeWidth, it.height + part.strokeWidth) } }
        .reduce { a, b -> a.createUnion(b) }

    override fun getIconWidth() = JBUI.scale(w)
    override fun getIconHeight() = JBUI.scale(h)

    override fun paintIcon(c: Component?, g: Graphics, x: Int, y: Int) {
        val g2 = g.create() as Graphics2D
        try {
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g2.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE)
            val scale = min(iconWidth * 0.92 / box.width, iconHeight * 0.92 / box.height)
            g2.translate(x + iconWidth / 2.0, y + iconHeight / 2.0)
            g2.scale(scale, scale)
            g2.translate(-box.centerX, -box.centerY)
            for (part in parts) {
                g2.composite = AlphaComposite.getInstance(AlphaComposite.SRC_OVER, part.opacity)
                part.fill?.let { g2.color = it; g2.fill(part.shape) }
                part.stroke?.let {
                    g2.color = it
                    g2.stroke = BasicStroke(part.strokeWidth, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)
                    g2.draw(part.shape)
                }
            }
        } finally {
            g2.dispose()
        }
    }
}
