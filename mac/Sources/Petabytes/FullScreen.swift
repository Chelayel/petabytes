import AppKit

enum FullScreen {
    /** Whether the app in front has a window covering a whole screen: full screen, or a game or video player. */
    static func appInFront() -> Bool {
        guard let front = NSWorkspace.shared.frontmostApplication,
              front.processIdentifier != ProcessInfo.processInfo.processIdentifier else { return false }
        let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        // A full-screen window spans the screen's width and its height below the notch, if it has one.
        let screens = NSScreen.screens.map { ($0.frame.width, $0.frame.height - $0.safeAreaInsets.top) }
        return windows.contains { window in
            guard window[kCGWindowOwnerPID as String] as? pid_t == front.processIdentifier,
                  window[kCGWindowLayer as String] as? Int == 0,
                  let raw = window[kCGWindowBounds as String] as? NSDictionary,
                  let bounds = CGRect(dictionaryRepresentation: raw) else { return false }
            return screens.contains { width, height in bounds.width >= width && bounds.height >= height - 1 }
        }
    }
}
