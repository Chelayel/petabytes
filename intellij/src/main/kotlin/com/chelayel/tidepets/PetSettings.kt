package com.chelayel.tidepets

import com.intellij.openapi.components.BaseState
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.SimplePersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.service

/** Whether the pet is shown, and its name. Shared by every open project. */
@Service(Service.Level.APP)
@State(name = "TidePets", storages = [Storage("tidePets.xml")])
class PetSettings : SimplePersistentStateComponent<PetSettings.Options>(Options()) {
    class Options : BaseState() {
        var enabled by property(true)
        var name by string("Shelly")
    }

    companion object {
        fun get(): PetSettings = service()
    }
}
