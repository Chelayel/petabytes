package com.chelayel.petabytes.pet

import java.awt.AlphaComposite
import java.awt.BasicStroke
import java.awt.Color
import java.awt.Font
import java.awt.Graphics2D
import java.awt.RenderingHints
import java.awt.geom.AffineTransform
import java.awt.geom.Ellipse2D
import java.awt.geom.RoundRectangle2D
import java.awt.geom.Rectangle2D
import kotlin.math.PI
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.max
import kotlin.math.ceil
import kotlin.random.Random

/** Colors and font for the speech bubble, taken from the IDE's look (or fixed, for previews). */
class BubbleStyle(val text: Color, val background: Color, val border: Color, val font: Font)

/** The angry face's vein red (tools/pets.py), reused for the angry bubble's outline and wash. */
private val ANGER = Color(0xE44954)

/**
 * Paints a [PetBrain]'s pet into an area: the pet sits [bottomInset] above the bottom edge
 * (plus its drift), at [scale] pixels per art unit, with its speech above it.
 */
class PetPainter(var scale: Double, private val bottomInset: Double = 4.0) {
    private var fade = 1f
    private var lastWidth = 0.0
    private var stretchX = 1.0
    private var stretchY = 1.0
    val spriteWidth get() = 120 * scale * stretchX
    val spriteHeight get() = 80 * scale * stretchY

    fun sync(brain: PetBrain) { stretchX = brain.sizeX; stretchY = brain.sizeY }

    /** Where the pet is drawn in an area [height] tall: x, y of the art box's top-left. */
    fun origin(brain: PetBrain, height: Double, width: Double = 0.0): Pair<Double, Double> =
        if (brain.vertical) (width - bottomInset - brain.depth - spriteWidth) to brain.x
        else brain.x to height - bottomInset - brain.depth - spriteHeight

    /** Facing left: always along the right edge (toward the code), else by swimming direction. */
    private fun facingLeft(brain: PetBrain) = brain.vertical || brain.dir < 0

