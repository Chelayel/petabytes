import Foundation

/** The Dock icon's meal and poke counters. The rules come from the same catalog as web/pet.html. */
final class PetCare {
    enum Meal { case snack, overfed, burst, ignored }
    enum Poke { case playful, warning, angry, ignored }

    private let rules: [String: Any]
    private let now: () -> Double
    private(set) var meal = 0
    private(set) var fullness = 0.0
    private(set) var pokes = 0
    private var lastFed = -Double.infinity, lastPoke = -Double.infinity
    private var angryUntil = -Double.infinity
    private(set) var angryAt: Double?
    private(set) var burstAt: Double?

    init(rules: [String: Any], now: @escaping () -> Double = { Date().timeIntervalSince1970 * 1000 }) {
        self.rules = rules
        self.now = now
    }

    func rule(_ key: String) -> Double { (rules[key] as? NSNumber)?.doubleValue ?? 0 }
    var angry: Bool { now() < angryUntil }
    var angryRemainingMs: Double { max(0, angryUntil - now()) }
    var bursting: Bool { burstAt != nil }
    var splashed: Bool { burstAt.map { now() - $0 >= rule("windupMs") } ?? false }

    func reset() {
        meal = 0; fullness = 0; pokes = 0
        lastFed = -.infinity; lastPoke = -.infinity; angryUntil = -.infinity
        burstAt = nil
        angryAt = nil
    }

    func feed() -> Meal {
        guard !bursting else { return .ignored }
        if now() - lastFed > rule("mealGapMs") { meal = 0 }
        lastFed = now()
        meal += 1
        pokes = 0; angryUntil = -.infinity; angryAt = nil
        if meal >= Int(rule("burstAt")) { burstAt = now(); return .burst }
        return meal > Int(rule("safeFeeds")) ? .overfed : .snack
    }

    func poke() -> Poke {
        guard !bursting else { return .ignored }
        pokes = now() - lastPoke > rule("pokeGapMs") ? 1 : pokes + 1
        lastPoke = now()
        if pokes >= Int(rule("angryAt")) || angry {
            if !angry { angryAt = now() }
            angryUntil = now() + rule("angerMs")
            return .angry
        }
        return pokes >= 3 ? .warning : .playful
    }

    /** Returns true exactly once when the burst has finished and the pet can respawn. */
    func update(_ dtMs: Double) -> Bool {
        if meal > 0 && now() - lastFed > rule("mealGapMs") { meal = 0 }
        let target = Double(max(0, meal - Int(rule("safeFeeds"))))
        fullness += (target - fullness) * min(1, 0.12 * min(64, dtMs) / 16.7)
        if let burstAt, now() - burstAt >= rule("burstMs") {
            reset()
            return true
        }
        return false
    }
}
