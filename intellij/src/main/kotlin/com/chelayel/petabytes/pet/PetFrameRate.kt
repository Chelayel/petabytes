package com.chelayel.petabytes.pet

import java.awt.Component
import java.awt.event.ComponentAdapter
import java.awt.event.ComponentEvent
import java.awt.event.HierarchyBoundsListener
import java.awt.event.HierarchyEvent
import java.awt.event.HierarchyListener

/** Slow while a sleeper is still; smooth while its editor moves or its pose settles. */
class PetFrameRate(private val clock: () -> Long = System::nanoTime) {
    private var smoothUntil = Long.MIN_VALUE

    fun requestSmoothFrames() { smoothUntil = clock() + 350_000_000L }

    fun delayMillis(sleeping: Boolean, settling: Boolean = false, quiet: Boolean = false, hidden: Boolean = false): Int = when {
        hidden -> 250
        sleeping && !settling && clock() >= smoothUntil -> 166
        quiet -> 66
        else -> 33
    }
}

/** The pet is outside the editor's layout, so it must also hear when the editor's ancestors move. */
class EditorLayoutTracker(private val changed: () -> Unit) : ComponentAdapter(), HierarchyBoundsListener, HierarchyListener {
    private var component: Component? = null

    fun watch(next: Component?) {
        if (component === next) return
        component?.removeComponentListener(this)
        component?.removeHierarchyBoundsListener(this)
        component?.removeHierarchyListener(this)
        component = next
        next?.addComponentListener(this)
        next?.addHierarchyBoundsListener(this)
        next?.addHierarchyListener(this)
        if (next != null) changed()
    }

    override fun componentMoved(event: ComponentEvent) = changed()
    override fun componentResized(event: ComponentEvent) = changed()
    override fun ancestorMoved(event: HierarchyEvent) = changed()
    override fun ancestorResized(event: HierarchyEvent) = changed()
    override fun hierarchyChanged(event: HierarchyEvent) {
        if ((event.changeFlags and HierarchyEvent.SHOWING_CHANGED.toLong()) != 0L) changed()
    }
}
