import Foundation

/** Where the pet lives: swimming along the top of the Dock, or in a small sea you can drag anywhere. */
enum Place: String {
    case dock, float
}

/** What the person chose, kept in UserDefaults. */
enum Settings {
    private static let defaults = UserDefaults.standard

    static var pet: String {
        get { defaults.string(forKey: "pet") ?? "turtle" }
        set { defaults.set(newValue, forKey: "pet") }
    }

    /** Empty for the pet's own name. */
    static var name: String {
        get { defaults.string(forKey: "name") ?? "" }
        set { defaults.set(newValue, forKey: "name") }
    }

    static var place: Place {
        get { Place(rawValue: defaults.string(forKey: "place") ?? "") ?? .dock }
        set { defaults.set(newValue.rawValue, forKey: "place") }
    }

    /** Whether the app's icon is in the Dock (where it can be kept) instead of the menu bar. */
    static var showInDock: Bool {
        get { defaults.bool(forKey: "showInDock") }
        set { defaults.set(newValue, forKey: "showInDock") }
    }

    /** Whether the pet in the Dock icon talks in a bubble above it (needs Accessibility to find the icon). */
    static var talkInDock: Bool {
        get { defaults.object(forKey: "talkInDock") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "talkInDock") }
    }

    /** Whether we've explained and asked for Accessibility once already, so it isn't asked again unbidden. */
    static var askedForAccessibility: Bool {
        get { defaults.bool(forKey: "askedForAccessibility") }
        set { defaults.set(newValue, forKey: "askedForAccessibility") }
    }

    /** Whether the pet reacts to what Claude Code is doing (the Petabytes add-on for Claude Code tells it). */
    static var claudeCode: Bool {
        get { defaults.object(forKey: "claudeCode") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "claudeCode") }
    }

    /** Whether the pet steps aside while an app is full screen. */
    static var hideInFullScreen: Bool {
        get { defaults.object(forKey: "hideInFullScreen") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "hideInFullScreen") }
    }

    /** When the app last asked GitHub for a newer version. */
    static var lastUpdateCheck: Date {
        get { defaults.object(forKey: "lastUpdateCheck") as? Date ?? .distantPast }
        set { defaults.set(newValue, forKey: "lastUpdateCheck") }
    }

    /** The newest version the app has already offered unasked, so the daily check offers each one once. */
    static var offeredUpdate: String {
        get { defaults.string(forKey: "offeredUpdate") ?? "" }
        set { defaults.set(newValue, forKey: "offeredUpdate") }
    }

    /** When the app first ran, set on first read. */
    static var firstRun: Date {
        if let date = defaults.object(forKey: "firstRun") as? Date { return date }
        defaults.set(Date(), forKey: "firstRun")
        return Date()
    }

    /** When to next ask for a star or a coffee; distantFuture once answered or turned down for good. */
    static var askForSupportAfter: Date? {
        get { defaults.object(forKey: "askForSupportAfter") as? Date }
        set { defaults.set(newValue, forKey: "askForSupportAfter") }
    }

    static var visible: Bool {
        get { defaults.object(forKey: "visible") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "visible") }
    }

    /** Bottom-left corner of the floating sea, in screen coordinates. */
    static var floatOrigin: CGPoint? {
        get {
            guard let x = defaults.object(forKey: "floatX") as? Double, let y = defaults.object(forKey: "floatY") as? Double else { return nil }
            return CGPoint(x: x, y: y)
        }
        set {
            defaults.set(newValue.map { Double($0.x) }, forKey: "floatX")
            defaults.set(newValue.map { Double($0.y) }, forKey: "floatY")
        }
    }
}

/** The pets in web/pets.json, in the order the menus list them. */
struct Catalog: Decodable {
    struct Pet: Decodable {
        let name: String
        let label: String?
        /** tide (sea creatures), home (dogs, cats and friends), snacks (food with feet), games (pixel characters) or gadgets (things on your desk). */
        let set: String?
    }

    let order: [String]
    let pets: [String: Pet]

    static let json: String = {
        guard let url = Bundle.main.url(forResource: "pets", withExtension: "json"),
              let text = try? String(contentsOf: url, encoding: .utf8) else { fatalError("pets.json is missing from the app bundle") }
        return text
    }()

    static let shared: Catalog = {
        do { return try JSONDecoder().decode(Catalog.self, from: Data(json.utf8)) }
        catch { fatalError("pets.json doesn't parse: \(error)") }
    }()
}
