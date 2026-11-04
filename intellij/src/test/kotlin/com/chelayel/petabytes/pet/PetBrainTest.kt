package com.chelayel.petabytes.pet

import java.io.File
import kotlin.random.Random
import kotlin.test.*
import org.junit.Test

class PetBrainTest {
    private val catalog = PetCatalog.parse(File("../web/pets.json").readText())
    private var time = 10_000_000L

    private fun brain(id: String = "turtle", vertical: Boolean = false) = PetBrain(
        catalog, catalog.pet(id), catalog.pet(id).name, clock = { time }, random = Random(7),
    ).apply { this.vertical = vertical; artScale = 0.8 }

    private fun step(brain: PetBrain, ms: Long = 17) {
        time += ms
        brain.update(ms.toDouble(), 600.0, (if (brain.vertical) 80 * brain.sizeY else 120 * brain.sizeX) * brain.artScale, 0.0)
    }

    private fun snack(brain: PetBrain) {
        brain.feed(600.0)
        val food = assertNotNull(brain.food)
        if (brain.vertical) food.x = brain.x + brain.pet.mouthY * brain.artScale * brain.sizeY
        else {
            val mouth = if (brain.pet.flip && brain.dir < 0) 120 - brain.pet.mouthX else brain.pet.mouthX
            food.x = brain.x + mouth * brain.artScale * brain.sizeX
            food.y = brain.spriteMouthTop + brain.pet.mouthY * brain.artScale * brain.sizeY - 8
        }
        brain.update(0.0, 600.0, 120 * brain.artScale, 0.0)
        assertNull(brain.food, "The snack should reach ${brain.pet.id}'s mouth")
        repeat(35) { step(brain) }
    }

    @Test fun allPetsGrowBurstAndRecoverOnBothEdges() {
        for (vertical in listOf(false, true)) for (id in catalog.pets.keys) {
            val pet = brain(id, vertical)
            repeat(3) { snack(pet) }
            assertEquals(0.0, pet.fullness, "$id should not grow for three snacks")
            var size = 0.0
            repeat(4) {
                snack(pet)
                assertTrue(pet.fullness > size, "$id should grow for every extra snack")
                size = pet.fullness
            }
            snack(pet)
            assertTrue(pet.bursting)
            assertTrue(pet.splashed)
            pet.feed(600.0)
            pet.clicked()
            assertNull(pet.food)
            step(pet, catalog.care.burstMs)
            assertFalse(pet.bursting)
            assertEquals(0, pet.meal)
            assertEquals(0.0, pet.fullness)
            snack(pet)
            assertEquals(1, pet.meal)
        }
    }

    @Test fun enlargedPetsCanReachSnacksAtTheEdge() {
        for (id in catalog.pets.keys) {
            val pet = brain(id)
            repeat(7) { snack(pet) }
            pet.feed(600.0)
            assertNotNull(pet.food).apply { x = 0.0; y = 0.0 }
            var frames = 0
            while (pet.food != null && frames++ < 3000) step(pet)
            assertNull(pet.food, "$id must reach an edge snack after growing")
            assertTrue(pet.bursting, "$id should burst on eating snack eight")
        }
    }

    @Test fun tantrumsStayReadableNearHomeWithLongPauses() {
        for (id in catalog.pets.keys) {
            val pet = brain(id)
            repeat(5) { pet.clicked() }
            assertTrue(pet.tantrum)
            assertFalse("eyesOpen" in pet.flags())
            assertFalse("worried" in pet.flags())
            // The calm face plus a brow per eye, two puffs of steam and a vein.
            assertTrue(pet.pet.parts.count { it.whenFlags == listOf("angry") } >= 4)
            assertTrue(pet.pet.parts.any { it.whenFlags?.containsAll(listOf("eyesOpen", "angry")) == true })
            val home = pet.home; val originX = pet.x
            val positions = ArrayList<PetBrain.TantrumPose>()
            val firstLine = pet.speech
            repeat(100) {
                step(pet)
                val position = pet.tantrumPosition(900.0, 600.0, 96.0, 64.0, 20.0, 500.0)
                assertTrue(position.x >= 12 && position.x + 96 * position.scale <= 900 - 8)
                assertTrue(position.y >= 8 && position.y + 64 * position.scale <= 600 - 8)
                assertEquals(2.0, position.scale)
                positions.add(position)
            }
            assertTrue(positions.maxOf { it.x } - positions.minOf { it.x } <= 4)
            assertTrue(positions.maxOf { it.y } - positions.minOf { it.y } in 1.0..18.0)
            assertTrue(positions.count { it.phase == 0.0 } >= 65)
            assertEquals(1, positions.map { it.anchorX to it.anchorY }.distinct().size)
            assertEquals(firstLine, pet.speech)
            assertEquals(home, pet.home)
            assertEquals(originX, pet.x)
            val start = pet.angryAt
            pet.clicked()
            assertEquals(start, pet.angryAt)
            assertEquals(firstLine, pet.speech)
            step(pet, catalog.care.angerLineMs)
            assertNotEquals(firstLine, pet.speech)
            pet.quiet = true
            assertFalse(pet.tantrum)
            assertTrue("angry" in pet.flags())
            step(pet, catalog.care.angerMs + 1)
            assertFalse(pet.active("angry"))
        }
    }

