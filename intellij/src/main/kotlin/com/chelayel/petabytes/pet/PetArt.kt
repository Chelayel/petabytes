package com.chelayel.petabytes.pet

import java.awt.Color
import java.awt.Shape
import java.awt.geom.Ellipse2D
import java.awt.geom.Path2D
import kotlin.math.PI
import kotlin.math.sin

/**
 * The pets as web/pets.json describes them (the same file the VS Code page draws):
 * shapes in a 120x80 box facing right, grouped so each mood can pose a group, with
 * some parts and groups oscillating. Pure AWT, so previews can render headlessly.
 */
class Wave(private val amount: Double, private val period: Double, private val phase: Double) {
    fun at(t: Double) = amount * sin(2 * PI * (t / period + phase))
}

data class Pose(val tx: Double = 0.0, val ty: Double = 0.0, val s: Double = 1.0, val r: Double = 0.0, val px: Double = 60.0, val py: Double = 40.0)

class GroupMotion(val sx: Wave?, val sy: Wave?, val px: Double, val py: Double)

class Part(
    val group: String,
    val shape: Shape,
    val fill: Color?,
    val stroke: Color?,
    val strokeWidth: Float,
    val opacity: Float,
    val pivotX: Double,
    val pivotY: Double,
    val rot: Wave?,
    val whenFlags: List<String>?,
)

class Pet(
    val id: String,
    val label: String,
    val name: String,
    val flip: Boolean,
    val floor: Boolean,
    val speed: Double,
    val bobAmount: Double,
    val bobPeriod: Double,
    val accent: Color,
    val mouthX: Double,
    val mouthY: Double,
    val headX: Double,
    val headY: Double,
    val parts: List<Part>,
    /** mood → group → pose */
    val poses: Map<String, Map<String, Pose>>,
    val groupMotion: Map<String, GroupMotion>,
    val lines: Map<String, List<String>>,
    /** tide, home, snacks, games or gadgets: the tab it's under in Choose a Pet. */
    val set: String = "tide",
)

/** What an IDE event (by key) makes the pet do; see REACTIONS in tools/pets.py. */
class Reaction(val mood: String?, val ms: Long, val bubbles: Int, val hearts: Int, val chance: Double, val cooldownMs: Long)

class Snack(val text: String, val key: String)

