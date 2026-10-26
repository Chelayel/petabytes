import AppKit

/**
 The pets as web/pets.json describes them, for drawing natively (the Dock icon): shapes in a 120x80 box facing
 right, grouped so each mood can pose a group, with some parts and groups oscillating. A port of the JetBrains
 plugin's PetArt.kt.
 */
struct Wave {
    let amount, period, phase: Double

    init?(_ value: Any?) {
        guard let n = numbers(value), n.count >= 2 else { return nil }
        amount = n[0]; period = n[1]; phase = n.count > 2 ? n[2] : 0
    }

    func at(_ t: Double) -> Double { amount * sin(2 * .pi * (t / period + phase)) }
}

struct Pose {
    var tx = 0.0, ty = 0.0, s = 1.0, r = 0.0
    var pivot = CGPoint(x: 60, y: 40)
}

struct ArtPart {
    let group: String
    let path: CGPath
    let fill: CGColor?
    let stroke: CGColor?
    let strokeWidth: CGFloat
    let opacity: CGFloat
    let pivot: CGPoint
    let rot: Wave?
    let when: [String]?

    /** Fills and outlines the part in art coordinates; the caller has set up the transform. */
    func draw(in g: CGContext) {
        g.setAlpha(opacity)
        if let fill {
            g.addPath(path)
            g.setFillColor(fill)
            g.fillPath()
        }
        if let stroke {
            g.addPath(path)
            g.setStrokeColor(stroke)
            g.setLineWidth(strokeWidth)
            g.setLineCap(.round); g.setLineJoin(.round)
            g.strokePath()
        }
    }
}

struct PetArt {
    let id: String
    let name: String
    let label: String
    /** The pet's own lines; the rest come from the shared ones. */
    private let lines: [String: [String]]
    let flip: Bool
    let bob: (amount: Double, period: Double)
    let accent: CGColor
    let parts: [ArtPart]
    /** mood → group → pose */
    let poses: [String: [String: Pose]]
    let groupMotion: [String: (sx: Wave?, sy: Wave?, pivot: CGPoint)]
    /** The art's extent, widened to be the same either way the pet faces. */
    let bounds: CGRect

    /** What each reaction key makes the pet do, from pets.json's reactions. */
    static let reactions: [String: [String: Any]] = (root["reactions"] as? [String: [String: Any]]) ?? [:]
    /** The snacks Feed drops; each has the key of the lines the pet says eating it. */
    static let snacks: [[String: String]] = (root["snacks"] as? [[String: String]]) ?? []
    private static let sharedLines: [String: [String]] = (root["lines"] as? [String: [String]]) ?? [:]

    private static let root: [String: Any] =
        (try? JSONSerialization.jsonObject(with: Data(Catalog.json.utf8))) as? [String: Any] ?? [:]

    static func load(_ id: String) -> PetArt {
        let pets = root["pets"] as? [String: [String: Any]] ?? [:]
        guard let pet = pets[id] ?? pets["turtle"] else { fatalError("pets.json has no pets") }
        return PetArt(id: id, pet)
    }

    private init(id: String, _ m: [String: Any]) {
        self.id = id
        name = m["name"] as? String ?? id
        label = m["label"] as? String ?? id
        lines = m["lines"] as? [String: [String]] ?? [:]
        flip = m["flip"] as? Bool ?? false
        let b = numbers(m["bob"]) ?? [4, 3]
        bob = (b[0], b[1])
        parts = (m["parts"] as? [[String: Any]] ?? []).map(Self.part)
        accent = parts.lazy.compactMap(\.stroke).first ?? NSColor(srgbRed: 0.37, green: 0.92, blue: 0.83, alpha: 1).cgColor
        poses = (m["poses"] as? [String: [String: [String: Any]]] ?? [:]).mapValues { groups in
            groups.mapValues { p in
                let pivot = numbers(p["p"]) ?? [60, 40]
                return Pose(tx: p["tx"] as? Double ?? 0, ty: p["ty"] as? Double ?? 0, s: p["s"] as? Double ?? 1, r: p["r"] as? Double ?? 0,
                            pivot: CGPoint(x: pivot[0], y: pivot[1]))
            }
        }
        groupMotion = (m["groupMotion"] as? [String: [String: Any]] ?? [:]).mapValues { g in
            let p = numbers(g["p"]) ?? [60, 40]
            return (Wave(g["sx"]), Wave(g["sy"]), CGPoint(x: p[0], y: p[1]))
        }
        let box = parts.filter { $0.when == nil }.reduce(CGRect.null) { $0.union($1.path.boundingBoxOfPath.insetBy(dx: -$1.strokeWidth / 2, dy: -$1.strokeWidth / 2)) }
        let half = max(60 - box.minX, box.maxX - 60)
        bounds = CGRect(x: 60 - half, y: box.minY, width: 2 * half, height: box.height)
    }

    /** A line for the key, the pet's own if it has one, with {name}, {kind} and the given values filled in. */
    func line(_ key: String, vars: [String: String] = [:]) -> String? {
        guard let line = (lines[key] ?? Self.sharedLines[key])?.randomElement() else { return nil }
        let values = ["name": Settings.name.isEmpty ? name : Settings.name, "kind": label.lowercased(), "task": "The task"]
            .merging(vars) { _, given in given }
        return values.reduce(line) { text, pair in text.replacingOccurrences(of: "{\(pair.key)}", with: pair.value) }
    }