    @Test fun mealBreakAndPetSwitchResetCare() {
        val pet = brain()
        repeat(4) { snack(pet) }
        step(pet, catalog.care.mealGapMs + 1)
        repeat(35) { step(pet) }
        assertEquals(0, pet.meal)
        assertTrue(pet.fullness < 0.02)
        repeat(8) { snack(pet) }
        assertTrue(pet.bursting)
        pet.become(catalog.pet("cat"), "Byte")
        assertFalse(pet.bursting)
        assertEquals(0, pet.meal)
        assertEquals(0.0, pet.fullness)
        assertNull(pet.food)
    }

    @Test fun sleepingPinnedPetsFollowEditorResizesWithoutWaking() {
        for (vertical in listOf(false, true)) for (id in catalog.pets.keys) {
            val pet = brain(id, vertical)
            val length = (if (vertical) 80 else 120) * pet.artScale
            pet.update(0.0, 400.0, length, 0.0)
            time += 3 * 60_000 + 1
            repeat(240) { time += 17; pet.update(17.0, 400.0, length, 0.0) }
            assertTrue(pet.sleeping)
            val before = pet.x
            // Closing a bottom tool window expands the editor; layout changes must not swim home afterward.
            pet.update(0.0, 760.0, length, 0.0)
            assertEquals(before + pet.home * 360, pet.x, 0.001, "$id must follow the resized editor immediately")
            assertTrue(pet.sleeping, "A layout change must not wake $id")
            pet.update(0.0, 400.0, length, 0.0)
            assertEquals(before, pet.x, 0.001, "$id must retain its anchor when the tool window reopens")
        }
    }

    @Test fun sleepingPinnedPetsStopDrifting() {
        val pet = brain()
        time += 3 * 60_000 + 1
        repeat(300) { step(pet) }
        val position = pet.x
        repeat(30) {
            step(pet, 166)
            assertEquals(position, pet.x, 0.01, "A sleeping pet should rest rather than chase its idle drift")
        }
        assertTrue(pet.sleeping)
    }

    @Test fun sleepingRoamingPetsStayStillEvenWhenTheCaretIsNearby() {
        val pet = brain().apply { roam = true }
        repeat(60) { step(pet) }
        time += 3 * 60_000 + 1
        repeat(120) { step(pet) }
        val position = pet.x
        pet.avoid(position)
        repeat(20) { step(pet, 166); assertEquals(position, pet.x, 0.001) }
        assertTrue(pet.sleeping)
    }

    @Test fun editorResizeKeepsDraggedPetsUnderThePointerAndHandlesTinyEditors() {
        val held = brain()
        held.update(0.0, 600.0, 96.0, 0.0)
        held.dragging = true
        held.dragTo(140.0, 600.0, 96.0)
        held.update(0.0, 900.0, 96.0, 0.0)
        assertEquals(140.0, held.x, 0.001)
        val tiny = brain()
        tiny.update(0.0, 30.0, 96.0, 0.0)
        tiny.update(0.0, 760.0, 96.0, 0.0)
        assertEquals(tiny.home * (760 - 96 - 4), tiny.x, 0.001)
        tiny.update(0.0, 0.0, 96.0, 0.0)
        assertTrue(tiny.x.isFinite())
    }

    @Test fun sleepPoseAndPositionProgressIndependentOfIdleFrameRate() {
        fun atFrameRate(frameMs: Long): PetBrain {
            var clock = 10_000_000L
            val pet = PetBrain(catalog, catalog.pet("turtle"), "Shelly", clock = { clock }, random = Random(7))
            repeat(60) { clock += 17; pet.update(17.0, 600.0, 96.0, 10.0) }
            clock += 3 * 60_000 + 1
            pet.update(0.0, 600.0, 96.0, 10.0)
            var remaining = 1000L
            while (remaining > 0) {
                val dt = minOf(remaining, frameMs)
                clock += dt
                pet.update(dt.toDouble(), 600.0, 96.0, 10.0)
                remaining -= dt
            }
            return pet
        }
        val smooth = atFrameRate(17)
        val idle = atFrameRate(166)
        assertEquals(smooth.x, idle.x, 0.001)
        assertEquals(smooth.depth, idle.depth, 0.001)
        for ((group, pose) in smooth.poses) for (index in pose.indices) {
            assertEquals(pose[index], idle.poses.getValue(group)[index], 0.001, "Pose $group must use elapsed time")
        }
    }

    @Test fun pokingEscalatesAndRecoversWithoutReactionOverrides() {
        val pet = brain()
        repeat(4) { pet.clicked(); step(pet, 100) }
        assertFalse(pet.active("angry"))
        pet.clicked()
        assertTrue(pet.active("angry"))
        val line = pet.speech
        pet.react("pet"); pet.saved()
        assertEquals(line, pet.speech)
        assertFalse("happy" in pet.flags())
        step(pet, catalog.care.angerMs + 1)
        pet.clicked()
        assertFalse(pet.active("angry"))
        repeat(4) { pet.clicked() }
        assertTrue(pet.active("angry"))
        snack(pet)
        assertFalse(pet.active("angry"))
    }
}