class PetCatalog(
    val pets: Map<String, Pet>,
    private val lines: Map<String, List<String>>,
    val reactions: Map<String, Reaction> = emptyMap(),
    val snacks: List<Snack> = listOf(Snack("{ }", "eatCurly")),
    /** Reaction keys the pet picks from to do something on its own now and then, and how often (seconds). */
    val antics: List<String> = emptyList(),
    val anticEvery: Pair<Double, Double> = 70.0 to 160.0,
) {
    fun pet(id: String?): Pet = pets[id] ?: pets.getValue("turtle")
    fun lines(pet: Pet, key: String): List<String> = pet.lines[key] ?: lines[key] ?: listOf("")

    companion object {
        fun load(): PetCatalog {
            val text = PetCatalog::class.java.getResourceAsStream("/pet/pets.json")?.bufferedReader()?.readText()
                ?: error("pets.json is missing from the plugin")
            return parse(text)
        }

        @Suppress("UNCHECKED_CAST")
        fun parse(text: String): PetCatalog {
            val root = Json(text).parse() as Map<String, Any?>
            val pets = (root["pets"] as Map<String, Any?>).mapValues { (id, raw) -> pet(id, raw as Map<String, Any?>) }
            val reactions = (root["reactions"] as Map<String, Any?>? ?: emptyMap()).mapValues { (_, r) ->
                r as Map<String, Any?>
                Reaction(
                    r["mood"] as String?, ((r["ms"] as Double?) ?: 1200.0).toLong(), ((r["bubbles"] as Double?) ?: 0.0).toInt(),
                    ((r["hearts"] as Double?) ?: 0.0).toInt(), (r["chance"] as Double?) ?: 1.0, (((r["cooldown"] as Double?) ?: 0.0) * 1000).toLong(),
                )
            }
            val snacks = (root["snacks"] as List<Map<String, Any?>>? ?: emptyList()).map { Snack(it["text"] as String, it["key"] as String) }
            val antics = (root["antics"] as List<String>?) ?: emptyList()
            val every = (root["anticEvery"] as List<Double>?)?.takeIf { it.size == 2 }?.let { it[0] to it[1] } ?: (70.0 to 160.0)
            return PetCatalog(pets, stringLists(root["lines"]), reactions, snacks.ifEmpty { listOf(Snack("{ }", "eatCurly")) }, antics, every)
        }

        @Suppress("UNCHECKED_CAST")
        private fun pet(id: String, m: Map<String, Any?>): Pet {
            val parts = (m["parts"] as List<Map<String, Any?>>).map(::part)
            val poses = (m["poses"] as Map<String, Any?>? ?: emptyMap()).mapValues { (_, groups) ->
                (groups as Map<String, Any?>).mapValues { (_, p) -> pose(p as Map<String, Any?>) }
            }
            val motion = (m["groupMotion"] as Map<String, Any?>? ?: emptyMap()).mapValues { (_, g) ->
                g as Map<String, Any?>
                val p = nums(g["p"]) ?: listOf(60.0, 40.0)
                GroupMotion(wave(g["sx"]), wave(g["sy"]), p[0], p[1])
            }
            val bob = nums(m["bob"]) ?: listOf(4.0, 3.0)
            val mouth = nums(m["mouth"]) ?: listOf(100.0, 40.0)
            val head = nums(m["head"]) ?: listOf(100.0, 20.0)
            // Bubbles and the sleep "z" take the pet's first outline color, as on the web page.
            val accent = parts.firstNotNullOfOrNull { it.stroke } ?: Color(0x5EEAD4)
            return Pet(
                id, m["label"] as String, m["name"] as String, m["flip"] as Boolean, m["floor"] as Boolean,
                (m["speed"] as Double), bob[0], bob[1], accent, mouth[0], mouth[1], head[0], head[1],
                parts, poses, motion, stringLists(m["lines"]), (m["set"] as String?) ?: "tide",
            )
        }

        @Suppress("UNCHECKED_CAST")
        private fun part(m: Map<String, Any?>): Part {
            val shape: Shape = when {
                m["path"] != null -> SvgPath.parse(m["path"] as String)
                m["circle"] != null -> nums(m["circle"])!!.let { (cx, cy, r) -> Ellipse2D.Double(cx - r, cy - r, 2 * r, 2 * r) }
                else -> nums(m["ellipse"])!!.let { (cx, cy, rx, ry) -> Ellipse2D.Double(cx - rx, cy - ry, 2 * rx, 2 * ry) }
            }
            val pivot = nums(m["pivot"]) ?: listOf(60.0, 40.0)
            return Part(
                group = m["group"] as String,
                shape = shape,
                fill = (m["fill"] as String?)?.let(::color),
                stroke = (m["stroke"] as String?)?.let(::color),
                strokeWidth = ((m["sw"] as Double?) ?: 1.0).toFloat(),
                opacity = ((m["opacity"] as Double?) ?: 1.0).toFloat(),
                pivotX = pivot[0], pivotY = pivot[1],
                rot = wave(m["rot"]),
                whenFlags = (m["when"] as List<String>?),
            )
        }

        private fun pose(m: Map<String, Any?>): Pose {
            val p = nums(m["p"]) ?: listOf(60.0, 40.0)
            return Pose(
                (m["tx"] as Double?) ?: 0.0, (m["ty"] as Double?) ?: 0.0,
                (m["s"] as Double?) ?: 1.0, (m["r"] as Double?) ?: 0.0, p[0], p[1],
            )
        }

        private fun wave(v: Any?) = nums(v)?.let { Wave(it[0], it[1], it.getOrElse(2) { 0.0 }) }

        @Suppress("UNCHECKED_CAST")
        private fun nums(v: Any?): List<Double>? = (v as List<Any?>?)?.map { (it as Number).toDouble() }

        @Suppress("UNCHECKED_CAST")
        private fun stringLists(v: Any?): Map<String, List<String>> =
            (v as Map<String, Any?>? ?: emptyMap()).mapValues { (_, l) -> l as List<String> }

        /** "#RRGGBB" or "rgba(r,g,b,a)". */
        fun color(s: String): Color {
            if (s.startsWith("#")) return Color(s.substring(1).toInt(16))
            val (r, g, b, a) = s.substringAfter("(").substringBefore(")").split(",").map { it.trim().toDouble() }
            return Color(r.toInt(), g.toInt(), b.toInt(), (a * 255).toInt())
        }
    }
}

