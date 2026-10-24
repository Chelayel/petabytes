import AppKit
import WebKit

/**
 A see-through panel above every window and Space with web/pet.html inside, the same page VS Code shows.
 It only takes clicks on the pet itself: everywhere else, clicks fall through to whatever is underneath.
 Drag the pet to float it anywhere; right-click it for its menu.
 */
final class PetWindow: NSPanel {
    /** The page's height in CSS pixels: room for the pet to drift up and down and speak above itself. */
    private static let seaHeight: CGFloat = 150
    private static let floatWidth: CGFloat = 300

    private let webView: WKWebView
    private let bridge = Bridge()
    private var ready = false
    private var queued: [String] = []
    /** The pet's box on the page, in CSS pixels from the top left, as the page last reported it. */
    private var petRect = CGRect.zero
    private var dragStart: CGPoint?
    private var frameStart = CGPoint.zero
    private var dragging = false
    /** Frames a second: plenty for a pet, and a fraction of the display's 60 or 120. Almost none while nobody can see it. */
    private var fps = 20

    var menuProvider: () -> NSMenu = { NSMenu() }

    /** Drawn but not seen, and never in the way: for the pet living in its Dock tile. */
    var invisible = false {
        didSet { updateAlpha() }
    }

    /** True while an app is full screen and the pet should step aside. */
    private var fullScreenApp = false {
        didSet { if fullScreenApp != oldValue { updateAlpha() } }
    }

    /** Hidden by transparency rather than ordered out: WebKit stops drawing a hidden window, and the Dock tile needs it. */
    private func updateAlpha() {
        alphaValue = invisible || fullScreenApp ? 0 : 1
        ignoresMouseEvents = true
    }

    /** Whether the app in front has a window covering a whole screen: full screen, or a game or video player. */
    func checkFullScreen() {
        guard Settings.hideInFullScreen, let front = NSWorkspace.shared.frontmostApplication,
              front.processIdentifier != ProcessInfo.processInfo.processIdentifier else {
            fullScreenApp = false
            return
        }
        let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
        let sizes = NSScreen.screens.map(\.frame.size)
        fullScreenApp = windows.contains { window in
            guard window[kCGWindowOwnerPID as String] as? pid_t == front.processIdentifier,
                  window[kCGWindowLayer as String] as? Int == 0,
                  let raw = window[kCGWindowBounds as String] as? NSDictionary,
                  let bounds = CGRect(dictionaryRepresentation: raw) else { return false }
            return sizes.contains(bounds.size)
        }
    }

    init() {
        let config = WKWebViewConfiguration()
        // Keep the page running while the window is hidden, for the pet living in its Dock tile.
        if #available(macOS 14, *) { config.preferences.inactiveSchedulingPolicy = .none }
        config.userContentController.add(bridge, name: "host")
        config.userContentController.addUserScript(WKUserScript(source: Self.hostScript, injectionTime: .atDocumentEnd, forMainFrameOnly: true))
        webView = WKWebView(frame: .zero, configuration: config)
        webView.setValue(false, forKey: "drawsBackground")
        super.init(contentRect: .zero, styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)

        isOpaque = false
        backgroundColor = .clear
        hasShadow = false
        level = .floating
        // Every Space, but not over full-screen apps.
        collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]
        hidesOnDeactivate = false
        isMovable = false
        ignoresMouseEvents = true
        contentView = webView
        bridge.window = self

