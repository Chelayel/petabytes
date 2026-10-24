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

    /** Whether the pet steps aside while an app is full screen. */
    static var hideInFullScreen: Bool {
        get { defaults.object(forKey: "hideInFullScreen") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "hideInFullScreen") }
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
        /** tide (sea creatures), home (dogs, cats and friends) or snacks (food with feet). */
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