/** The subset of SVG path syntax the art uses: M L H V Q C Z, absolute and relative. */
object SvgPath {
    fun parse(d: String): Path2D.Double {
        val tokens = Regex("[MmLlHhVvQqCcZz]|-?(?:\\d+\\.?\\d*|\\.\\d+)(?:[eE][-+]?\\d+)?").findAll(d).map { it.value }.toList()
        val path = Path2D.Double()
        var i = 0
        var cmd = 'M'
        var x = 0.0; var y = 0.0; var sx = 0.0; var sy = 0.0
        fun num() = tokens[i++].toDouble()
        while (i < tokens.size) {
            if (tokens[i][0].isLetter()) cmd = tokens[i++][0]
            val rel = cmd.isLowerCase()
            val ox = if (rel) x else 0.0
            val oy = if (rel) y else 0.0
            when (cmd.uppercaseChar()) {
                'M' -> { x = ox + num(); y = oy + num(); path.moveTo(x, y); sx = x; sy = y; cmd = if (rel) 'l' else 'L' }
                'L' -> { x = ox + num(); y = oy + num(); path.lineTo(x, y) }
                'H' -> { x = ox + num(); path.lineTo(x, y) }
                'V' -> { y = oy + num(); path.lineTo(x, y) }
                'Q' -> { val cx = ox + num(); val cy = oy + num(); x = ox + num(); y = oy + num(); path.quadTo(cx, cy, x, y) }
                'C' -> {
                    val c1x = ox + num(); val c1y = oy + num(); val c2x = ox + num(); val c2y = oy + num()
                    x = ox + num(); y = oy + num(); path.curveTo(c1x, c1y, c2x, c2y, x, y)
                }
                'Z' -> { path.closePath(); x = sx; y = sy }
                else -> error("Unsupported path command $cmd")
            }
        }
        return path
    }
}

/** Just enough JSON for pets.json: objects, arrays, strings, numbers (as Double), booleans, null. */
class Json(private val s: String) {
    private var i = 0

    fun parse(): Any? = value().also { ws(); check(i == s.length) { "Trailing content at $i" } }

    private fun ws() { while (i < s.length && s[i].isWhitespace()) i++ }

    private fun value(): Any? {
        ws()
        return when (val c = s[i]) {
            '{' -> obj()
            '[' -> arr()
            '"' -> str()
            't' -> { expect("true"); true }
            'f' -> { expect("false"); false }
            'n' -> { expect("null"); null }
            else -> if (c == '-' || c.isDigit()) num() else error("Unexpected '$c' at $i")
        }
    }

    private fun expect(word: String) { check(s.startsWith(word, i)) { "Expected $word at $i" }; i += word.length }

    private fun obj(): Map<String, Any?> {
        val out = LinkedHashMap<String, Any?>()
        i++; ws()
        if (s[i] == '}') { i++; return out }
        while (true) {
            ws(); val k = str(); ws(); check(s[i++] == ':') { "Expected ':' at ${i - 1}" }
            out[k] = value(); ws()
            when (s[i++]) { ',' -> continue; '}' -> return out; else -> error("Expected ',' or '}' at ${i - 1}") }
        }
    }

    private fun arr(): List<Any?> {
        val out = ArrayList<Any?>()
        i++; ws()
        if (s[i] == ']') { i++; return out }
        while (true) {
            out.add(value()); ws()
            when (s[i++]) { ',' -> continue; ']' -> return out; else -> error("Expected ',' or ']' at ${i - 1}") }
        }
    }

    private fun str(): String {
        check(s[i++] == '"') { "Expected string at ${i - 1}" }
        val b = StringBuilder()
        while (true) {
            val c = s[i++]
            when (c) {
                '"' -> return b.toString()
                '\\' -> when (val e = s[i++]) {
                    'n' -> b.append('\n'); 't' -> b.append('\t'); 'r' -> b.append('\r'); 'b' -> b.append('\b'); 'f' -> b.append('\u000C')
                    'u' -> { b.append(s.substring(i, i + 4).toInt(16).toChar()); i += 4 }
                    else -> b.append(e)
                }
                else -> b.append(c)
            }
        }
    }

    private fun num(): Double {
        val start = i
        while (i < s.length && (s[i].isDigit() || s[i] in "-+.eE")) i++
        return s.substring(start, i).toDouble()
    }
}
