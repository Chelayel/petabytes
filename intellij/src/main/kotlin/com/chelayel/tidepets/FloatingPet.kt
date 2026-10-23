package com.chelayel.tidepets

import com.chelayel.tidepets.pet.BubbleStyle
import com.chelayel.tidepets.pet.PetBrain
import com.chelayel.tidepets.pet.PetPainter
import com.intellij.openapi.actionSystem.ActionManager
import com.intellij.openapi.actionSystem.ActionPlaces
import com.intellij.openapi.actionSystem.ActionGroup
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
import javax.swing.SwingUtilities
import kotlin.math.abs

/**
 * The pet, drawn over the bottom edge of the editor. It only claims the mouse over the
 * pet itself ([contains]), and not at all while it's out of the way of the caret, so
 * clicks and scrolling anywhere else reach the editor. Drag it to where it should stay;
 * right-click it for its menu.
 */
class FloatingPet(val brain: PetBrain, scale: Double, private val onDropped: (Double) -> Unit) : JComponent() {
    val painter = PetPainter(scale = JBUI.scale(1) * scale)
    private var pressX = 0
    private var grabOffset = 0.0
    private var moved = false

    init {
        isOpaque = false
        cursor = Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)
        val mouse = object : MouseAdapter() {
            override fun mousePressed(e: MouseEvent) {
                if (e.isPopupTrigger) { menu(e); return }
                if (!SwingUtilities.isLeftMouseButton(e)) return
                pressX = e.x
                grabOffset = e.x - brain.x
                moved = false
            }

            override fun mouseDragged(e: MouseEvent) {
                if (!SwingUtilities.isLeftMouseButton(e)) return
                if (!moved && abs(e.x - pressX) < JBUI.scale(4)) return
                moved = true
                brain.dragging = true
                cursor = Cursor.getPredefinedCursor(Cursor.MOVE_CURSOR)
                brain.dragTo(e.x - grabOffset, width.toDouble(), painter.spriteWidth)
                repaint()
            }

            override fun mouseReleased(e: MouseEvent) {
                if (e.isPopupTrigger) { menu(e); return }
                if (!SwingUtilities.isLeftMouseButton(e)) return
                cursor = Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)
                if (moved) {
                    brain.dropped(width.toDouble(), painter.spriteWidth)
                    onDropped(brain.home)
                } else if (e.clickCount == 2) {
                    brain.react("pet")
                } else {
                    brain.clicked()
                }
                moved = false
                repaint()
            }
        }
        addMouseListener(mouse)
        addMouseMotionListener(mouse)
    }

    private fun menu(e: MouseEvent) {
        val group = ActionManager.getInstance().getAction("TidePets.Menu") as? ActionGroup ?: return
        ActionManager.getInstance().createActionPopupMenu(ActionPlaces.POPUP, group).component.show(this, e.x, e.y)
    }

    /** Room above the pet for its speech bubble. */
    val preferredHeight get() = (painter.spriteHeight + JBUI.scale(44)).toInt()

    /** The pet's own rectangle, in this component's coordinates. */
    fun petBounds(): java.awt.geom.Rectangle2D {
        val (ox, oy) = painter.origin(brain, height.toDouble())
        return java.awt.geom.Rectangle2D.Double(ox, oy, painter.spriteWidth, painter.spriteHeight)
    }

    override fun contains(x: Int, y: Int): Boolean =
        (brain.dragging || !brain.dodging) && petBounds().contains(x.toDouble(), y.toDouble())

    override fun paintComponent(g: Graphics) {
        val style = BubbleStyle(
            text = UIUtil.getLabelForeground(),
            background = JBColor.namedColor("ToolTip.background", UIUtil.getPanelBackground()),
            border = JBColor.border(),
            font = JBFont.small(),
        )
        val fade = if (brain.dodging && !brain.dragging) 0.22f else 1f
        painter.paint(g as Graphics2D, brain, width.toDouble(), height.toDouble(), style, fade)
    }
}