        NSEvent.addLocalMonitorForEvents(matching: [.leftMouseDown, .leftMouseDragged, .leftMouseUp, .rightMouseDown]) { [weak self] event in
            guard let self, event.window === self else { return event }
            return self.handle(event)
        }
        Timer.scheduledTimer(withTimeInterval: 1.0 / 15, repeats: true) { [weak self] _ in self?.updateClickThrough() }
        let workspace = NSWorkspace.shared.notificationCenter, distributed = DistributedNotificationCenter.default()
        for (center, name, rate) in [
            (workspace, NSWorkspace.screensDidSleepNotification, 1), (workspace, NSWorkspace.screensDidWakeNotification, 20),
            (distributed, Notification.Name("com.apple.screenIsLocked"), 1), (distributed, Notification.Name("com.apple.screenIsUnlocked"), 20),
        ] as [(NotificationCenter, Notification.Name, Int)] {
            center.addObserver(forName: name, object: nil, queue: .main) { [weak self] _ in
                self?.fps = rate
                self?.configure()
            }
        }
        NotificationCenter.default.addObserver(forName: NSApplication.didChangeScreenParametersNotification, object: nil, queue: .main) { [weak self] _ in self?.place() }
        // The Dock can grow, shrink or move without the screen changing; check now and then.
        Timer.scheduledTimer(withTimeInterval: 3, repeats: true) { [weak self] _ in
            guard let self, Settings.place == .dock, self.frame != self.dockFrame() else { return }
            self.place()
        }
        let check: (Notification) -> Void = { [weak self] _ in self?.checkFullScreen() }
        workspace.addObserver(forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main, using: check)
        workspace.addObserver(forName: NSWorkspace.activeSpaceDidChangeNotification, object: nil, queue: .main, using: check)
        // An app can also go full screen without switching apps or Spaces being announced in time.
        Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in self?.checkFullScreen() }
        load()
        place()
    }

    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }

    // ---- The page ----------------------------------------------------------

    /**
     Runs inside the page: hides the panel's name label, drops the glow (a filter redrawn every frame is the
     most expensive thing on the page) and reports where the pet is, for click-through.
     */
    private static let hostScript = """
    (() => {
      const style = document.createElement("style");
      style.textContent = ".name { display: none; } #pet svg { filter: none; }";
      document.head.appendChild(style);
      const host = window.webkit.messageHandlers.host, pet = document.getElementById("pet");
      setInterval(() => {
        const r = pet.getBoundingClientRect();
        host.postMessage({ type: "rect", x: r.left, y: r.top, w: r.width, h: r.height });
      }, 100);
      host.postMessage({ type: "ready" });
    })();
    """

    private func load() {
        guard let url = Bundle.main.url(forResource: "pet", withExtension: "html"),
              let page = try? String(contentsOf: url, encoding: .utf8) else { fatalError("pet.html is missing from the app bundle") }
        let html = page
            .replacingOccurrences(of: "{{csp}}", with: "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
            .replacingOccurrences(of: "{{nonce}}", with: "petabytes")
            .replacingOccurrences(of: "{{pets}}", with: Catalog.json.replacingOccurrences(of: "<", with: "\\u003c"))
        webView.loadHTMLString(html, baseURL: nil)
    }

    /** Hands the page a message, as pet.html's receive() expects: config, react, feed, typing and so on. */
    func send(_ message: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: message), let json = String(data: data, encoding: .utf8) else { return }
        let script = "window.petabytes.receive(\(json))"
        if ready { webView.evaluateJavaScript(script) } else { queued.append(script) }
    }

    /** A picture of the pet as it is right now, for the Dock icon. */
    func snapshotPet(attempts: Int = 20, _ done: @escaping (NSImage?) -> Void) {
        guard ready, !petRect.isEmpty else {
            // The page is still loading; try again shortly.
            guard attempts > 0 else { return done(nil) }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) { [weak self] in self?.snapshotPet(attempts: attempts - 1, done) }
            return
        }
        let config = WKSnapshotConfiguration()
        config.rect = CGRect(x: petRect.minX * zoom, y: petRect.minY * zoom, width: petRect.width * zoom, height: petRect.height * zoom)
        webView.takeSnapshot(with: config) { image, _ in done(image) }
    }

    func configure() {
        send(["type": "config", "pet": Settings.pet, "name": Settings.name, "ground": Settings.place == .dock || Settings.showInDock, "fps": fps])
    }

    fileprivate func received(_ body: Any) {
        guard let message = body as? [String: Any], let type = message["type"] as? String else { return }
        switch type {
        case "ready":
            ready = true
            configure()
            queued.forEach { webView.evaluateJavaScript($0) }
            queued.removeAll()
        case "rect":
            func number(_ key: String) -> CGFloat { CGFloat((message[key] as? NSNumber)?.doubleValue ?? 0) }
            petRect = CGRect(x: number("x"), y: number("y"), width: number("w"), height: number("h"))
        default:
            break
        }
    }

    // ---- Where it lives ----------------------------------------------------

    /** The size the pet is drawn at: 1 is the VS Code size. */
    var zoom: CGFloat {
        get { webView.pageZoom }
        set { webView.pageZoom = newValue; place() }
    }

    func place() {
        setFrame(Settings.place == .dock ? dockFrame() : floatFrame(), display: true)
        configure()
    }

    /**
     A strip as wide as the Dock whose bottom edge is the top of the Dock: pet.html stands a pet on the ground
     on the strip's bottom edge. With the Dock at a side or hidden, the pet walks along the bottom of the screen.
     */
    private func dockFrame() -> NSRect {
        let screen = Self.dockScreen()
        let visible = screen.visibleFrame, full = screen.frame
        let height = Self.seaHeight * zoom
        guard visible.minY > full.minY else {
            return NSRect(x: visible.minX, y: full.minY, width: visible.width, height: height)
        }
        let width = min(visible.width, max(Self.floatWidth * zoom, Dock.estimatedWidth()))
        // The Dock's top edge sits a few points below where the usable area starts.
        return NSRect(x: full.midX - width / 2, y: visible.minY - 4, width: width, height: height)
    }

    private func floatFrame() -> NSRect {
        let size = NSSize(width: Self.floatWidth * zoom, height: Self.seaHeight * zoom)
        let origin = Settings.floatOrigin.flatMap { saved in
            NSScreen.screens.contains { $0.frame.contains(CGPoint(x: saved.x + size.width / 2, y: saved.y + size.height / 2)) } ? saved : nil
        }
        if let origin { return NSRect(origin: origin, size: size) }
        let visible = (NSScreen.main ?? Self.dockScreen()).visibleFrame
        return NSRect(x: visible.maxX - size.width - 24, y: visible.minY + 24, width: size.width, height: size.height)
    }

    /** The screen the Dock is on: the one whose usable area is cut off at the bottom or a side. */
    private static func dockScreen() -> NSScreen {
        NSScreen.screens.first { s in
            s.visibleFrame.minY > s.frame.minY || s.visibleFrame.minX > s.frame.minX || s.visibleFrame.maxX < s.frame.maxX
        } ?? NSScreen.screens[0]
    }

    // ---- Mouse -------------------------------------------------------------

    /** Lets clicks through everywhere except on the pet. */
    private func updateClickThrough() {
        let mouse = NSEvent.mouseLocation
        guard isVisible, alphaValue > 0, !dragging, frame.insetBy(dx: -10, dy: -10).contains(mouse) || !ignoresMouseEvents else { return }
        let onPage = CGPoint(x: (mouse.x - frame.minX) / zoom, y: (frame.maxY - mouse.y) / zoom)
        let overPet = petRect.insetBy(dx: -6, dy: -6).contains(onPage)
        if ignoresMouseEvents == overPet { ignoresMouseEvents = !overPet }
    }

    private func handle(_ event: NSEvent) -> NSEvent? {
        switch event.type {
        case .rightMouseDown:
            NSMenu.popUpContextMenu(menuProvider(), with: event, for: webView)
            return nil
        case .leftMouseDown:
            dragStart = NSEvent.mouseLocation
            frameStart = frame.origin
            dragging = false
            return event
        case .leftMouseDragged:
            guard let start = dragStart else { return event }
            let mouse = NSEvent.mouseLocation
            if !dragging {
                guard hypot(mouse.x - start.x, mouse.y - start.y) > 4 else { return nil }
                dragging = true
                if Settings.place == .dock { leaveDock() }
            }
            setFrameOrigin(CGPoint(x: frameStart.x + mouse.x - start.x, y: frameStart.y + mouse.y - start.y))
            return nil
        case .leftMouseUp:
            if dragging {
                dragging = false
                Settings.floatOrigin = frame.origin
            }
            dragStart = nil
            return event
        default:
            return event
        }
    }

    /** Dragged off the Dock: shrink to a small sea around the pet, so it stays under the cursor. */
    private func leaveDock() {
        Settings.place = .float
        let width = Self.floatWidth * zoom
        // pet.html keeps the pet inside the sea, so in a narrower one it may sit further left than it does now.
        let petX = petRect.minX * zoom
        let petXAfter = min(petX, width - (petRect.width + 4) * zoom)
        let next = NSRect(x: frame.minX + petX - petXAfter, y: frame.minY, width: width, height: frame.height)
        setFrame(next, display: true)
        frameStart = next.origin
        Settings.floatOrigin = next.origin
        configure()
    }
}

/** Receives the page's messages; separate so the web view doesn't hold on to the window. */
private final class Bridge: NSObject, WKScriptMessageHandler {
    weak var window: PetWindow?

    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        window?.received(message.body)
    }
}
