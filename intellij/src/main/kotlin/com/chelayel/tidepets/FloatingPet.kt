package com.chelayel.tidepets

import com.chelayel.tidepets.pet.BubbleStyle
import com.chelayel.tidepets.pet.PetBrain
import com.chelayel.tidepets.pet.PetPainter
import com.intellij.ui.JBColor
import com.intellij.util.ui.JBFont
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import java.awt.Cursor
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent
import javax.swing.JComponent

/**
 * The pet, drawn over the bottom edge of the editor. It only claims the mouse over the
 * pet itself ([contains]), so clicks and scrolling anywhere else reach the editor.
 */
class FloatingPet(val brain: PetBrain) : JComponent() {
    val painter = PetPainter(scale = JBUI.scale(1) * 0.62)

    init {
        isOpaque = false
        cursor = Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)
        toolTipText = null
        addMouseListener(object : MouseAdapter() {
            override fun mouseClicked(e: MouseEvent) { brain.clicked(); repaint() }
        })
    }

    /** Room above the pet for its speech bubble. */
    val preferredHeight get() = (painter.spriteHeight + JBUI.scale(44)).toInt()

    override fun contains(x: Int, y: Int): Boolean {
        val (ox, oy) = painter.origin(brain, height.toDouble())
        return x >= ox && x <= ox + painter.spriteWidth && y >= oy && y <= oy + painter.spriteHeight
    }

    override fun paintComponent(g: Graphics) {
        val style = BubbleStyle(
            text = UIUtil.getLabelForeground(),
            background = JBColor.namedColor("ToolTip.background", UIUtil.getPanelBackground()),
            border = JBColor.border(),
            font = JBFont.small(),
        )
        painter.paint(g as Graphics2D, brain, width.toDouble(), height.toDouble(), style)
    }
}
