package com.chelayel.tidepets.pet

import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

/**
 * What the pet is doing: where it is, which way it faces, its mood, what it's saying.
 * The same rules as web/pet.html, so a pet behaves alike in both IDEs. Time comes from
 * [clock] so previews can render a fixed moment.
 */
class PetBrain(
    private val catalog: PetCatalog,
    var pet: Pet,
    var name: String,
    private val clock: () -> Long = System::currentTimeMillis,
    private val random: Random = Random.Default,
) {
    class Bubble(val x: Double, val y: Double, val size: Double, val dx: Double, val born: Long)

    // Position, in pixels from the left of the area the pet swims in.
    var x = 20.0; private set
    var dir = 1; private set
    private var speed = 0.4
    /** Pixels above the lowest position; eases toward [depthTarget]. */
    var depth = 0.0; private set
    private var depthTarget = 0.0
    private var nextDepthAt = 0L

    /** Seconds of limb motion; runs faster when excited, stops when hiding. */
    var animClock = 0.0; private set
    var errors = 0; private set
    var debugging = false; private set
    var sleeping = false; private set
    private val until = HashMap<String, Long>()
    var happyAt = 0L; private set
    var spinAt = 0L; private set
    private var lastActivity = clock()
    private var lastTypingLine = 0L

    var speech: String? = null; private set
    var speechUntil = 0L; private set
    val bubbles = ArrayList<Bubble>()
    /** Per group, the pose currently drawn (eased toward the mood's target). */
    val poses = HashMap<String, DoubleArray>()

    fun now() = clock()
    fun active(mood: String) = (until[mood] ?: 0L) > now()

    private fun flash(mood: String, ms: Long) {
        if (mood == "happy" && !active("happy")) happyAt = now()
        if (mood == "spin" && !active("spin")) spinAt = now()
        until[mood] = max(until[mood] ?: 0L, now() + ms)
    }

    /** The flags parts are shown by (`when` in pets.json) and poses are chosen by. */
    fun flags(): Set<String> {
        val hiding = active("hiding")
        val happy = active("happy")
        val closed = sleeping || hiding
        val worried = errors > 0 && !happy && !sleeping
        return buildSet {
            if (hiding) add("hiding")
            if (happy) add("happy")
            if (worried) add("worried")
            if (sleeping) add("sleeping")
            if (active("curious") && !sleeping) add("curious")
            if (debugging) add("debugging")
            if (worried || hiding) add("puffed")
            if (closed) add("eyesClosed") else if (happy) add("eyesHappy") else add("eyesOpen")
        }
    }

    // ---- Talking ----------------------------------------------------------

    fun say(text: String, ms: Long = 2600) { speech = text; speechUntil = now() + ms }

    private fun sayLine(key: String, ms: Long = 2600, task: String? = null) {
        val line = catalog.lines(pet, key).random(random)
        say(
            line.replace("{name}", name).replace("{task}", task ?: "The task")
                .replace("{errors}", "$errors error${if (errors == 1) "" else "s"}"),
            ms,
        )
    }

    private fun blow(count: Int) {
        val t = now()
        repeat(count) { i ->
            bubbles.add(Bubble(random.nextDouble(-5.0, 5.0), 0.0, 4 + random.nextDouble() * 6, random.nextDouble(-12.0, 12.0), t + i * 180L))
        }
    }

    fun mouthBubbleOrigin(): Pair<Double, Double> = pet.mouthX to pet.mouthY

    private fun wake(): Boolean {
        lastActivity = now()
        if (!sleeping) return false
        sleeping = false
        flash("curious", 1200)
        sayLine("wake")
        return true
    }

    // ---- Events from the IDE -----------------------------------------------

    fun hello() { if (now() > speechUntil) sayLine("hello", 2200) }

    fun typing() {
        val woke = wake()
        flash("excited", 2500)
        if (!woke && now() - lastTypingLine > 90_000 && random.nextDouble() < 0.3) { lastTypingLine = now(); sayLine("typing", 1800) }
    }

    fun saved() {
        wake()
        if (errors > 0) sayLine("savedWithErrors") else { flash("happy", 1100); blow(3); sayLine("save", 1800) }
    }

    fun errorsChanged(count: Int) {
        wake()
        val before = errors
        errors = count
        if (count > before) {
            if (count - before >= 3) { flash("hiding", 3000); sayLine("yikes") } else sayLine("worried")
        } else if (count == 0 && before > 0) { flash("happy", 1100); blow(6); sayLine("fixed") }
    }

    fun fileChanged(count: Int) {
        val woke = wake()
        errors = count
        flash("curious", 1500)
        if (!woke && random.nextDouble() < 0.25) sayLine("file", 1600)
    }

    fun taskFinished(ok: Boolean, task: String) {
        wake()
        if (ok) { flash("happy", 1100); blow(6); sayLine("taskOk", task = task) }
        else { flash("hiding", 2200); sayLine("taskFail", task = task) }
    }

    fun debug(active: Boolean) {
        wake()
        debugging = active
        sayLine(if (active) "debugOn" else "debugOff")
    }

    fun clicked() {
        val woke = wake()
        flash("spin", 800)
        blow(5)
        if (!woke) sayLine("click", 1600)
    }

    // ---- Motion -------------------------------------------------------------

    /** Advance by [dtMs] in an area [width] wide with [room] pixels to drift up and down in. */
    fun update(dtMs: Double, width: Double, spriteWidth: Double, room: Double) {
        val t = now()
        val dt = min(64.0, dtMs) / 16.7
        if (!sleeping && !debugging && t - lastActivity > 3 * 60_000) { sleeping = true; sayLine("sleep", 2000) }

        val f = flags()
        val excited = active("excited") && !sleeping
        var target = 0.4 * pet.speed
        if (sleeping || "hiding" in f || "curious" in f || active("spin")) target = 0.0
        else if (excited) target = 1.7 * pet.speed
        else if (debugging) target = 0.8 * pet.speed
        else if ("worried" in f) target = 0.22 * pet.speed
        speed += (target - speed) * 0.06 * dt

        x += speed * dir * dt
        val maxX = max(0.0, width - spriteWidth - 4)
        if (x > maxX) { x = maxX; dir = -1 }
        if (x < 4) { x = 4.0; dir = 1 }
        if (speed > 0.1 && random.nextDouble() < 0.0015 * dt) dir = -dir

        if (t >= nextDepthAt) {
            depthTarget = if (sleeping || pet.floor) 0.0 else random.nextDouble() * room
            nextDepthAt = t + 4000
        }
        depth += (depthTarget - depth) * 0.02 * dt

        val tempo = when {
            "hiding" in f -> 0.0
            excited -> 3.5
            sleeping -> 0.25
            "worried" in f -> 0.65
            else -> 1.0
        }
        animClock += dtMs / 1000 * tempo

        // Ease every group toward its pose for the current mood.
        val moods = listOf("hiding", "sleeping", "worried", "curious").filter { it in f }
        val groups = pet.parts.map { it.group }.toSet()
        for (g in groups) {
            val p = moods.firstNotNullOfOrNull { pet.poses[it]?.get(g) } ?: Pose()
            val cur = poses.getOrPut(g) { doubleArrayOf(0.0, 0.0, 1.0, 0.0, p.px, p.py) }
            val target6 = doubleArrayOf(p.tx, p.ty, p.s, p.r)
            for (k in 0..3) cur[k] += (target6[k] - cur[k]) * 0.15 * dt
            cur[4] = p.px; cur[5] = p.py
        }

        bubbles.removeAll { t - it.born > 1800 }
    }

    /** Switch to another pet in place, keeping position and mood. */
    fun become(next: Pet, newName: String) {
        pet = next
        name = newName
        poses.clear()
    }
}
