import AppKit

/**
 After a week with the pet, asks once whether the person would star Petabytes on GitHub or buy its maker a coffee.
 Not Now asks again in a month; either link, or Don't Ask Again, and it never asks again.
 */
enum SupportReminder {
    private static let firstAsk: TimeInterval = 7 * 24 * 60 * 60
    private static let again: TimeInterval = 30 * 24 * 60 * 60

    static let coffee = URL(string: "https://buymeacoffee.com/chelayel")!
    static let github = URL(string: "https://github.com/Chelayel/petabytes")!

    static func askIfDue(petName: String) {
        let due = Settings.askForSupportAfter ?? Settings.firstRun.addingTimeInterval(firstAsk)
        guard Date() >= due else { return }
        // Not over something full screen: that's someone busy.
        guard !FullScreen.appInFront() else { return }

        let alert = NSAlert()
        alert.messageText = "Enjoying \(petName)?"
        alert.informativeText = "Petabytes is free and made by one person. If your pet makes your day a little better, a star on GitHub helps others find it, and a coffee keeps new pets coming."
        alert.addButton(withTitle: "Buy Me a Coffee")
        alert.addButton(withTitle: "Star on GitHub")
        alert.addButton(withTitle: "Not Now")
        alert.showsSuppressionButton = true
        alert.suppressionButton?.title = "Don't ask again"
        let answer = alert.runInFront()
        switch answer {
        case .alertFirstButtonReturn: NSWorkspace.shared.open(coffee)
        case .alertSecondButtonReturn: NSWorkspace.shared.open(github)
        default: break
        }
        let never = answer != .alertThirdButtonReturn || alert.suppressionButton?.state == .on
        Settings.askForSupportAfter = never ? .distantFuture : Date().addingTimeInterval(again)
    }
}