    /** [fade] multiplies every opacity: 1 normally, low while the pet stays out of the way. */
    fun paint(g0: Graphics2D, brain: PetBrain, width: Double, height: Double, style: BubbleStyle, fade: Float = 1f) {
        val g = g0.create() as Graphics2D
        sync(brain)
        this.fade = fade
        lastWidth = width
        try {
            if (brain.splashed || brain.tantrum) return
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE)
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)
            val (ox, oy) = origin(brain, height, width)
            brain.spriteMouthTop = oy
            brain.artScale = scale
            paintFood(g, brain, style)
            paintPet(g, brain, ox, oy)
            paintBubbles(g, brain, ox, oy)
            paintZzz(g, brain, ox, oy, style)
            paintSpeech(g, brain, ox, oy, width, height, style)
        } finally {
            g.dispose()
        }
    }

    private fun paintPet(g: Graphics2D, brain: PetBrain, ox: Double, oy: Double, faceLeft: Boolean? = null, phase: Double? = null, magnification: Double = 1.0) {
        val pet = brain.pet
        val flags = brain.flags()
        val now = brain.now()
        val t = brain.animClock

        // The whole pet: bob, happy loop, spin, facing.
        var ty = if (phase == null) pet.bobAmount * sin(2 * PI * (now / 1000.0) / (pet.bobPeriod * if (brain.sleeping) 2 else 1)) else 0.0
        var rot = 0.0
        if ("happy" in flags) {
            val p = min(1.0, (now - brain.happyAt) / 1100.0)
            ty -= 18 * sin(PI * p); rot += -12 * sin(2 * PI * p)
        }
        if (brain.active("spin") && "angry" !in flags && !brain.bursting) rot += 360 * min(1.0, (now - brain.spinAt) / 800.0)
        if (brain.bursting) rot += 4 * sin((now - brain.burstAt!!) / 24.0)
        if (phase != null) rot += 2 * sin(phase * PI * 2)
        val squash = if (phase != null) sin(PI * phase) * 0.025 else 0.0
        val base = AffineTransform()
        base.translate(ox, oy)
        base.scale(scale * stretchX * magnification, scale * stretchY * magnification)
        base.translate(0.0, ty)
        base.rotate(Math.toRadians(rot), 60.0, 40.0)
        base.translate(60.0, 40.0); base.scale(1 - squash, 1 + squash); base.translate(-60.0, -40.0)
        if (pet.flip && (faceLeft ?: facingLeft(brain))) { base.translate(120.0, 0.0); base.scale(-1.0, 1.0) }

        for (part in pet.parts) {
            val show = part.whenFlags == null || part.whenFlags.any { it in flags }
            if (!show) continue
            val at = AffineTransform(base)
            brain.poses[part.group]?.let { p ->
                at.translate(p[4], p[5]); at.translate(p[0], p[1]); at.rotate(Math.toRadians(p[3])); at.scale(p[2], p[2]); at.translate(-p[4], -p[5])
            }
            pet.groupMotion[part.group]?.let { m ->
                val sx = 1 + (m.sx?.at(t) ?: 0.0)
                val sy = 1 + (m.sy?.at(t) ?: 0.0)
                at.translate(m.px, m.py); at.scale(sx, sy); at.translate(-m.px, -m.py)
            }
            part.rot?.let { at.rotate(Math.toRadians(it.at(t)), part.pivotX, part.pivotY) }
            val shape = at.createTransformedShape(part.shape)
            val alpha = AlphaComposite.getInstance(AlphaComposite.SRC_OVER, part.opacity * fade)
            g.composite = alpha
            part.fill?.let { g.color = it; g.fill(shape) }
            part.stroke?.let {
                g.color = it
                // Stroke width scales with the art, like SVG's.
                g.stroke = BasicStroke((part.strokeWidth * scale * magnification).toFloat(), BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)
                g.draw(shape)
            }
        }
        g.composite = AlphaComposite.SrcOver
    }

    fun paintTantrum(g0: Graphics2D, brain: PetBrain, width: Double, height: Double, style: BubbleStyle, originX: Double, originY: Double) {
        if (!brain.tantrum) return
        val g = g0.create() as Graphics2D
        try {
            sync(brain); fade = 1f
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)
            g.font = angryFont(style)
            val captionHeight = speechLines(g, brain.speech.orEmpty(), min(320.0, width - 24) - 24).size * g.fontMetrics.height + 12.0
            val position = brain.tantrumPosition(width, height, spriteWidth, spriteHeight, originX, originY, captionHeight)
            paintPet(g, brain, position.x, position.y, position.dir < 0, position.phase, position.scale)
            paintSpeech(g, brain, position.anchorX, position.anchorY, width, height, style, position)
        } finally { g.dispose() }
    }

    /** Paints above the whole IDE window in a separate, click-through component. */
    fun paintMess(g0: Graphics2D, brain: PetBrain, width: Double, height: Double) {
        if (!brain.splashed || width <= 0 || height <= 0) return
        val g = g0.create() as Graphics2D
        try {
            val progress = brain.messAge.toDouble() / brain.messDuration
            val alpha = if (progress < 0.78) 1.0 else ((1 - progress) / 0.22).coerceIn(0.0, 1.0)
            val art = brain.pet.splatter
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, if (art.pixel) RenderingHints.VALUE_ANTIALIAS_OFF else RenderingHints.VALUE_ANTIALIAS_ON)
            g.composite = AlphaComposite.getInstance(AlphaComposite.SRC_OVER, (alpha * 0.82).toFloat())
            g.color = art.fill
            g.fill(Rectangle2D.Double(0.0, 0.0, width, height))
            g.composite = AlphaComposite.getInstance(AlphaComposite.SRC_OVER, alpha.toFloat())
            val cols = ceil(width / height * 4).toInt().coerceIn(3, 9)
            val cellW = width / cols; val cellH = height / 4
            val random = Random(brain.pet.id.hashCode())
            for (row in 0..4) for (col in 0..cols) {
                val blob = g.create() as Graphics2D
                try {
                    blob.translate((col + (random.nextDouble() - 0.5) * 0.35) * cellW, (row + (random.nextDouble() - 0.5) * 0.35) * cellH)
                    val scale = max(cellW, cellH) / 76
                    blob.scale(scale, scale)
                    if (!art.pixel) blob.rotate(Math.toRadians(random.nextDouble() * 80 - 40))
                    blob.translate(-50.0, -50.0)
                    blob.color = if ((row + col) % 3 == 0) art.shade else art.fill
                    blob.fill(art.shape)
                    blob.color = withAlpha(art.outline, 0.45)
                    blob.stroke = BasicStroke(1.5f)
                    blob.draw(art.shape)
                    blob.color = art.shine
                    for ((x, y, r) in listOf(Triple(36.0, 35.0, 8.0), Triple(60.0, 48.0, 4.0), Triple(31.0, 58.0, 3.0))) {
                        blob.fill(if (art.pixel) Rectangle2D.Double(x, y, r, r) else Ellipse2D.Double(x - r, y - r * 0.65, r * 2, r * 1.3))
                    }
                } finally { blob.dispose() }
            }
        } finally { g.dispose() }
    }

    private fun paintBubbles(g: Graphics2D, brain: PetBrain, ox: Double, oy: Double) {
        val pet = brain.pet
        val now = brain.now()
        val mouthX = if (pet.flip && facingLeft(brain)) 120 - pet.mouthX else pet.mouthX
        g.stroke = BasicStroke(1.5f)
        val headX = if (pet.flip && facingLeft(brain)) 120 - pet.headX else pet.headX
        for (b in brain.bubbles) {
            val age = (now - b.born) / 1800.0
            if (age < 0) continue
            val p = 1 - (1 - age) * (1 - age) // ease-out
            val alpha = (0.85 * (1 - age) * fade).coerceIn(0.0, 1.0)
            if (b.heart) {
                val x = ox + headX * scale * stretchX + b.x + b.dx * p
                val y = oy + pet.headY * scale * stretchY - 50 * p
                g.color = withAlpha(Color(0xF472B6), alpha)
                g.fill(heart(x, y, 9.0))
                continue
            }
            val x = ox + mouthX * scale * stretchX + b.x + b.dx * p
            val y = oy + pet.mouthY * scale * stretchY - 6 - 70 * p
            g.color = withAlpha(pet.accent, alpha)
            g.draw(Ellipse2D.Double(x - b.size / 2, y - b.size / 2, b.size, b.size))
        }
    }

    private fun heart(cx: Double, cy: Double, size: Double): java.awt.Shape {
        val s = size / 2
        return java.awt.geom.Path2D.Double().apply {
            moveTo(cx, cy + s)
            curveTo(cx - 2.2 * s, cy - 0.2 * s, cx - 1.0 * s, cy - 1.7 * s, cx, cy - 0.6 * s)
            curveTo(cx + 1.0 * s, cy - 1.7 * s, cx + 2.2 * s, cy - 0.2 * s, cx, cy + s)
            closePath()
        }
    }

    private fun paintFood(g: Graphics2D, brain: PetBrain, style: BubbleStyle) {
        val food = brain.food ?: return
        g.font = Font(Font.MONOSPACED, Font.BOLD, (style.font.size2D + 1).toInt())
        g.color = withAlpha(brain.pet.accent, fade.toDouble())
        val w = g.fontMetrics.stringWidth(food.snack.text)
        if (brain.vertical) {
            // Sinking down the pet's column, in front of its mouth.
            val pet = brain.pet
            val (ox, _) = origin(brain, 0.0, lastWidth)
            val mouthX = ox + (if (pet.flip) 120 - pet.mouthX else pet.mouthX) * scale * stretchX
            g.drawString(food.snack.text, (mouthX - w / 2).toFloat(), (food.x).toFloat())
        } else {
            g.drawString(food.snack.text, (food.x - w / 2).toFloat(), (food.y + g.fontMetrics.ascent).toFloat())
        }
    }

    private fun paintZzz(g: Graphics2D, brain: PetBrain, ox: Double, oy: Double, style: BubbleStyle) {
        if (!brain.sleeping) return
        val pet = brain.pet
        val p = (brain.now() % 2600) / 2600.0
        val headX = if (pet.flip && facingLeft(brain)) 120 - pet.headX else pet.headX
        g.font = style.font.deriveFont(Font.BOLD, (style.font.size2D * (0.9f + 0.4f * p.toFloat())))
        g.color = withAlpha(pet.accent, if (p < 0.3) p / 0.3 else 1 - (p - 0.3) / 0.7)
        g.drawString("z", (ox + headX * scale + 10 * p).toFloat(), (oy + pet.headY * scale - 22 * p).toFloat())
    }

    private fun angryFont(style: BubbleStyle) = style.font.deriveFont(Font.BOLD, max(13f, style.font.size2D + 1))

    /** The normal bubble with a wash of the angry face's vein red, so the shout stays in the IDE's own palette. */
    private fun angryBackground(base: Color) = Color(
        (base.red * 0.86 + ANGER.red * 0.14).toInt(), (base.green * 0.86 + ANGER.green * 0.14).toInt(),
        (base.blue * 0.86 + ANGER.blue * 0.14).toInt(), base.alpha)

    private fun speechLines(g: Graphics2D, text: String, wrapWidth: Double): List<String> {
        val lines = ArrayList<String>()
        var line = ""
        for (word in text.split(' ')) {
            val next = if (line.isEmpty()) word else "$line $word"
            if (line.isNotEmpty() && g.fontMetrics.stringWidth(next) > wrapWidth) { lines.add(line); line = "" }
            // A long word still needs to fit when the panel is very narrow.
            for (char in (if (line.isEmpty()) word else " $word")) {
                if (line.isNotEmpty() && g.fontMetrics.stringWidth(line + char) > wrapWidth) { lines.add(line); line = "" }
                line += char
            }
        }
        if (line.isNotEmpty()) lines.add(line)
        return lines
    }

    private fun paintSpeech(g: Graphics2D, brain: PetBrain, ox: Double, oy: Double, width: Double, height: Double, style: BubbleStyle, stage: PetBrain.TantrumPose? = null) {
        val text = brain.speech ?: return
        val left = brain.speechUntil - brain.now()
        if (left <= 0) return
        val alpha = min(1.0, left / 250.0)
        val angry = brain.active("angry")
        g.font = if (angry) angryFont(style) else style.font
        val fm = g.fontMetrics
        val wrapWidth = (stage?.captionWidth ?: min(320.0, width - 24)) - 24
        val lines = if (angry) speechLines(g, text, wrapWidth) else listOf(text)
        val w = stage?.captionWidth ?: ((lines.maxOfOrNull { fm.stringWidth(it) } ?: 0) + 20.0)
        val h = fm.height * lines.size + 12.0
        // Along the right edge the bubble opens to the pet's left; otherwise above it.
        val edge = brain.vertical && !brain.tantrum
        val captionX = if (stage != null) {
            if (stage.side) ox + spriteWidth * stage.scale + 12 else ox + spriteWidth * stage.scale / 2 - w / 2
        } else if (edge) ox - w - 2 else ox
        val captionY = if (stage != null) {
            if (stage.side) oy + (spriteHeight * stage.scale - h) / 2 else oy - h - stage.hopHeight - 28
        } else if (edge) oy + spriteHeight * 0.15 else if (oy - h - 8 >= 4) oy - h - 8 else oy + spriteHeight + 4
        val x = captionX.coerceIn(4.0, max(4.0, width - w - 4))
        val y = captionY.coerceIn(4.0, max(4.0, height - h - 4))
        val box = RoundRectangle2D.Double(x, y, w, h, 14.0, 14.0)
        g.color = withAlpha(if (angry) angryBackground(style.background) else style.background, alpha * style.background.alpha / 255.0)
        g.fill(box)
        g.stroke = BasicStroke(1f)
        g.color = withAlpha(if (angry) ANGER else style.border, alpha)
        g.draw(box)
        g.color = withAlpha(style.text, alpha)
        lines.forEachIndexed { i, value ->
            val tx = if (stage != null) x + (w - fm.stringWidth(value)) / 2 else x + 10
            g.drawString(value, tx.toFloat(), (y + 6 + fm.ascent + i * fm.height).toFloat())
        }
    }

    private fun withAlpha(c: Color, a: Double) = Color(c.red, c.green, c.blue, (a.coerceIn(0.0, 1.0) * 255).toInt())
}
