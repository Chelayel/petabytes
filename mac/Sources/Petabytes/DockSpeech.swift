import AppKit
import ApplicationServices
import SwiftUI

/**
 Shows what the pet in the Dock icon says, in a bubble just above the icon (beside it, with the Dock at a side).
 macOS only tells an app where its Dock icon is through the Accessibility permission: the Dock's accessibility
 tree has an item per icon, with its position. Without the permission, or with the Dock hidden, it stays quiet
 and the icon's own one-glyph bubble does the talking.
 */
final class DockSpeech {
    private let panel: NSPanel
    private let host = NSHostingView(rootView: SpeechBubble(text: "", tail: .down))
    private var hideTimer: Timer?

    init() {
        panel = NSPanel(contentRect: .zero, styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: true)
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = false
        panel.ignoresMouseEvents = true
        panel.hidesOnDeactivate = false
        panel.level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.dockWindow)) + 1)
        panel.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]
        panel.contentView = host
    }

    static var allowed: Bool { AXIsProcessTrusted() }

    /** Asks macOS for the Accessibility permission; the system shows its own prompt with a way to System Settings. */
    static func requestAccess() {
        let prompt = kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String
        AXIsProcessTrustedWithOptions([prompt: true] as CFDictionary)
    }

    /** Shows the line above the icon; false when it can't (no permission, switched off, or no icon to point at). */
    @discardableResult
    func say(_ text: String) -> Bool {
        guard Settings.talkInDock, Self.allowed, let tile = Self.tileFrame(),
              let screen = NSScreen.screens.first(where: { $0.frame.intersects(tile) }) else { return false }
        let frame = screen.frame
        // Which edge the Dock is on decides where the bubble goes and which way its tail points.
        let tail: SpeechBubble.Tail = tile.minX - frame.minX < 8 ? .left : frame.maxX - tile.maxX < 8 ? .right : .down
        host.rootView = SpeechBubble(text: text, tail: tail)
        let size = host.fittingSize
        var origin: CGPoint
        switch tail {
        case .down: origin = CGPoint(x: tile.midX - size.width / 2, y: tile.maxY + 2)
        case .left: origin = CGPoint(x: tile.maxX + 2, y: tile.midY - size.height / 2)
        case .right: origin = CGPoint(x: tile.minX - size.width - 2, y: tile.midY - size.height / 2)
        }
        origin.x = min(max(origin.x, frame.minX + 4), frame.maxX - size.width - 4)
        panel.setFrame(NSRect(origin: origin, size: size), display: true)
        panel.alphaValue = 1
        panel.orderFrontRegardless()
        hideTimer?.invalidate()
        hideTimer = Timer.scheduledTimer(withTimeInterval: 3, repeats: false) { [weak self] _ in self?.hide() }
        return true
    }

    func hide() {
        hideTimer?.invalidate()
        NSAnimationContext.runAnimationGroup({ $0.duration = 0.25; panel.animator().alphaValue = 0 }) { [panel] in
            if panel.alphaValue == 0 { panel.orderOut(nil) }
        }
    }

    /** Where this app's Dock icon is, in AppKit screen coordinates, or nil when the Dock won't say. */
    static func tileFrame() -> NSRect? {
        guard let dock = NSRunningApplication.runningApplications(withBundleIdentifier: "com.apple.dock").first else { return nil }
        let name = Bundle.main.object(forInfoDictionaryKey: "CFBundleName") as? String ?? "Petabytes"
        for list in children(of: AXUIElementCreateApplication(dock.processIdentifier)) {
            for item in children(of: list) where attribute(item, kAXTitleAttribute) as? String == name {
                var position = CGPoint.zero, size = CGSize.zero
                guard let p = attribute(item, kAXPositionAttribute), let s = attribute(item, kAXSizeAttribute),
                      AXValueGetValue(p as! AXValue, .cgPoint, &position), AXValueGetValue(s as! AXValue, .cgSize, &size),
                      size.width > 0 else { return nil }
                // Accessibility measures from the top left of the main screen; AppKit from the bottom left.
                let top = NSScreen.screens[0].frame.maxY
                return NSRect(x: position.x, y: top - position.y - size.height, width: size.width, height: size.height)
            }
        }
        return nil
    }

    private static func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
        var value: CFTypeRef?
        return AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success ? value : nil
    }

    private static func children(of element: AXUIElement) -> [AXUIElement] {
        attribute(element, kAXChildrenAttribute) as? [AXUIElement] ?? []
    }
}

/** The bubble: the same dark rounded box as the walking pet's, with a tail toward the Dock icon. */
private struct SpeechBubble: View {
    enum Tail { case down, left, right }

    let text: String
    let tail: Tail

    var body: some View {
        let box = Text(text)
            .font(.system(size: 13, weight: .medium))
            .foregroundStyle(Color(white: 0.92))
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(RoundedRectangle(cornerRadius: 9).fill(Color(red: 0.1, green: 0.11, blue: 0.13)))
            .overlay(RoundedRectangle(cornerRadius: 9).stroke(Color.white.opacity(0.18)))
            .fixedSize()
        Group {
            switch tail {
            case .down: VStack(spacing: -1) { box; Pointer().rotationEffect(.degrees(180)) }
            case .left: HStack(spacing: -1) { Pointer().rotationEffect(.degrees(-90)); box }
            case .right: HStack(spacing: -1) { box; Pointer().rotationEffect(.degrees(90)) }
            }
        }
        .padding(2)
    }
}

private struct Pointer: View {
    var body: some View {
        Path { p in
            p.move(to: CGPoint(x: 0, y: 7)); p.addLine(to: CGPoint(x: 6, y: 0)); p.addLine(to: CGPoint(x: 12, y: 7))
        }
        .fill(Color(red: 0.1, green: 0.11, blue: 0.13))
        .frame(width: 12, height: 7)
    }
}
