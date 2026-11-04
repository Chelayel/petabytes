import AppKit
import WebKit

/** Short-lived, click-through splashes and tantrums, painted by the shared web renderer. */
final class PetEffectWindow: NSPanel, WKNavigationDelegate {
    private static var active: PetEffectWindow?
    private let webView = WKWebView()
    private let petID: String
    private let kind: String
    private var message: [String: Any]
    private var ready = false
    private var closeWork: DispatchWorkItem?

    static func show(pet: String, on screen: NSScreen? = NSScreen.main) {
        present(pet: pet, kind: "splatter", on: screen, zoom: 1, message: ["type": "splatter", "pet": pet])
    }

    static func tantrum(pet: String, name: String = "", durationMs: Double, fullness: Double,
                        on screen: NSScreen? = NSScreen.main, zoom: CGFloat = 1.3, origin: CGPoint? = nil) {
        var message: [String: Any] = ["type": "tantrum", "pet": pet, "name": name,
                                      "durationMs": min(6000, max(1, durationMs)), "fullness": fullness]
        if let origin { message["x"] = origin.x; message["y"] = origin.y }
        if let window = active, window.kind == "tantrum", window.petID == pet {
            window.message = message
            if window.ready { window.play() }
            return
        }
        present(pet: pet, kind: "tantrum", on: screen, zoom: zoom, message: message)
    }

    private static func present(pet: String, kind: String, on screen: NSScreen?, zoom: CGFloat, message: [String: Any]) {
        dismiss()
        guard let screen else { return }
        let window = PetEffectWindow(pet: pet, kind: kind, screen: screen, zoom: zoom, message: message)
        active = window
        window.load()
        // Also close if WebKit fails to finish loading.
        window.closeAfter(7)
    }

    static func dismissTantrum() {
        if active?.kind == "tantrum" { dismiss() }
    }

    static func dismiss() {
        active?.closeWork?.cancel()
        active?.close()
        active = nil
    }

    private init(pet: String, kind: String, screen: NSScreen, zoom: CGFloat, message: [String: Any]) {
        petID = pet
        self.kind = kind
        self.message = message
        super.init(contentRect: screen.frame, styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        isOpaque = false; backgroundColor = .clear; hasShadow = false
        isReleasedWhenClosed = false
        ignoresMouseEvents = true
        level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.dockWindow)) + 2)
        collectionBehavior = [.moveToActiveSpace, .stationary, .ignoresCycle]
        hidesOnDeactivate = false
        webView.setValue(false, forKey: "drawsBackground")
        webView.pageZoom = zoom
        webView.navigationDelegate = self
        contentView = webView
    }

    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }

    private func load() {
        guard let url = Bundle.main.url(forResource: "pet", withExtension: "html"),
              let page = try? String(contentsOf: url, encoding: .utf8) else { Self.dismiss(); return }
        let html = page.replacingOccurrences(of: "{{csp}}", with: "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
            .replacingOccurrences(of: "{{nonce}}", with: "petabytes")
            .replacingOccurrences(of: "{{pets}}", with: Catalog.json.replacingOccurrences(of: "<", with: "\\u003c"))
        webView.loadHTMLString(html, baseURL: nil)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        ready = true
        play()
    }

    private func play() {
        guard Self.active === self,
              let data = try? JSONSerialization.data(withJSONObject: message),
              let json = String(data: data, encoding: .utf8) else { return }
        webView.evaluateJavaScript("window.petabytes.receive(\(json))") { [weak self] _, _ in
            guard let self, Self.active === self else { return }
            self.orderFrontRegardless()
            let duration = self.kind == "tantrum" ? self.message["durationMs"] as? Double ?? 6000
                : (PetArt.careRules["burstMs"] as? Double ?? 4600) - (PetArt.careRules["windupMs"] as? Double ?? 350)
            self.closeAfter(duration / 1000)
        }
    }

    private func closeAfter(_ seconds: Double) {
        closeWork?.cancel()
        let work = DispatchWorkItem { [weak self] in
            guard let self, Self.active === self else { return }
            Self.dismiss()
        }
        closeWork = work
        DispatchQueue.main.asyncAfter(deadline: .now() + seconds, execute: work)
    }
}
