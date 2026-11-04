package com.chelayel.petabytes.pet

import kotlin.math.max
import kotlin.math.min
import kotlin.math.abs
import kotlin.math.pow
import kotlin.math.PI
import kotlin.math.sin
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
    class Food(val snack: Snack, var x: Double, var y: Double)

    // Position, in pixels from the left of the area the pet swims in.
    var x = 20.0; private set
    var dir = 1; private set
    private var speed = 0.4
    /** Pixels above the lowest position; eases toward [depthTarget]. */
    var depth = 0.0; private set
    private var depthTarget = 0.0
    private var nextDepthAt = 0L
    private var previousWidth = Double.NaN
    private var previousLimit = 0.0
    private var previousVertical = false
    /** A position or mood is still easing toward its target, rather than just breathing in place. */
    var settling = false; private set

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
    /** Where a roaming pet with nothing to do is heading, and until when it rests on arriving. */
    private var goal: Double? = null
    private var restUntil = 0L

    /**
     * True: the pet lives in a strip along the right edge and moves up and down; [x] is then its
     * distance from the top. False: it moves along the bottom edge and [x] is from the left.
     */
    var vertical = false

    /** Pixels per art unit, set by the painter. */
    var artScale = 0.62

    /** False: the pet stays near [home] instead of swimming the whole width. */
    var roam = false
    /** Where the pet stays when it isn't roaming, as a fraction of the width. */
    var home = 0.95
    /** Held by the mouse: it follows the pointer and doesn't swim. */
    var dragging = false
    /** The caret is on a line the pet covers: it fades and swims clear of [avoidX]. */
    var dodging = false; private set
    private var avoidX = 0.0

    /**
     * When the pet next does something on its own (pets.json's antics). Off while [quiet]: the IDE's power save mode.
     */
    private var nextAntic = 0L
    var quiet = false

    private val lastReact = HashMap<String, Long>()
    private var sessionMark = clock()
    private var lastFed = clock()
    private var eaten = 0
    var meal = 0; private set
    var fullness = 0.0; private set
    private var pokes = 0
    private var lastPoke = Long.MIN_VALUE / 2
    var angryAt = 0L; private set
    private var nextAngryLine = 0L
    private var tantrumOrigin: Pair<Double, Double>? = null
    private var tantrumDir = 1
    val tantrum get() = active("angry") && !quiet && !dragging && food == null && !bursting
    data class TantrumPose(val x: Double, val y: Double, val dir: Int, val phase: Double,
                          val scale: Double, val anchorX: Double, val anchorY: Double,
                          val side: Boolean, val captionWidth: Double, val hopHeight: Double)
    var burstAt: Long? = null; private set
    val bursting get() = burstAt != null
    val splashed get() = burstAt?.let { now() - it >= catalog.care.windupMs } ?: false
    val messAge get() = burstAt?.let { now() - it - catalog.care.windupMs } ?: -1L
    val messDuration get() = catalog.care.burstMs - catalog.care.windupMs
    val sizeX get() = 1 + fullness * pet.growthX
    val sizeY get() = 1 + fullness * pet.growthY
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
        val angry = active("angry")
        val hiding = active("hiding") && !angry
        val happy = active("happy") && !angry && !bursting
        val closed = sleeping || hiding
        val worried = (errors > 0 || bursting) && !angry && !happy && !sleeping
        return buildSet {
            if (hiding) add("hiding")
            if (happy) add("happy")
            if (angry) add("angry")
            if (worried) add("worried")
            if (sleeping) add("sleeping")
            if (active("curious") && !angry && !sleeping) add("curious")
            if (debugging) add("debugging")
            if (worried || hiding) add("puffed")
            if (closed) add("eyesClosed") else if (happy) add("eyesHappy") else if (!angry) add("eyesOpen")
        }
    }

    // ---- Talking ----------------------------------------------------------

    fun say(text: String, ms: Long = 2600) { speech = text; speechUntil = now() + ms }

    private fun sayLine(key: String, ms: Long = 2600, task: String? = null, vars: Map<String, String> = emptyMap()) {
        if (bursting && key != "burstWarning") return
        if (active("angry") && key != "angry") return
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
        if (bursting || active("angry")) return
        val r = catalog.reactions[key] ?: return
        if (now() - (lastReact[key] ?: Long.MIN_VALUE / 2) < r.cooldownMs) return
        lastReact[key] = now()
        wake()
        r.mood?.let { flash(it, r.ms) }
        if (r.bubbles > 0) blow(r.bubbles)
        if (r.hearts > 0) blow(r.hearts, heart = true)
        if (random.nextDouble() < r.chance) sayLine(key, vars = vars)
    }

    /**
     * Now and then, while you pause, a spin, the zoomies, a hum or a passing thought. Not activity: the pet still
     * falls asleep. Not mid-flow, and not over something else it's doing or saying.
     */
    private fun maybeAntic(t: Long) {
        if (catalog.antics.isEmpty() || t < nextAntic) return
        // Busy now: try again shortly, so a pause soon after still gets one.
        nextAntic = t + 20_000
        if (t - lastActivity < 15_000) return
        val f = flags()
        if (quiet || bursting || active("angry") || dragging || sleeping || debugging || food != null || "hiding" in f || "worried" in f || active("excited") || t <= speechUntil) return
        val (lo, hi) = catalog.anticEvery
        nextAntic = t + ((lo + random.nextDouble() * (hi - lo)) * 1000).toLong()
        val key = catalog.antics.random(random)
        val r = catalog.reactions[key] ?: return
        r.mood?.let { flash(it, r.ms) }
        if (r.bubbles > 0) blow(r.bubbles)
        if (r.hearts > 0) blow(r.hearts, heart = true)
        if (random.nextDouble() < r.chance) sayLine(key, 2400)
    }

    /** Drop a snack (a random one unless [text] names it) somewhere across an area [width] wide. */
    fun feed(width: Double, text: String? = null) {
        if (food != null || bursting) return
        val snack = catalog.snacks.find { it.text == text } ?: catalog.snacks.random(random)
        // Along the right edge the snack sinks down the pet's own column, from the top.
        food = if (vertical) Food(snack, -10.0, 0.0) else Food(snack, 20 + random.nextDouble() * max(1.0, width - 60), -14.0)
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
        if (bursting) return
        val woke = wake()
        pokes = if (now() - lastPoke > catalog.care.pokeGapMs) 1 else pokes + 1
        lastPoke = now()
        if (pokes >= catalog.care.angryAt || active("angry")) {
            val fresh = !active("angry")
            if (fresh) { angryAt = now(); tantrumOrigin = null; tantrumDir = dir }
            flash("angry", catalog.care.angerMs)
            until["spin"] = 0; until["happy"] = 0
            bubbles.clear()
            if (fresh || now() >= nextAngryLine) shout()
        } else if (pokes >= 3) {
            sayLine("pokeWarning", 1800)
        } else {
            flash("spin", 800)
            blow(5)
            if (!woke) sayLine("click", 1600)
        }
    }

    private fun shout() {
        val lines = catalog.lines(pet, "angry")
        say(lines.filter { it != speech }.ifEmpty { lines }.random(random), catalog.care.angerLineMs + 350)
        nextAngryLine = now() + catalog.care.angerLineMs
    }

    /** Enlarge near home, with short stomps and long reading pauses. Normal position stays intact. */
    fun tantrumPosition(width: Double, height: Double, petWidth: Double, petHeight: Double, originX: Double, originY: Double, captionHeight: Double = 40.0): TantrumPose {
        val origin = tantrumOrigin ?: (originX to originY).also { tantrumOrigin = it }
        val side = height < 240 && width >= 220
        val pad = 12.0; val bottom = 16.0
        val hopHeight = min(if (side) 8.0 else 18.0, height * 0.04)
        val top = max(min(104.0, height * 0.4), if (side) 0.0 else captionHeight + hopHeight + 36)
        val captionMin = min(160.0, max(104.0, width * 0.43))
        val availableW = if (side) width - captionMin - 12 - pad * 2 else width - pad * 2
        val availableH = if (side) height - 28 - bottom else height - top - bottom
        val scale = min(2.0, min(availableW / petWidth, availableH / petHeight)).coerceAtLeast(0.25)
        val w = petWidth * scale; val h = petHeight * scale
        val anchorX = if (side) pad else (origin.first + petWidth / 2 - w / 2).coerceIn(pad, max(pad, width - w - pad))
        val anchorY = if (side) height - h - bottom else (origin.second + petHeight - h).coerceIn(top, max(top, height - h - bottom))
        val age = max(0L, now() - angryAt) % catalog.care.hopMs
        val phase = if (!quiet && age < catalog.care.hopMoveMs) age.toDouble() / catalog.care.hopMoveMs else 0.0
        return TantrumPose(anchorX + (if (side) 2 else 4) * sin(PI * phase), anchorY - hopHeight * 4 * phase * (1 - phase),
            tantrumDir, phase, scale, anchorX, anchorY, side, if (side) width - anchorX - w - 24 else min(320.0, width - 24), hopHeight)
    }

    // ---- Motion -------------------------------------------------------------

    /** Advance by [dtMs] in an area [width] wide with [room] pixels to drift up and down in. */
    fun update(dtMs: Double, width: Double, spriteWidth: Double, room: Double) {
        val t = now()
        val elapsedMs = dtMs.coerceIn(0.0, 250.0)
        val dt = min(64.0, elapsedMs) / 16.7
        // Easing uses the full elapsed time even at the sleeping frame rate; travel still caps long stalls.
        val homeEase = 1 - 0.96.pow(elapsedMs / 16.7)
        val depthEase = 1 - 0.98.pow(elapsedMs / 16.7)
        val poseEase = 1 - 0.85.pow(elapsedMs / 16.7)
        settling = false
        if (active("angry") && food == null && t >= nextAngryLine) shout()
        if (meal > 0 && t - lastFed > catalog.care.mealGapMs) meal = 0
        fullness += (max(0, meal - catalog.care.safeFeeds) - fullness) * min(1.0, 0.12 * dt)
        if (burstAt?.let { t - it >= catalog.care.burstMs } == true) {
            meal = 0; fullness = 0.0; burstAt = null
            sayLine("burstRecovered")
        }
        if (!sleeping && !debugging && t - lastActivity > 3 * 60_000) { sleeping = true; sayLine("sleep", 2000) }
        if (sleeping) sessionMark = t // a break resets the long-session clock
        if (!sleeping && t - sessionMark > 90 * 60_000) { sessionMark = t; react("longSession") }
        if (!sleeping && food == null && t - lastFed > 60 * 60_000) react("hungry")
        maybeAntic(t)

        val f = flags()
        val excited = active("excited") && !sleeping
        val maxX = max(0.0, width - spriteWidth - 4)
        if (!previousWidth.isNaN() && (width != previousWidth || vertical != previousVertical) && !dragging) {
            fun resized(position: Double): Double = when {
                previousLimit <= 0 -> home * maxX
                roam -> position * maxX / previousLimit
                else -> position + home * (maxX - previousLimit)
            }.coerceIn(4.0, max(4.0, maxX))
            val before = x
            x = resized(x)
            goal = goal?.let(::resized)
            settling = abs(x - before) > 0.05
        }
        previousWidth = width; previousLimit = maxX; previousVertical = vertical
        val snack = food
        if (snack != null && !dragging) {
            // The snack sinks to the pet's mouth line; the pet swims over to it.
            val scale = artScale
            val gap: Double
            val reached: Boolean
            if (vertical) {
                // x is the snack's height here: it sinks, and the pet swims up or down to meet it.
                snack.x = min(snack.x + 0.9 * dt, maxX + pet.mouthY * scale * sizeY)
                gap = snack.x - (x + pet.mouthY * scale * sizeY)
                reached = kotlin.math.abs(gap) < 14
            } else {
                val mouthLocal = if (pet.flip && dir < 0) 120 - pet.mouthX else pet.mouthX
                val left = (if (pet.flip) min(pet.mouthX, 120 - pet.mouthX) else pet.mouthX) * scale * sizeX
                val right = (if (pet.flip) max(pet.mouthX, 120 - pet.mouthX) else pet.mouthX) * scale * sizeX
                snack.x = snack.x.coerceIn(4 + left, max(4.0, maxX) + right)
                val mouthY = spriteMouthTop + pet.mouthY * scale * sizeY
                snack.y = min(snack.y + 0.9 * dt, mouthY - 8)
                gap = snack.x - (x + mouthLocal * scale * sizeX)
                reached = kotlin.math.abs(gap) < 14 && snack.y >= mouthY - 20
            }
            if (reached) eat()
            else {
                if (kotlin.math.abs(gap) > 6) dir = if (gap > 0) 1 else -1
                speed += (2.0 * pet.speed - speed) * 0.1 * dt
                x += speed * dir * dt
            }
        } else if (dragging || bursting || active("angry") || (sleeping && roam)) {
            speed = 0.0
        } else if (dodging && roam) {
            // Swim clear of the caret, toward whichever side has more room.
            val center = x + spriteWidth / 2
            val clear = kotlin.math.abs(center - avoidX) > spriteWidth
            dir = if (avoidX > width / 2) -1 else 1
            speed += ((if (clear) 0.0 else 2.2) - speed) * 0.1 * dt
            x += speed * dir * dt
        } else if (!roam) {
            // Awake pets drift near home; sleepers rest at their anchor instead of chasing that drift.
            val target = (home * maxX + if (sleeping) 0.0 else 12 * kotlin.math.sin(t / 2600.0)).coerceIn(4.0, max(4.0, maxX))
            val step = (target - x) * homeEase
            if (kotlin.math.abs(step) > 0.05) dir = if (step > 0) 1 else -1
            x += step
            settling = settling || abs(target - x) > 0.05
        } else {
            var target = 0.4 * pet.speed
            if (sleeping || "hiding" in f || "curious" in f || active("spin")) target = 0.0
            else if (excited) target = 1.7 * pet.speed
            else if (debugging) target = 0.8 * pet.speed
            else if ("worried" in f) target = 0.22 * pet.speed
            // Head for a spot anywhere along the edge, rest there a moment, then pick another, so the pet
            // gets around the whole strip instead of pacing near where it started.
            val heading = goal
            if (heading == null || kotlin.math.abs(heading - x) < 8) {
                if (heading != null) restUntil = t + 800 + random.nextLong(2500)
                goal = 4 + random.nextDouble() * max(0.0, maxX - 4)
            }
            if (t < restUntil && !excited) target = 0.0
            else dir = if (goal!! > x) 1 else -1
            speed += (target - speed) * 0.06 * dt
            x += speed * dir * dt
        }
        if (x > maxX) { x = maxX; if (snack == null) dir = -1 }
        if (x < 4) { x = 4.0; if (snack == null) dir = 1 }

        if (t >= nextDepthAt) {
            depthTarget = if (sleeping || pet.floor) 0.0 else random.nextDouble() * room
            nextDepthAt = t + 4000
        }
        if (sleeping || pet.floor) depthTarget = 0.0
        depth += (depthTarget - depth) * depthEase
        settling = settling || abs(depthTarget - depth) > 0.05

        val tempo = when {
            "hiding" in f -> 0.0
            "angry" in f -> 0.8
            excited -> 3.5
            sleeping -> 0.25
            "worried" in f -> 0.65
            else -> 1.0
        }
        animClock += elapsedMs / 1000 * tempo

        // Ease every group toward its pose for the current mood.
        val moods = listOf("angry", "hiding", "sleeping", "worried", "curious").filter { it in f }
        val groups = pet.parts.map { it.group }.toSet()
        for (g in groups) {
            val p = moods.firstNotNullOfOrNull { pet.poses[it]?.get(g) } ?: Pose()
            val cur = poses.getOrPut(g) { doubleArrayOf(0.0, 0.0, 1.0, 0.0, p.px, p.py) }
            val target6 = doubleArrayOf(p.tx, p.ty, p.s, p.r)
            for (k in 0..3) {
                cur[k] += (target6[k] - cur[k]) * poseEase
                if (abs(target6[k] - cur[k]) > (if (k == 2) 0.002 else 0.05)) settling = true
            }
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
        meal++
        pokes = 0
        until["angry"] = 0
        if (meal >= catalog.care.burstAt) {
            burstAt = now()
            until["happy"] = 0; until["spin"] = 0
            bubbles.clear()
            sayLine("burstWarning", catalog.care.windupMs)
            return
        }
        flash("happy", 1100)
        blow(3)
        if (meal > catalog.care.safeFeeds) sayLine("overfed", 2200) else sayLine(snack.snack.key, 2200)
    }

    /** Switch to another pet in place, keeping position and mood. */
    fun become(next: Pet, newName: String) {
        if (next.id != pet.id) {
            meal = 0; fullness = 0.0; pokes = 0; lastPoke = Long.MIN_VALUE / 2
            burstAt = null; food = null; until["angry"] = 0
            angryAt = 0; nextAngryLine = 0
            speech = null; bubbles.clear()
        }
        pet = next
        name = newName
        poses.clear()
    }
}