    /** The pet standing still with its eyes open, as big as fits in the middle of the picture. */
    func image(size: NSSize) -> NSImage {
        NSImage(size: size, flipped: false) { rect in
            guard let g = NSGraphicsContext.current?.cgContext else { return false }
            let scale = min(rect.width * 0.92 / bounds.width, rect.height * 0.92 / bounds.height)
            g.translateBy(x: rect.midX, y: rect.midY)
            g.scaleBy(x: scale, y: -scale)
            g.translateBy(x: -bounds.midX, y: -bounds.midY)
            for part in parts where part.when?.contains("eyesOpen") ?? true {
                g.saveGState()
                part.draw(in: g)
                g.restoreGState()
            }
            return true
        }
    }

    private static func part(_ m: [String: Any]) -> ArtPart {
        let path: CGPath
        if let d = m["path"] as? String {
            path = SvgPath.parse(d)
        } else if let c = numbers(m["circle"]) {
            path = CGPath(ellipseIn: CGRect(x: c[0] - c[2], y: c[1] - c[2], width: 2 * c[2], height: 2 * c[2]), transform: nil)
        } else {
            let e = numbers(m["ellipse"]) ?? [0, 0, 0, 0]
            path = CGPath(ellipseIn: CGRect(x: e[0] - e[2], y: e[1] - e[3], width: 2 * e[2], height: 2 * e[3]), transform: nil)
        }
        let pivot = numbers(m["pivot"]) ?? [60, 40]
        return ArtPart(
            group: m["group"] as? String ?? "",
            path: path,
            fill: (m["fill"] as? String).flatMap(color),
            stroke: (m["stroke"] as? String).flatMap(color),
            strokeWidth: CGFloat(m["sw"] as? Double ?? 1),
            opacity: CGFloat(m["opacity"] as? Double ?? 1),
            pivot: CGPoint(x: pivot[0], y: pivot[1]),
            rot: Wave(m["rot"]),
            when: m["when"] as? [String]
        )
    }
}

private func numbers(_ value: Any?) -> [Double]? {
    (value as? [Any])?.compactMap { ($0 as? NSNumber)?.doubleValue }
}

/** "#RRGGBB", "rgba(r,g,b,a)" or "none". */
private func color(_ s: String) -> CGColor? {
    if s.hasPrefix("#"), let v = UInt32(s.dropFirst(), radix: 16) {
        return CGColor(srgbRed: CGFloat(v >> 16 & 0xFF) / 255, green: CGFloat(v >> 8 & 0xFF) / 255, blue: CGFloat(v & 0xFF) / 255, alpha: 1)
    }
    guard s.hasPrefix("rgba(") else { return nil }
    let n = s.dropFirst(5).dropLast().split(separator: ",").compactMap { Double($0.trimmingCharacters(in: .whitespaces)) }
    guard n.count == 4 else { return nil }
    return CGColor(srgbRed: n[0] / 255, green: n[1] / 255, blue: n[2] / 255, alpha: n[3])
}

/** The subset of SVG path syntax the art uses: M L H V Q C Z, absolute and relative. */
enum SvgPath {
    static func parse(_ d: String) -> CGPath {
        let regex = try! NSRegularExpression(pattern: "[MmLlHhVvQqCcZz]|-?(?:\\d+\\.?\\d*|\\.\\d+)(?:[eE][-+]?\\d+)?")
        let tokens = regex.matches(in: d, range: NSRange(d.startIndex..., in: d)).map { String(d[Range($0.range, in: d)!]) }
        let path = CGMutablePath()
        var i = 0, cmd: Character = "M"
        var x = 0.0, y = 0.0, sx = 0.0, sy = 0.0
        func num() -> Double { defer { i += 1 }; return Double(tokens[i]) ?? 0 }
        while i < tokens.count {
            if let c = tokens[i].first, c.isLetter { cmd = c; i += 1 }
            let rel = cmd.isLowercase
            let ox = rel ? x : 0, oy = rel ? y : 0
            switch cmd.uppercased() {
            case "M":
                x = ox + num(); y = oy + num()
                path.move(to: CGPoint(x: x, y: y)); sx = x; sy = y
                cmd = rel ? "l" : "L"
            case "L": x = ox + num(); y = oy + num(); path.addLine(to: CGPoint(x: x, y: y))
            case "H": x = ox + num(); path.addLine(to: CGPoint(x: x, y: y))
            case "V": y = oy + num(); path.addLine(to: CGPoint(x: x, y: y))
            case "Q":
                let cx = ox + num(), cy = oy + num()
                x = ox + num(); y = oy + num()
                path.addQuadCurve(to: CGPoint(x: x, y: y), control: CGPoint(x: cx, y: cy))
            case "C":
                let c1 = CGPoint(x: ox + num(), y: oy + num()), c2 = CGPoint(x: ox + num(), y: oy + num())
                x = ox + num(); y = oy + num()
                path.addCurve(to: CGPoint(x: x, y: y), control1: c1, control2: c2)
            case "Z":
                path.closeSubpath(); x = sx; y = sy
            default:
                i += 1
            }
        }
        return path
    }
}
