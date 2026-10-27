import AppKit
import Security

extension NSAlert {
    /**
     Shows the alert where it will be seen. An app that isn't in front can't bring itself forward on recent macOS,
     so an alert it puts up unasked would wait behind other windows: this one floats above them, on the current Space.
     */
    @discardableResult
    func runInFront() -> NSApplication.ModalResponse {
        window.level = .floating
        window.collectionBehavior.insert(.moveToActiveSpace)
        NSApp.activate(ignoringOtherApps: true)
        return runModal()
    }
}

/**
 Keeps the app up to date from its GitHub releases. Once a day (and from Check for Updates…) it asks GitHub for the
 latest release; when that's newer, it offers to install it: it downloads the release's DMG, checks the app inside
 is signed by the same certificate as this one (the running app's own designated requirement, so nothing else gets
 in), puts it in place of this one and relaunches. When it can't (a build signed ad hoc, or an app somewhere it
 can't write), it opens the DMG instead, to drag across by hand.
 */
final class Updater {
    struct Release {
        let version: String
        let dmg: URL
        let page: URL
    }

    private static let latest = URL(string: "https://api.github.com/repos/Chelayel/petabytes/releases/latest")!
    private static let day: TimeInterval = 24 * 60 * 60

    static var current: String { Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0" }

    /** A newer release found but not installed, for the menu to offer. */
    private(set) var available: Release?
    private var busy = false

    /** The daily check: quiet unless there's something new, and only asks once per version. */
    func checkIfDue() {
        guard Date().timeIntervalSince(Settings.lastUpdateCheck) > Self.day else { return }
        check(quietly: true)
    }

    func check(quietly: Bool) {
        guard !busy else { return }
        busy = true
        Settings.lastUpdateCheck = Date()
        Task { @MainActor in
            defer { busy = false }
            let release: Release?
            do { release = try await Self.fetchLatest() } catch {
                // Offline, or GitHub busy: the daily check tries again within the hour.
                Settings.lastUpdateCheck = .distantPast
                if !quietly { Self.tell("Couldn't check for updates", "GitHub didn't answer: \(error.localizedDescription)") }
                return
            }
            guard let release, Self.isNewer(release.version, than: Self.current) else {
                available = nil
                if !quietly { Self.tell("Petabytes is up to date", "You have the latest version, \(Self.current).") }
                return
            }
            available = release
            if quietly && Settings.offeredUpdate == release.version { return }
            Settings.offeredUpdate = release.version
            offer(release)
        }
    }

    /** Asks before installing; Later keeps the offer in the menu. */
    func offer(_ release: Release) {
        let alert = NSAlert()
        alert.messageText = "Petabytes \(release.version) is available"
        alert.informativeText = "You have \(Self.current). Install it now? Petabytes will restart, and your pet comes right back."
        alert.addButton(withTitle: "Install and Relaunch")
        alert.addButton(withTitle: "Later")
        alert.addButton(withTitle: "What's New")
        switch alert.runInFront() {
        case .alertFirstButtonReturn: install(release)
        case .alertThirdButtonReturn: NSWorkspace.shared.open(release.page)
        default: break
        }
    }

    // ---- Finding it --------------------------------------------------------

    private static func fetchLatest() async throws -> Release? {
        var request = URLRequest(url: latest, timeoutInterval: 20)
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        request.setValue("Petabytes/\(current)", forHTTPHeaderField: "User-Agent")
        let (data, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 200,
              let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let tag = json["tag_name"] as? String,
              let page = (json["html_url"] as? String).flatMap(URL.init(string:)),
              let assets = json["assets"] as? [[String: Any]],
              let dmg = assets.lazy.compactMap({ $0["browser_download_url"] as? String }).first(where: { $0.hasSuffix(".dmg") }),
              let dmgURL = URL(string: dmg) else { return nil }
        return Release(version: tag.hasPrefix("v") ? String(tag.dropFirst()) : tag, dmg: dmgURL, page: page)
    }

    /** 1.10.0 is newer than 1.9.2: compared number by number. */
    static func isNewer(_ version: String, than other: String) -> Bool {
        let a = version.split(separator: ".").map { Int($0) ?? 0 }, b = other.split(separator: ".").map { Int($0) ?? 0 }
        for i in 0..<max(a.count, b.count) where (i < a.count ? a[i] : 0) != (i < b.count ? b[i] : 0) {
            return (i < a.count ? a[i] : 0) > (i < b.count ? b[i] : 0)
        }
        return false
    }

    // ---- Installing it -----------------------------------------------------

    private func install(_ release: Release) {
        busy = true
        Task { @MainActor in
            defer { busy = false }
            let work = FileManager.default.temporaryDirectory.appendingPathComponent("Petabytes-update-\(UUID().uuidString)")
            do {
                try FileManager.default.createDirectory(at: work, withIntermediateDirectories: true)
                let (download, _) = try await URLSession.shared.download(from: release.dmg)
                let dmg = work.appendingPathComponent("Petabytes.dmg")
                try FileManager.default.moveItem(at: download, to: dmg)
                let staged = try await Task.detached { try Self.unpack(dmg, into: work) }.value
                guard Self.sameSigner(staged), Self.canReplaceSelf else {
                    // Not one we can vouch for, or nowhere we may write: hand it over to drag across by hand.
                    NSWorkspace.shared.open(dmg)
                    return
                }
                try Self.relaunch(into: staged)
            } catch {
                Self.tell("Couldn't install the update", "\(error.localizedDescription)\n\nYou can download it from GitHub instead.")
                NSWorkspace.shared.open(release.page)
            }
        }
    }

    /** Mounts the DMG out of sight, copies the app out, and ejects it. */
    private static func unpack(_ dmg: URL, into work: URL) throws -> URL {
        let mount = work.appendingPathComponent("mount")
        try run("/usr/bin/hdiutil", ["attach", dmg.path, "-nobrowse", "-readonly", "-noautoopen", "-mountpoint", mount.path])
        defer { _ = try? run("/usr/bin/hdiutil", ["detach", mount.path, "-force"]) }
        let staged = work.appendingPathComponent("Petabytes.app")
        try run("/usr/bin/ditto", [mount.appendingPathComponent("Petabytes.app").path, staged.path])
        return staged
    }

    /** Whether the new app meets this one's designated requirement: signed by the same certificate. */
    private static func sameSigner(_ app: URL) -> Bool {
        var running: SecCode?, me: SecStaticCode?, requirement: SecRequirement?, other: SecStaticCode?
        guard SecCodeCopySelf([], &running) == errSecSuccess, let running,
              SecCodeCopyStaticCode(running, [], &me) == errSecSuccess, let me,
              SecCodeCopyDesignatedRequirement(me, [], &requirement) == errSecSuccess, let requirement,
              SecStaticCodeCreateWithPath(app as CFURL, [], &other) == errSecSuccess, let other else { return false }
        // An ad hoc build's requirement names its own exact code, which no other build meets: it falls back too.
        let flags = SecCSFlags(rawValue: kSecCSCheckAllArchitectures | kSecCSStrictValidate | kSecCSCheckNestedCode)
        return SecStaticCodeCheckValidity(other, flags, requirement) == errSecSuccess
    }

    private static var canReplaceSelf: Bool {
        let parent = Bundle.main.bundleURL.deletingLastPathComponent().path
        // An app run straight from the DMG or from Downloads under App Translocation sits somewhere read-only.
        return FileManager.default.isWritableFile(atPath: parent) && !parent.contains("/AppTranslocation/") && !parent.hasPrefix("/Volumes/")
    }

    /** Quits, and leaves a small script to swap the apps once this one is gone and open the new one. */
    private static func relaunch(into staged: URL) throws {
        let target = Bundle.main.bundleURL.path
        let script = """
        while kill -0 \(ProcessInfo.processInfo.processIdentifier) 2>/dev/null; do sleep 0.2; done
        rm -rf "$2.old"
        if mv "$2" "$2.old"; then
          if /usr/bin/ditto "$1" "$2"; then rm -rf "$2.old"; else rm -rf "$2"; mv "$2.old" "$2"; fi
        fi
        /usr/bin/xattr -dr com.apple.quarantine "$2" 2>/dev/null
        /usr/bin/open "$2"
        rm -rf "$(dirname "$1")"
        """
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/sh")
        process.arguments = ["-c", script, "petabytes-update", staged.path, target]
        try process.run()
        NSApp.terminate(nil)
    }

    @discardableResult
    private static func run(_ tool: String, _ arguments: [String]) throws -> Int32 {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: tool)
        process.arguments = arguments
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        try process.run()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else {
            throw NSError(domain: "Petabytes", code: Int(process.terminationStatus),
                          userInfo: [NSLocalizedDescriptionKey: "\(URL(fileURLWithPath: tool).lastPathComponent) failed (\(process.terminationStatus))."])
        }
        return process.terminationStatus
    }

    private static func tell(_ title: String, _ text: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = text
        alert.runInFront()
    }
}
