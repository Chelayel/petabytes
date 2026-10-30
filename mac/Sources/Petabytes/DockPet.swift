import AppKit

/**
 The pet living inside its Dock icon, drawn natively (15 frames a second while something's happening, 10 when calm,
 4 asleep, and fewer in Low Power Mode): no web page runs meanwhile.
 It takes the same messages as pet.html (react, typing, active, feed) and follows the same rules, cut down
 to what fits in an icon: moods, poses, turning around, naps, and a one-glyph bubble in the icon's corner.
 What it says goes to onSay, which shows it above the icon when it can (DockSpeech).
 */
final class DockPet {
    private static let sleepAfter: TimeInterval = 3 * 60

    private let view = NSImageView()
    private var timer: Timer?
    private var art = PetArt.load(Settings.pet)

    private var until: [String: Date] = [:]
    private var happyAt = Date.distantPast, spinAt = Date.distantPast
    private var lastActivity = Date()
    private var lastReact: [String: Date] = [:]
    private var sleeping = false
    private var facingLeft = false
    private var nextTurn = Date().addingTimeInterval(6)
    /** Seconds of limb motion: faster when excited, stopped while hiding. */
    private var clock = 0.0
    private var lastFrame = Date()
    private var poses: [String: Pose] = [:]
    /** A glyph in a bubble at the icon's corner, until the date. */
    private var bubble: (glyph: String, until: Date)?
    private var lastTypingLine = Date.distantPast
    /** When the pet next does something on its own (pets.json's antics). */
    private var nextAntic = Date().addingTimeInterval(.random(in: PetArt.anticEvery))
    private var interval = 0.0
    /** A line the pet says, for a bubble above the Dock icon; true when it was shown there. */
    var onSay: (String) -> Bool = { _ in false }

