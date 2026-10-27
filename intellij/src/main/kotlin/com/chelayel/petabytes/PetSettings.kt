package com.chelayel.petabytes

import com.intellij.openapi.components.BaseState
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.SimplePersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.service

/** Whether the pet is shown, which one, and its name. Shared by every open project. */
@Service(Service.Level.APP)
@State(name = "Petabytes", storages = [Storage("petabytes.xml")])
class PetSettings : SimplePersistentStateComponent<PetSettings.Options>(Options()) {
    class Options : BaseState() {
        var enabled by property(true)
        var pet by string("turtle")
        /** Empty: the pet's own name (Shelly, Bloop, ...). */
        var name by string("")
        /** right: swims up and down a strip at the editor's right edge. bottom: along the bottom edge. */
        var position by string("right")
        /** True: swims the length of its edge. False: stays where it was dropped. */
        var roam by property(true)
        /** Where it stays when not roaming, as a fraction of the editor's width. */
        var home by property(0.95f)
        /** small, medium or large. */
        var size by string("medium")
        /** When the pet was first seen, for asking for a rating after a week (milliseconds; 0 until then). */
        var firstSeen by property(0L)
        /** When to next ask for a rating or a coffee; Long.MAX_VALUE once answered or turned down for good. */
        var askForSupportAfter by property(0L)
    }

    companion object {
        fun get(): PetSettings = service()

        /** Art units to pixels, before the IDE's own UI scale. */
        fun scaleFor(size: String?) = when (size) { "small" -> 0.48; "large" -> 0.8; else -> 0.62 }
    }
}
