package com.chelayel.petabytes

import com.chelayel.petabytes.pet.PetCatalog
import com.intellij.ide.BrowserUtil
import com.intellij.notification.NotificationAction
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.project.Project
import java.util.concurrent.atomic.AtomicBoolean

/**
 After a week with the pet, asks once for a rating or a coffee. Not Now (or letting the balloon go) asks again
 in a month; rating, the coffee, or Don't Ask Again, and it never asks again.
 */
object SupportReminder {
    private const val DAY = 24L * 60 * 60 * 1000
    private val askedThisSession = AtomicBoolean()

    fun askIfDue(project: Project) {
        val s = PetSettings.get().state
        val now = System.currentTimeMillis()
        if (s.firstSeen == 0L) s.firstSeen = now
        val due = if (s.askForSupportAfter == 0L) s.firstSeen + 7 * DAY else s.askForSupportAfter
        if (now < due || !askedThisSession.compareAndSet(false, true)) return
        // Until it's answered, it counts as Not Now.
        s.askForSupportAfter = now + 30 * DAY

        val name = s.name?.ifBlank { null } ?: runCatching { PetCatalog.load().pet(s.pet).name }.getOrDefault("your pet")
        val never = { s.askForSupportAfter = Long.MAX_VALUE }
        NotificationGroupManager.getInstance().getNotificationGroup("Petabytes")
            .createNotification(
                "Enjoying $name?",
                "Petabytes is free and made by one person: a rating helps others find it, and a coffee keeps new pets coming.",
                NotificationType.INFORMATION,
            )
            .addAction(NotificationAction.createSimpleExpiring("Rate Petabytes") {
                BrowserUtil.browse("https://plugins.jetbrains.com/plugin/35446-petabytes/reviews"); never()
            })
            .addAction(NotificationAction.createSimpleExpiring("Buy me a coffee") {
                BrowserUtil.browse("https://buymeacoffee.com/chelayel"); never()
            })
            .addAction(NotificationAction.createSimpleExpiring("Don't ask again") { never() })
            .notify(project)
    }
}