    func start() {
        art = PetArt.load(Settings.pet)
        poses = [:]
        NSApp.dockTile.contentView = view
        schedule()
        // Say hi once the icon has had a moment to appear.
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [weak self] in self?.say("hello") }
    }

    /** Says a line above the icon; when that can't be shown, the glyph in the icon's corner speaks instead. */
    private func say(_ key: String, vars: [String: String] = [:], glyph: String? = nil, seconds: Double = 2.6) {
        if let line = art.line(key, vars: vars), onSay(line) { return }
        if let glyph { show(glyph, seconds) }
    }

    /** Redraws only as often as it shows: each frame redraws the whole Dock icon. */
    private func schedule() {
        let lowPower = ProcessInfo.processInfo.isLowPowerModeEnabled
        let busy = !until.values.allSatisfy { $0 < Date() } || Date().timeIntervalSince(lastActivity) < 20
        let fps: Double = sleeping ? (lowPower ? 2 : 4) : busy ? (lowPower ? 10 : 15) : (lowPower ? 6 : 10)
        guard timer == nil || interval != 1 / fps else { return }
        interval = 1 / fps
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in self?.frame() }
        timer?.tolerance = interval / 4
    }

    /**
     Now and then, while you pause, a spin, the zoomies, a hum or a passing thought. Not activity: the pet still
     falls asleep. Not in Low Power Mode, and not over something else it's doing or showing.
     */
    private func maybeAntic(_ now: Date) {
        guard !PetArt.antics.isEmpty, now >= nextAntic else { return }
        // Busy now: try again shortly, so a pause soon after still gets one.
        nextAntic = now.addingTimeInterval(20)
        let f = flags()
        guard !sleeping, !ProcessInfo.processInfo.isLowPowerModeEnabled, now.timeIntervalSince(lastActivity) > 15,
              !f.contains("hiding"), !active("excited"), !(bubble.map { $0.until > now } ?? false),
              let key = PetArt.antics.randomElement(), let r = PetArt.reactions[key] else { return }
        nextAntic = now.addingTimeInterval(.random(in: PetArt.anticEvery))
        if let mood = r["mood"] as? String { flash(mood, ((r["ms"] as? Double) ?? 1200) / 1000) }
        if Double.random(in: 0..<1) < ((r["chance"] as? Double) ?? 1) {
            say(key, glyph: r["glyph"] as? String ?? "…", seconds: 2.4)
        } else if let glyph = r["glyph"] as? String, r["mood"] == nil {
            show(glyph, 1.6)
        }
    }

    func stop() {
        timer?.invalidate()
        timer = nil
        NSApp.dockTile.contentView = nil
        NSApp.dockTile.display()
    }

    func choose(_ id: String) {
        art = PetArt.load(id)
        poses = [:]
    }

    // ---- Behaving ----------------------------------------------------------

    private func active(_ mood: String) -> Bool { (until[mood] ?? .distantPast) > Date() }

    private func flash(_ mood: String, _ seconds: Double) {
        if mood == "happy" && !active("happy") { happyAt = Date() }
        if mood == "spin" && !active("spin") { spinAt = Date() }
        until[mood] = max(until[mood] ?? .distantPast, Date().addingTimeInterval(seconds))
    }

    private func show(_ glyph: String, _ seconds: Double = 2.6) {
        bubble = (glyph, Date().addingTimeInterval(seconds))
    }

    @discardableResult
    private func wake() -> Bool {
        lastActivity = Date()
        guard sleeping else { return false }
        sleeping = false
        flash("curious", 1.2)
        say("wake", glyph: "!", seconds: 1.5)
        return true
    }

    /** The messages pet.html takes, as the Mac sends them. */
    func receive(_ message: [String: Any]) {
        switch message["type"] as? String {
        case "react":
            guard let key = message["key"] as? String, let r = PetArt.reactions[key] else { return }
            let cooldown = (r["cooldown"] as? Double) ?? 0
            if let last = lastReact[key], Date().timeIntervalSince(last) < cooldown { return }
            lastReact[key] = Date()
            wake()
            let mood = r["mood"] as? String
            if let mood { flash(mood, ((r["ms"] as? Double) ?? 1200) / 1000) }
            if Double.random(in: 0..<1) < ((r["chance"] as? Double) ?? 1) {
                say(key, vars: message["vars"] as? [String: String] ?? [:],
                    glyph: mood == "hiding" ? "!" : (r["hearts"] != nil || mood == "happy") ? "♥" : mood == "curious" ? "?" : "…")
            }
        case "feed":
            wake()
            flash("happy", 1.1)
            say(PetArt.snacks.randomElement()?["key"] ?? "eatCurly", glyph: "♥", seconds: 2.2)
        case "typing":
            // Now and then, as pet.html does: not every burst of typing gets a line.
            if !wake() && Date().timeIntervalSince(lastTypingLine) > 90 && Double.random(in: 0..<1) < 0.3 {
                lastTypingLine = Date()
                say("typing")
            }
            flash("excited", 2.5)
        default: // "active", and anything else, means someone's there
            wake()
        }
    }

    private func flags() -> Set<String> {
        let hiding = active("hiding"), happy = active("happy"), closed = sleeping || hiding
        var f: Set<String> = []
        if hiding { f.insert("hiding"); f.insert("puffed") }
        if happy { f.insert("happy") }
        if sleeping { f.insert("sleeping") }
        if active("curious") && !sleeping { f.insert("curious") }
        f.insert(closed ? "eyesClosed" : happy ? "eyesHappy" : "eyesOpen")
        return f
    }

    // ---- Drawing -----------------------------------------------------------

    private func frame() {
        let now = Date()
        let dt = min(0.1, now.timeIntervalSince(lastFrame))
        lastFrame = now
        if !sleeping && now.timeIntervalSince(lastActivity) > Self.sleepAfter {
            sleeping = true
            schedule()
            show("z", .infinity)
            say("sleep")
        }
        if !sleeping, bubble?.glyph == "z" { bubble = nil }
        maybeAntic(now)
        schedule()
        // Walking in place, it turns around now and then, as it would at the end of the Dock.
        if art.flip && !sleeping && now > nextTurn {
            facingLeft.toggle()
            nextTurn = now.addingTimeInterval(.random(in: 5...12))
        }

        let f = flags()
        let excited = active("excited") && !sleeping
        let tempo = f.contains("hiding") ? 0 : excited ? 3.0 : sleeping ? 0.25 : 1
        clock += dt * tempo

        let size = NSSize(width: 256, height: 256)
        view.image = NSImage(size: size, flipped: false) { [self] rect in
            guard let g = NSGraphicsContext.current?.cgContext else { return false }
            draw(g, in: rect, flags: f, now: now)
            if let bubble, bubble.until > now { drawBubble(g, bubble.glyph) }
            return true
        }
        NSApp.dockTile.display()
    }

    /** The pet in the middle of the icon, as big as fits with room for a happy hop. */
    private func draw(_ g: CGContext, in rect: CGRect, flags f: Set<String>, now: Date) {
        let box = art.bounds
        let hop = 14.0
        let scale = min(rect.width * 0.9 / box.width, rect.height * 0.86 / (box.height + hop))
        g.saveGState()
        // Into the art's coordinates: y down, the art box's centre on the icon's centre.
        g.translateBy(x: rect.midX, y: rect.midY)
        g.scaleBy(x: scale, y: -scale)
        g.translateBy(x: -box.midX, y: -box.midY)

        var ty = 0.0, rot = 0.0
        if !sleeping { ty = art.bob.amount * 0.4 * sin(2 * .pi * now.timeIntervalSince1970 / art.bob.period) }
        if f.contains("happy") {
            let p = min(1, now.timeIntervalSince(happyAt) / 1.1)
            ty -= hop * sin(.pi * p); rot -= 12 * sin(2 * .pi * p)
        }
        if active("spin") { rot += 360 * min(1, now.timeIntervalSince(spinAt) / 0.8) }
        g.translateBy(x: 0, y: ty)
        rotate(g, rot, about: CGPoint(x: 60, y: 40))
        if art.flip && facingLeft { g.translateBy(x: 120, y: 0); g.scaleBy(x: -1, y: 1) }

        // Each group's pose eases toward the current mood's.
        let moods = ["hiding", "sleeping", "worried", "curious"].filter(f.contains)
        for group in Set(art.parts.map(\.group)) {
            let target = moods.lazy.compactMap { self.art.poses[$0]?[group] }.first ?? Pose()
            var pose = poses[group] ?? Pose(pivot: target.pivot)
            pose.tx += (target.tx - pose.tx) * 0.15; pose.ty += (target.ty - pose.ty) * 0.15
            pose.s += (target.s - pose.s) * 0.15; pose.r += (target.r - pose.r) * 0.15
            pose.pivot = target.pivot
            poses[group] = pose
        }

        for part in art.parts {
            if let when = part.when, !when.contains(where: f.contains) { continue }
            let pose = poses[part.group] ?? Pose()
            g.saveGState()
            g.translateBy(x: pose.pivot.x + pose.tx, y: pose.pivot.y + pose.ty)
            g.rotate(by: pose.r * .pi / 180)
            g.scaleBy(x: pose.s, y: pose.s)
            g.translateBy(x: -pose.pivot.x, y: -pose.pivot.y)
            if let m = art.groupMotion[part.group] {
                g.translateBy(x: m.pivot.x, y: m.pivot.y)
                g.scaleBy(x: 1 + (m.sx?.at(clock) ?? 0), y: 1 + (m.sy?.at(clock) ?? 0))
                g.translateBy(x: -m.pivot.x, y: -m.pivot.y)
            }
            if let wave = part.rot { rotate(g, wave.at(clock), about: part.pivot) }
            part.draw(in: g)
            g.restoreGState()
        }
        g.restoreGState()
    }

    private func rotate(_ g: CGContext, _ degrees: Double, about p: CGPoint) {
        g.translateBy(x: p.x, y: p.y)
        g.rotate(by: degrees * .pi / 180)
        g.translateBy(x: -p.x, y: -p.y)
    }

    private func drawBubble(_ g: CGContext, _ glyph: String) {
        let bubble = CGRect(x: 168, y: 180, width: 80, height: 70)
        g.setFillColor(.white)
        g.addPath(CGPath(roundedRect: bubble, cornerWidth: 32, cornerHeight: 32, transform: nil))
        g.fillPath()
        g.move(to: CGPoint(x: 180, y: 190)); g.addLine(to: CGPoint(x: 164, y: 168)); g.addLine(to: CGPoint(x: 202, y: 182))
        g.fillPath()
        let color = glyph == "♥" ? NSColor.systemPink : NSColor(srgbRed: 0.1, green: 0.11, blue: 0.13, alpha: 1)
        let text = NSAttributedString(string: glyph, attributes: [.font: NSFont.systemFont(ofSize: 50, weight: .heavy), .foregroundColor: color])
        let size = text.size()
        text.draw(at: NSPoint(x: bubble.midX - size.width / 2, y: bubble.midY - size.height / 2))
    }
}
