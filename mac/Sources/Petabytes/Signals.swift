import AppKit
import IOKit.ps
import Network

/**
 What the Mac tells the pet, as the messages pet.html understands. Nothing here needs a permission:
 it reads how long ago a key was pressed (never which key), which kind of app is in front, the battery, the network,
 finished downloads, new screenshots, the clipboard's change count (never its contents), heat, appearance
 and the lock screen.
 */
final class Signals {
    private let send: ([String: Any]) -> Void
    private var typingSeconds = 0
    private var wasOnAC: Bool?
    private var wasLow = false
    private var online: Bool?
    private var clipboardCount = NSPasteboard.general.changeCount
    private let network = NWPathMonitor()
    private let screenshots = NSMetadataQuery()
    private var powerSource: CFRunLoopSource?

    init(send: @escaping ([String: Any]) -> Void) {
        self.send = send
    }

    private func react(_ key: String, _ vars: [String: String] = [:]) {
        send(["type": "react", "key": key, "vars": vars])
    }

    func start() {
        Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in self?.tick() }
        Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in self?.timeOfDay() }
        watchApps()
        watchPower()
        watchNetwork()
        watchScreenshots()

        let distributed = DistributedNotificationCenter.default()
        distributed.addObserver(forName: Notification.Name("com.apple.DownloadFileFinished"), object: nil, queue: .main) { [weak self] _ in self?.react("download") }
        distributed.addObserver(forName: Notification.Name("AppleInterfaceThemeChangedNotification"), object: nil, queue: .main) { [weak self] _ in self?.react("darkMode") }
        distributed.addObserver(forName: Notification.Name("com.apple.screenIsUnlocked"), object: nil, queue: .main) { [weak self] _ in self?.react("unlock") }
        NotificationCenter.default.addObserver(forName: ProcessInfo.thermalStateDidChangeNotification, object: nil, queue: .main) { [weak self] _ in
            let state = ProcessInfo.processInfo.thermalState
            if state == .serious || state == .critical { self?.react("hot") }
        }
        NSWorkspace.shared.notificationCenter.addObserver(forName: NSWorkspace.didWakeNotification, object: nil, queue: .main) { [weak self] _ in
            self?.send(["type": "active"])
        }
    }

    /** Once a second: are you here, are you typing, did you copy something. */
    private func tick() {
        let anyEvent = CGEventType(rawValue: ~0)!
        let idle = CGEventSource.secondsSinceLastEventType(.combinedSessionState, eventType: anyEvent)
        let sinceKey = CGEventSource.secondsSinceLastEventType(.combinedSessionState, eventType: .keyDown)
        // pet.html naps after a few quiet minutes; anything you do keeps it (or wakes it) up.
        if idle < 1.5 { send(["type": "active"]) }
        // Two seconds of keys in a row is typing; one stray shortcut isn't.
        typingSeconds = sinceKey < 1 ? typingSeconds + 1 : 0
        if typingSeconds >= 2 { send(["type": "typing"]) }

        let count = NSPasteboard.general.changeCount
        if count != clipboardCount {
            clipboardCount = count
            react("copy")
        }
    }

    private func timeOfDay() {
        let idle = CGEventSource.secondsSinceLastEventType(.combinedSessionState, eventType: CGEventType(rawValue: ~0)!)
        guard idle < 60 else { return }
        let hour = Calendar.current.component(.hour, from: Date())
        if hour >= 23 || hour < 5 { react("lateNight") } else if hour < 10 { react("morning") }
    }

    // ---- Apps --------------------------------------------------------------

    /** Apps by bundle identifier, and the reaction (in pets.json) to bringing one to the front. */
    private static let apps: [String: String] = {
        let groups: [String: [String]] = [
            "terminal": ["com.apple.Terminal", "com.googlecode.iterm2", "dev.warp.Warp-Stable", "com.mitchellh.ghostty",
                         "net.kovidgoyal.kitty", "org.alacritty", "com.github.wez.wezterm", "co.zeit.hyper"],
            "ai": ["com.anthropic.claudefordesktop", "com.openai.chat", "com.openai.codex", "com.openai.atlas",
                   "ai.perplexity.mac", "com.todesktop.230313mzl4w4u92"],
            "ide": ["com.microsoft.VSCode", "com.microsoft.VSCodeInsiders", "com.apple.dt.Xcode", "com.google.android.studio",
                    "dev.zed.Zed", "com.sublimetext.4", "com.exafunction.windsurf", "com.panic.Nova", "com.barebones.bbedit"],
            "meeting": ["us.zoom.xos", "com.microsoft.teams2", "com.microsoft.teams", "com.apple.FaceTime", "com.cisco.webexmeetingsapp"],
            "music": ["com.spotify.client", "com.apple.Music", "com.apple.podcasts", "com.tidal.desktop"],
            "browser": ["com.apple.Safari", "com.google.Chrome", "company.thebrowser.Browser", "org.mozilla.firefox",
                        "com.brave.Browser", "com.microsoft.edgemac", "app.zen-browser.zen", "com.operasoftware.Opera"],
            "chat": ["com.tinyspeck.slackmacgap", "com.hnc.Discord", "com.apple.MobileSMS", "net.whatsapp.WhatsApp",
                     "ru.keepcoder.Telegram", "org.whispersystems.signal-desktop"],
            "mail": ["com.apple.mail", "com.microsoft.Outlook", "com.readdle.smartemail-Mac", "com.superhuman.electron"],
            "design": ["com.figma.Desktop", "com.bohemiancoding.sketch3", "com.seriflabs.affinitydesigner2", "com.seriflabs.affinityphoto2",
                       "com.adobe.Photoshop", "com.adobe.illustrator", "com.pixelmatorteam.pixelmator.x", "com.canva.CanvaDesktop"],
            "notes": ["notion.id", "md.obsidian", "com.apple.Notes", "net.shinyfrog.bear", "com.apple.iWork.Pages", "com.microsoft.Word"],
            "calendar": ["com.apple.iCal", "com.flexibits.fantastical2.mac", "com.cron.electron"],
            "game": ["com.valvesoftware.steam", "com.mojang.minecraftlauncher", "net.battle.app", "com.epicgames.EpicGamesLauncher"],
            "video": ["com.apple.TV", "com.colliderli.iina", "org.videolan.vlc", "com.apple.QuickTimePlayerX"],
            "activity": ["com.apple.ActivityMonitor"],
            "docker": ["com.docker.docker", "com.electron.dockerdesktop", "dev.orbstack.OrbStack"],
            "database": ["com.tinyapp.TablePlus", "org.jkiss.dbeaver.core.product", "com.sequel-ace.sequel-ace", "com.jetbrains.datagrip"],
            "api": ["com.postmanlabs.mac", "com.insomnia.app", "com.usebruno.app"],
            "simulator": ["com.apple.iphonesimulator"],
            "settings": ["com.apple.systempreferences"],
            "appStore": ["com.apple.AppStore"],
            "passwords": ["com.apple.Passwords", "com.1password.1password", "com.bitwarden.desktop"],
        ]
        return Dictionary(groups.flatMap { key, ids in ids.map { ($0, key) } }, uniquingKeysWith: { first, _ in first })
    }()

    private func watchApps() {
        NSWorkspace.shared.notificationCenter.addObserver(forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main) { [weak self] note in
            guard let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication, let id = app.bundleIdentifier else { return }
            if let key = Self.apps[id] ?? (id.hasPrefix("com.jetbrains.") ? "ide" : nil) { self?.react(key) }
        }
    }

    // ---- Battery -----------------------------------------------------------

    private func watchPower() {
        let context = Unmanaged.passUnretained(self).toOpaque()
        guard let source = IOPSNotificationCreateRunLoopSource({ context in
            guard let context else { return }
            Unmanaged<Signals>.fromOpaque(context).takeUnretainedValue().powerChanged()
        }, context)?.takeRetainedValue() else { return }
        powerSource = source
        CFRunLoopAddSource(CFRunLoopGetMain(), source, .defaultMode)
        powerChanged()
    }

    private func powerChanged() {
        guard let info = IOPSCopyPowerSourcesInfo()?.takeRetainedValue(),
              let list = IOPSCopyPowerSourcesList(info)?.takeRetainedValue() as? [CFTypeRef],
              let battery = list.lazy.compactMap({ IOPSGetPowerSourceDescription(info, $0)?.takeUnretainedValue() as? [String: Any] })
                .first(where: { $0[kIOPSTypeKey] as? String == kIOPSInternalBatteryType }) else { return } // a desktop Mac
        let onAC = battery[kIOPSPowerSourceStateKey] as? String == kIOPSACPowerValue
        let current = battery[kIOPSCurrentCapacityKey] as? Int ?? 100
        let max = battery[kIOPSMaxCapacityKey] as? Int ?? 100
        let percent = max > 0 ? current * 100 / max : 100

        if wasOnAC == false && onAC { react("charging") }
        let low = !onAC && percent <= 20
        if low && !wasLow { react("batteryLow", ["percent": "\(percent)%"]) }
        wasOnAC = onAC
        wasLow = low
    }

    // ---- Network -----------------------------------------------------------

    private func watchNetwork() {
        network.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                guard let self else { return }
                let up = path.status == .satisfied
                if let online = self.online, online != up { self.react(up ? "online" : "offline") }
                self.online = up
            }
        }
        network.start(queue: .global(qos: .utility))
    }

    // ---- Screenshots -------------------------------------------------------

    /** Spotlight tags screenshots wherever they're saved; only ones taken from now on count. */
    private func watchScreenshots() {
        screenshots.predicate = NSPredicate(format: "kMDItemIsScreenCapture == 1 AND kMDItemContentCreationDate > %@", Date() as NSDate)
        screenshots.searchScopes = [NSMetadataQueryUserHomeScope]
        NotificationCenter.default.addObserver(forName: .NSMetadataQueryDidUpdate, object: screenshots, queue: .main) { [weak self] note in
            let added = note.userInfo?[NSMetadataQueryUpdateAddedItemsKey] as? [Any] ?? []
            if !added.isEmpty { self?.react("screenshot") }
        }
        screenshots.start()
    }
}
