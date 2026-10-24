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
import kotlin.math.PI
import kotlin.math.min
import kotlin.math.sin

/** Colors and font for the speech bubble, taken from the IDE's look (or fixed, for previews). */
class BubbleStyle(val text: Color, val background: Color, val border: Color, val font: Font)

/**
 * Paints a [PetBrain]'s pet into an area: the pet sits [bottomInset] above the bottom edge
 * (plus its drift), at [scale] pixels per art unit, with its speech above it.
 */
class PetPainter(var scale: Double, private val bottomInset: Double = 4.0) {
    private var fade = 1f
    private var lastWidth = 0.0
    val spriteWidth get() = 120 * scale
    val spriteHeight get() = 80 * scale

    /** Where the pet is drawn in an area [height] tall: x, y of the art box's top-left. */
    fun origin(brain: PetBrain, height: Double, width: Double = 0.0): Pair<Double, Double> =
        if (brain.vertical) (width - bottomInset - brain.depth - spriteWidth) to brain.x
        else brain.x to height - bottomInset - brain.depth - spriteHeight

    /** Facing left: always along the right edge (toward the code), else by swimming direction. */
    private fun facingLeft(brain: PetBrain) = brain.vertical || brain.dir < 0

    /** [fade] multiplies every opacity: 1 normally, low while the pet stays out of the way. */
    fun paint(g0: Graphics2D, brain: PetBrain, width: Double, height: Double, style: BubbleStyle, fade: Float = 1f) {
        val g = g0.create() as Graphics2D
        this.fade = fade
        lastWidth = width
        try {
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
            paintSpeech(g, brain, ox, oy, width, style)
        } finally {
            g.dispose()
        }
    }

    private fun paintPet(g: Graphics2D, brain: PetBrain, ox: Double, oy: Double) {
        val pet = brain.pet
        val flags = brain.flags()
        val now = brain.now()
        val t = brain.animClock

        // The whole pet: bob, happy loop, spin, facing.
        var ty = pet.bobAmount * sin(2 * PI * (now / 1000.0) / (pet.bobPeriod * if (brain.sleeping) 2 else 1))
        var rot = 0.0
        if ("happy" in flags) {
            val p = min(1.0, (now - brain.happyAt) / 1100.0)
            ty -= 18 * sin(PI * p); rot += -12 * sin(2 * PI * p)
        }
        if (brain.active("spin")) rot += 360 * min(1.0, (now - brain.spinAt) / 800.0)
        val base = AffineTransform()
        base.translate(ox, oy)
        base.scale(scale, scale)
        base.translate(0.0, ty)
        base.rotate(Math.toRadians(rot), 60.0, 40.0)
        if (pet.flip && facingLeft(brain)) { base.translate(120.0, 0.0); base.scale(-1.0, 1.0) }

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
                g.stroke = BasicStroke((part.strokeWidth * scale).toFloat(), BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)
                g.draw(shape)
            }
        }
        g.composite = AlphaComposite.SrcOver
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
                val x = ox + headX * scale + b.x + b.dx * p
                val y = oy + pet.headY * scale - 50 * p
                g.color = withAlpha(Color(0xF472B6), alpha)
                g.fill(heart(x, y, 9.0))
                continue
            }
            val x = ox + mouthX * scale + b.x + b.dx * p
            val y = oy + pet.mouthY * scale - 6 - 70 * p
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
            val mouthX = ox + (if (pet.flip) 120 - pet.mouthX else pet.mouthX) * scale
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

    private fun paintSpeech(g: Graphics2D, brain: PetBrain, ox: Double, oy: Double, width: Double, style: BubbleStyle) {
        val text = brain.speech ?: return
        val left = brain.speechUntil - brain.now()
        if (left <= 0) return
        val alpha = min(1.0, left / 250.0)
        g.font = style.font
        val fm = g.fontMetrics
        val w = fm.stringWidth(text) + 16.0
        val h = fm.height + 8.0
        // Along the right edge the bubble opens to the pet's left; otherwise above it.
        val x = if (brain.vertical) (ox - w - 2).coerceAtLeast(2.0) else ox.coerceIn(4.0, (width - w - 4).coerceAtLeast(4.0))
        val y = if (brain.vertical) oy + spriteHeight * 0.15 else (oy - h - 2).coerceAtLeast(2.0)
        val box = RoundRectangle2D.Double(x, y, w, h, 14.0, 14.0)
        g.color = withAlpha(style.background, alpha * style.background.alpha / 255.0)
        g.fill(box)
        g.stroke = BasicStroke(1f)
        g.color = withAlpha(style.border, alpha)
        g.draw(box)
        g.color = withAlpha(style.text, alpha)
        g.drawString(text, (x + 8).toFloat(), (y + 4 + fm.ascent).toFloat())
    }

    private fun withAlpha(c: Color, a: Double) = Color(c.red, c.green, c.blue, (a.coerceIn(0.0, 1.0) * 255).toInt())
}
