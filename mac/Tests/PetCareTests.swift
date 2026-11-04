import XCTest
@testable import Petabytes

final class PetCareTests: XCTestCase {
    private final class Clock { var time = 10_000_000.0 }

    private func makeCare(_ clock: Clock) throws -> PetCare {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        let data = try Data(contentsOf: root.appendingPathComponent("web/pets.json"))
        let catalog = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
        return PetCare(rules: try XCTUnwrap(catalog["care"] as? [String: Any]), now: { clock.time })
    }

    func testMealGrowthBurstAndRecovery() throws {
        let clock = Clock()
        let pet = try makeCare(clock)
        for _ in 0..<3 { XCTAssertEqual(pet.feed(), .snack); _ = pet.update(17) }
        XCTAssertEqual(pet.fullness, 0)
        var previous = 0.0
        for _ in 4..<8 {
            XCTAssertEqual(pet.feed(), .overfed)
            for _ in 0..<35 { _ = pet.update(17) }
            XCTAssertGreaterThan(pet.fullness, previous)
            previous = pet.fullness
        }
        XCTAssertEqual(pet.feed(), .burst)
        XCTAssertEqual(pet.feed(), .ignored)
        XCTAssertEqual(pet.poke(), .ignored)
        clock.time += pet.rule("windupMs") + 1
        XCTAssertTrue(pet.splashed)
        clock.time += pet.rule("burstMs")
        XCTAssertTrue(pet.update(17))
        XCTAssertFalse(pet.bursting)
        XCTAssertEqual(pet.meal, 0)
        XCTAssertEqual(pet.fullness, 0)
        XCTAssertEqual(pet.feed(), .snack)
    }

    func testMealBreakAndPetReset() throws {
        let clock = Clock(), pet = try makeCare(clock)
        for _ in 0..<7 { _ = pet.feed() }
        _ = pet.update(64)
        clock.time += pet.rule("mealGapMs") + 1
        for _ in 0..<35 { _ = pet.update(17) }
        XCTAssertEqual(pet.meal, 0)
        XCTAssertLessThan(pet.fullness, 0.02)
        XCTAssertEqual(pet.feed(), .snack)
        XCTAssertEqual(pet.meal, 1)
        for _ in 0..<7 { _ = pet.feed() }
        XCTAssertTrue(pet.bursting)
        pet.reset()
        XCTAssertFalse(pet.bursting)
        XCTAssertFalse(pet.angry)
        XCTAssertEqual(pet.fullness, 0)
        XCTAssertEqual(pet.pokes, 0)
    }

    func testPokingCooldownAndSoothing() throws {
        let clock = Clock(), pet = try makeCare(clock)
        XCTAssertEqual(pet.poke(), .playful)
        XCTAssertEqual(pet.poke(), .playful)
        XCTAssertEqual(pet.poke(), .warning)
        XCTAssertEqual(pet.poke(), .warning)
        XCTAssertEqual(pet.poke(), .angry)
        XCTAssertTrue(pet.angry)
        let start = pet.angryAt
        clock.time += 1500
        XCTAssertEqual(pet.poke(), .angry)
        XCTAssertEqual(pet.angryAt, start)
        XCTAssertEqual(pet.angryRemainingMs, pet.rule("angerMs"))
        clock.time += pet.rule("angerMs") + 1
        XCTAssertFalse(pet.angry)
        XCTAssertEqual(pet.poke(), .playful)
        for _ in 0..<4 { _ = pet.poke() }
        XCTAssertTrue(pet.angry)
        _ = pet.feed()
        XCTAssertFalse(pet.angry)
        XCTAssertEqual(pet.pokes, 0)
    }
}
