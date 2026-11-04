package com.chelayel.petabytes.pet

import java.awt.event.ComponentEvent
import java.awt.event.HierarchyEvent
import javax.swing.JPanel
import javax.swing.SwingUtilities
import kotlin.test.assertEquals
import org.junit.Test

class PetFrameRateTest {
    @Test fun resizingBoostsSleepingFramesUntilTheLayoutStopsChanging() {
        var now = 0L
        val rate = PetFrameRate { now }
        assertEquals(166, rate.delayMillis(sleeping = true))
        rate.requestSmoothFrames()
        assertEquals(33, rate.delayMillis(sleeping = true))
        now = 300_000_000
        rate.requestSmoothFrames()
        now = 400_000_000
        assertEquals(33, rate.delayMillis(sleeping = true), "A continuing resize must extend smooth updates")
        now = 650_000_001
        assertEquals(166, rate.delayMillis(sleeping = true), "A settled sleeper must return to its low idle rate")
    }

    @Test fun unfinishedPoseTransitionsStaySmoothAndPowerSavingStillApplies() {
        val rate = PetFrameRate { 0 }
        assertEquals(33, rate.delayMillis(sleeping = true, settling = true))
        assertEquals(66, rate.delayMillis(sleeping = true, settling = true, quiet = true))
        assertEquals(166, rate.delayMillis(sleeping = true, quiet = true))
        assertEquals(33, rate.delayMillis(sleeping = false))
        assertEquals(66, rate.delayMillis(sleeping = false, quiet = true))
        rate.requestSmoothFrames()
        assertEquals(250, rate.delayMillis(sleeping = true, hidden = true))
    }

    @Test fun editorAndAncestorLayoutEventsRequestSmoothFrames() {
        var now = 0L
        val rate = PetFrameRate { now }
        val tracker = EditorLayoutTracker(rate::requestSmoothFrames)
        val parent = JPanel(); val editor = JPanel()
        SwingUtilities.invokeAndWait { parent.add(editor); tracker.watch(editor) }
        now += 400_000_000
        assertEquals(166, rate.delayMillis(sleeping = true))
        SwingUtilities.invokeAndWait { editor.dispatchEvent(ComponentEvent(editor, ComponentEvent.COMPONENT_RESIZED)) }
        assertEquals(33, rate.delayMillis(sleeping = true))
        now += 400_000_000
        SwingUtilities.invokeAndWait {
            editor.dispatchEvent(HierarchyEvent(editor, HierarchyEvent.ANCESTOR_RESIZED, parent, parent))
        }
        assertEquals(33, rate.delayMillis(sleeping = true))
        SwingUtilities.invokeAndWait { tracker.watch(null) }
    }

    @Test fun restoringAnEditorHiddenByAMaximizedToolWindowRequestsSmoothFrames() {
        var now = 0L
        val rate = PetFrameRate { now }
        val tracker = EditorLayoutTracker(rate::requestSmoothFrames)
        val parent = JPanel(); val editor = JPanel()
        SwingUtilities.invokeAndWait { parent.add(editor); tracker.watch(editor) }
        now += 400_000_000
        assertEquals(250, rate.delayMillis(sleeping = true, hidden = true))
        SwingUtilities.invokeAndWait {
            editor.dispatchEvent(HierarchyEvent(editor, HierarchyEvent.HIERARCHY_CHANGED, editor, parent, HierarchyEvent.SHOWING_CHANGED.toLong()))
        }
        assertEquals(33, rate.delayMillis(sleeping = true))
        SwingUtilities.invokeAndWait { tracker.watch(null) }
    }

    @Test fun switchingOrHidingTheEditorDetachesItsLayoutListeners() {
        var now = 0L
        val rate = PetFrameRate { now }
        val tracker = EditorLayoutTracker(rate::requestSmoothFrames)
        val first = JPanel(); val second = JPanel()
        SwingUtilities.invokeAndWait { tracker.watch(first); tracker.watch(second) }
        now += 400_000_000
        SwingUtilities.invokeAndWait { first.dispatchEvent(ComponentEvent(first, ComponentEvent.COMPONENT_RESIZED)) }
        assertEquals(166, rate.delayMillis(sleeping = true), "An old editor must not keep the pet running fast")
        SwingUtilities.invokeAndWait { second.dispatchEvent(ComponentEvent(second, ComponentEvent.COMPONENT_MOVED)) }
        assertEquals(33, rate.delayMillis(sleeping = true))
        SwingUtilities.invokeAndWait { tracker.watch(null) }
        now += 400_000_000
        SwingUtilities.invokeAndWait { second.dispatchEvent(ComponentEvent(second, ComponentEvent.COMPONENT_RESIZED)) }
        assertEquals(166, rate.delayMillis(sleeping = true))
    }
}
