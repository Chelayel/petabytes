package com.chelayel.petabytes.pet

import java.awt.Color
import java.awt.Font
import java.awt.image.BufferedImage
import java.io.File
import javax.imageio.ImageIO
import kotlin.random.Random

/**
 * Renders every pet in each mood with the IntelliJ painter, headlessly, so the native
 * drawing can be checked against the VS Code page: `./gradlew renderPreview`.
 */
fun main(args: Array<String>) {
    val catalog = PetCatalog.parse(File(args[0]).readText())
    val out = File(args[1]).apply { mkdirs() }
    val moods = listOf("calm", "happy", "worried", "hiding", "debugging", "sleeping")
    val cellW = 220; val cellH = 120; val scale = 1.2
    val style = BubbleStyle(Color(0xE4E4E7), Color(0x1F2226), Color(0x2A2E33), Font("SansSerif", Font.PLAIN, 12))
    val sheet = BufferedImage(cellW * moods.size * 2, cellH * catalog.pets.size * 2, BufferedImage.TYPE_INT_ARGB)
    val sg = sheet.createGraphics()
    sg.scale(2.0, 2.0)
    sg.color = Color(0x151719); sg.fillRect(0, 0, cellW * moods.size, cellH * catalog.pets.size)
    catalog.pets.values.forEachIndexed { row, pet ->
        moods.forEachIndexed { col, mood ->
            var t = 10_000_000L
            val brain = PetBrain(catalog, pet, pet.name, clock = { t }, random = Random(7))
            brain.update(16.7, cellW.toDouble(), 120 * scale, 0.0)
            when (mood) {
                "happy" -> brain.errorsChanged(2).also { t += 3200; brain.errorsChanged(0) }
                "worried" -> brain.errorsChanged(1)
                "hiding" -> brain.taskFinished(false, "npm test")
                "debugging" -> brain.debug(true)
                "sleeping" -> { t += 4 * 60_000 }
            }
            // Let poses settle, but stop mid-reaction for the happy loop.
            val frames = if (mood == "happy") 25 else 60
            repeat(frames) { t += 17; brain.update(16.7, cellW.toDouble(), 120 * scale, 0.0) }
            val g = sg.create(col * cellW, row * cellH, cellW, cellH) as java.awt.Graphics2D
            PetPainter(scale, bottomInset = 6.0).paint(g, brain, cellW.toDouble(), cellH.toDouble(), style)
            g.color = Color(0x71717A); g.font = Font("SansSerif", Font.PLAIN, 10)
            g.drawString("${pet.name} · $mood", 6, cellH - 4)
            g.dispose()
        }
    }
    sg.dispose()
    ImageIO.write(sheet, "png", File(out, "preview.png"))
    println(File(out, "preview.png").absolutePath)
}
