import AppKit

/**
 How wide the Dock is. macOS doesn't say without the Accessibility permission, so this counts its tiles from its
 own preferences (pinned apps and folders, Finder, Trash, apps running that aren't pinned) and multiplies by
 the tile size. Minimized windows and magnification aren't counted, so it can come out a little narrow.
 */
enum Dock {
    static func estimatedWidth() -> CGFloat {
        let prefs = UserDefaults(suiteName: "com.apple.dock")
        let pinned = prefs?.array(forKey: "persistent-apps") as? [[String: Any]] ?? []
        let folders = (prefs?.array(forKey: "persistent-others") ?? []).count
        let tile = CGFloat(prefs?.double(forKey: "tilesize") ?? 0).nonZero ?? 48

        let pinnedIds = Set(pinned.compactMap { (($0["tile-data"] as? [String: Any])?["bundle-identifier"] as? String) })
        let unpinned = NSWorkspace.shared.runningApplications.filter {
            $0.activationPolicy == .regular && $0.bundleIdentifier != "com.apple.finder" && !pinnedIds.contains($0.bundleIdentifier ?? "")
        }.count
        let recents = prefs?.object(forKey: "show-recents") as? Bool ?? true ? (prefs?.array(forKey: "recent-apps") ?? []).count : 0

        let tiles = CGFloat(1 + pinned.count + unpinned + recents + folders + 1) // Finder ... Trash
        let dividers: CGFloat = (unpinned + recents > 0 ? 1 : 0) + 1
        return tiles * tile * 1.05 + dividers * 12 + 16
    }
}

private extension CGFloat {
    var nonZero: CGFloat? { self == 0 ? nil : self }
}
