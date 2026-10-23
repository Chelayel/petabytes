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
    class Bubble(val x: Double, val y: Double, val size: Double, val dx: Double, val born: Long, val heart: Boolean = false)

    /** A snack sinking toward the pet: [x] in pixels across the area, [y] pixels from its top. */
    class Food(val snack: Snack, val x: Double, var y: Double)

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

    /** False: the pet stays near [home] instead of swimming the whole width. */
    var roam = false
    /** Where the pet stays when it isn't roaming, as a fraction of the width. */
    var home = 0.95
    /** Held by the mouse: it follows the pointer and doesn't swim. */
    var dragging = false
    /** The caret is on a line the pet covers: it fades and swims clear of [avoidX]. */
    var dodging = false; private set
    private var avoidX = 0.0

    private val lastReact = HashMap<String, Long>()
    private var sessionMark = clock()
    private var lastFed = clock()
    private var eaten = 0
    var food: Food? = null; private set

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

    private fun sayLine(key: String, ms: Long = 2600, task: String? = null, vars: Map<String, String> = emptyMap()) {
        val line = catalog.lines(pet, key).random(random)
        val all = mapOf(
            "name" to name, "kind" to pet.label.lowercase(), "task" to (task ?: "The task"), "branch" to "a new branch",
            "errors" to "$errors error${if (errors == 1) "" else "s"}",
        ) + vars
        say(Regex("\\{(\\w+)}").replace(line) { all[it.groupValues[1]] ?: it.value }, ms)
    }

    private fun blow(count: Int, heart: Boolean = false) {
        val t = now()
        repeat(count) { i ->
            bubbles.add(Bubble(random.nextDouble(-8.0, 8.0), 0.0, 4 + random.nextDouble() * 6, random.nextDouble(-14.0, 14.0), t + i * (if (heart) 200L else 180L), heart))
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

    /** Hello, or good morning / it's late, by the clock. */
    fun hello(hour: Int = java.time.LocalTime.now().hour) {
        if (now() <= speechUntil) return
        when {
            hour >= 23 || hour < 5 -> react("lateNight")
            hour in 5..9 -> react("morning")
            else -> sayLine("hello", 2200)
        }
    }

    /** An event the IDE reports by key; pets.json's reactions say what the pet does. */
    fun react(key: String, vars: Map<String, String> = emptyMap()) {
        val r = catalog.reactions[key] ?: return
        if (now() - (lastReact[key] ?: Long.MIN_VALUE / 2) < r.cooldownMs) return
        lastReact[key] = now()
        wake()
        r.mood?.let { flash(it, r.ms) }
        if (r.bubbles > 0) blow(r.bubbles)
        if (r.hearts > 0) blow(r.hearts, heart = true)
        if (random.nextDouble() < r.chance) sayLine(key, vars = vars)
    }

    /** Drop a snack (a random one unless [text] names it) somewhere across an area [width] wide. */
    fun feed(width: Double, text: String? = null) {
        if (food != null) return
        val snack = catalog.snacks.find { it.text == text } ?: catalog.snacks.random(random)
        food = Food(snack, 20 + random.nextDouble() * max(1.0, width - 60), -14.0)
        wake()
    }

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

    /** Follow the mouse while it drags the pet; [x] is the art box's left edge. */
    fun dragTo(x: Double, width: Double, spriteWidth: Double) {
        val clamped = x.coerceIn(4.0, max(4.0, width - spriteWidth - 4))
        if (clamped != this.x) dir = if (clamped > this.x) 1 else -1
        this.x = clamped
        speed = 0.0
        lastActivity = now()
        sleeping = false
    }

    /** Dropped: stay here from now on. */
    fun dropped(width: Double, spriteWidth: Double) {
        dragging = false
        roam = false
        home = if (width > spriteWidth) (x / (width - spriteWidth)).coerceIn(0.0, 1.0) else 0.0
    }

    /** The caret's x if it's on a line the pet covers, or null. */
    fun avoid(caretX: Double?) {
        dodging = caretX != null
        if (caretX != null) avoidX = caretX
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
        if (sleeping) sessionMark = t // a break resets the long-session clock
        if (!sleeping && t - sessionMark > 90 * 60_000) { sessionMark = t; react("longSession") }
        if (!sleeping && food == null && t - lastFed > 60 * 60_000) react("hungry")

        val f = flags()
        val excited = active("excited") && !sleeping
        val maxX = max(0.0, width - spriteWidth - 4)
        val snack = food
        if (snack != null && !dragging) {
            // The snack sinks to the pet's mouth line; the pet swims over to it.
            val scale = spriteWidth / 120
            val mouthLocal = if (pet.flip && dir < 0) 120 - pet.mouthX else pet.mouthX
            val mouthX = x + mouthLocal * scale
            val mouthY = spriteMouthTop + pet.mouthY * scale
            snack.y = min(snack.y + 0.9 * dt, mouthY - 8)
            val gap = snack.x - mouthX
            if (kotlin.math.abs(gap) < 14 && snack.y >= mouthY - 20) eat()
            else {
                if (kotlin.math.abs(gap) > 6) dir = if (gap > 0) 1 else -1
                speed += (2.0 * pet.speed - speed) * 0.1 * dt
                x += speed * dir * dt
            }
        } else if (dragging) {
            speed = 0.0
        } else if (dodging && roam) {
            // Swim clear of the caret, toward whichever side has more room.
            val center = x + spriteWidth / 2
            val clear = kotlin.math.abs(center - avoidX) > spriteWidth
            dir = if (avoidX > width / 2) -1 else 1
            speed += ((if (clear) 0.0 else 2.2) - speed) * 0.1 * dt
            x += speed * dir * dt
        } else if (!roam) {
            // Stay near home: drift a little either side of it, face where it's going.
            val target = home * maxX + 12 * kotlin.math.sin(t / 2600.0)
            val step = (target - x) * 0.04 * dt
            if (kotlin.math.abs(step) > 0.05) dir = if (step > 0) 1 else -1
            x += step
        } else {
            var target = 0.4 * pet.speed
            if (sleeping || "hiding" in f || "curious" in f || active("spin")) target = 0.0
            else if (excited) target = 1.7 * pet.speed
            else if (debugging) target = 0.8 * pet.speed
            else if ("worried" in f) target = 0.22 * pet.speed
            speed += (target - speed) * 0.06 * dt
            x += speed * dir * dt
            if (speed > 0.1 && random.nextDouble() < 0.0015 * dt) dir = -dir
        }
        if (x > maxX) { x = maxX; dir = -1 }
        if (x < 4) { x = 4.0; dir = 1 }

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

    /** Where the art box's top is (pixels from the area's top), set by the painter each frame for feeding. */
    var spriteMouthTop = 0.0

    private fun eat() {
        val snack = food ?: return
        food = null
        lastFed = now()
        eaten++
        flash("happy", 1100)
        blow(3)
        if (eaten % 5 == 0) react("full") else sayLine(snack.snack.key, 2200)
    }

    /** Switch to another pet in place, keeping position and mood. */
    fun become(next: Pet, newName: String) {
        pet = next
        name = newName
        poses.clear()
    }
}
