package com.chelayel.petabytes

import com.chelayel.petabytes.pet.PetBrain
import com.chelayel.petabytes.pet.PetCatalog
import com.intellij.codeInsight.daemon.DaemonCodeAnalyzer
import com.intellij.codeInsight.daemon.impl.HighlightInfo
import com.intellij.execution.ExecutionListener
import com.intellij.execution.ExecutionManager
import com.intellij.execution.executors.DefaultDebugExecutor
import com.intellij.execution.executors.DefaultRunExecutor
import com.intellij.openapi.command.CommandProcessor
import com.intellij.openapi.vcs.BranchChangeListener
import com.intellij.openapi.editor.EditorKind
import com.intellij.openapi.fileEditor.FileDocumentManager
import com.intellij.openapi.wm.ToolWindowManager
import com.intellij.execution.process.ProcessHandler
import com.intellij.execution.runners.ExecutionEnvironment
import com.intellij.lang.annotation.HighlightSeverity
import com.intellij.openapi.Disposable
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.editor.Document
import com.intellij.openapi.editor.EditorFactory
import com.intellij.openapi.editor.event.DocumentEvent
import com.intellij.openapi.editor.event.DocumentListener
import com.intellij.openapi.editor.impl.DocumentMarkupModel
import com.intellij.openapi.fileEditor.FileDocumentManagerListener
import com.intellij.openapi.fileEditor.FileEditor
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.fileEditor.FileEditorManagerEvent
import com.intellij.openapi.fileEditor.FileEditorManagerListener
import com.intellij.openapi.project.Project
import com.intellij.openapi.project.ProjectManager
import com.intellij.openapi.wm.WindowManager
import com.intellij.util.ui.JBUI
import java.awt.Rectangle
import javax.swing.JLayeredPane
import javax.swing.RootPaneContainer
import javax.swing.SwingUtilities
import javax.swing.Timer
import java.io.File

/**
 * One pet per project window: it floats along the bottom of the selected editor and
 * reacts to typing, saving, errors in the open file, switching files, run
 * configurations finishing, and debugging.
 */
@Service(Service.Level.PROJECT)
class PetService(private val project: Project) : Disposable {

    private val catalog by lazy { PetCatalog.load() }
    private var overlay: FloatingPet? = null
    private var layer: JLayeredPane? = null
    private val timer = Timer(33) { tick() }
    private var lastTick = System.nanoTime()

    private var lastTyping = 0L
    private var braces = 0
    private val undos = ArrayDeque<Long>()
    private var lastSave = 0L
    private var lastErrors = 0
    private var listening = false

    /** Show or hide the pet to match the settings. Called at startup and whenever they change. */
    fun refresh() {
        val settings = PetSettings.get().state
        if (!settings.enabled) { hide(); return }
        val pet = catalog.pet(settings.pet)
        val name = settings.name?.takeIf { it.isNotBlank() } ?: pet.name
        val scale = PetSettings.scaleFor(settings.size)
        var current = overlay
        if (current != null && current.painter.scale != JBUI.scale(1) * scale) { hide(); current = null }
        if (current == null) {
            val brain = PetBrain(catalog, pet, name)
            overlay = FloatingPet(brain, scale) { home ->
                // Remember where it was dropped, for every project window.
                PetSettings.get().state.apply { roam = false; this.home = home.toFloat() }
                PetService.refreshAll()
            }
            brain.hello()
            current = overlay
        } else if (current.brain.pet !== pet || current.brain.name != name) {
            current.brain.become(pet, name)
            current.brain.hello()
        }
        current!!.brain.roam = settings.roam
        current.brain.vertical = settings.position != "bottom"
        current.brain.home = settings.home.toDouble()
        listen()
        if (!timer.isRunning) { lastTick = System.nanoTime(); timer.start() }
    }

    private fun hide() {
        timer.stop()
        lastFileEditor = null
        overlay?.let { o -> layer?.remove(o); layer?.repaint() }
        overlay = null
        layer = null
    }

    private fun tick() {
        val o = overlay ?: return
        val nowNs = System.nanoTime()
        val dtMs = (nowNs - lastTick) / 1_000_000.0
        lastTick = nowNs

        val editor = fileEditor()
        val frame = WindowManager.getInstance().getFrame(project) as? RootPaneContainer
        val target = frame?.layeredPane
        if (editor == null || target == null || !editor.component.isShowing) { o.isVisible = false; return }
        if (layer !== target) {
            layer?.remove(o)
            // As Any: from Kotlin the Integer unboxes to the add(Component, int) overload, which
            // takes it as a list index, not a layer, and the pet can end up under the editor.
            target.add(o, JLayeredPane.PALETTE_LAYER as Any)
            layer = target
        }
        // A strip along the editor's right edge or its bottom edge, clear of the scrollbars.
        val r = SwingUtilities.convertRectangle(editor.component.parent, editor.component.bounds, target)
        val gap = JBUI.scale(14)
        val vertical = o.brain.vertical
        val bounds = if (vertical) {
            val w = o.preferredWidth.coerceAtMost(r.width)
            Rectangle(r.x + r.width - w - gap, r.y + gap, w, (r.height - 2 * gap).coerceAtLeast(0))
        } else {
            val h = o.preferredHeight
            Rectangle(r.x, r.y + r.height - h - gap, (r.width - gap).coerceAtLeast(0), h)
        }
        if (o.bounds != bounds) o.bounds = bounds
        o.isVisible = true
        o.brain.avoid(caretOverPet(editor, o, target))
        watchToolWindows()
        watchClaudeCode()
        if (vertical) o.brain.update(dtMs, bounds.height.toDouble(), o.painter.spriteHeight, room = JBUI.scale(6).toDouble())
        else o.brain.update(dtMs, bounds.width.toDouble(), o.painter.spriteWidth, room = JBUI.scale(10).toDouble())
        o.repaint()
    }

    private var lastFileEditor: com.intellij.openapi.editor.Editor? = null

    /**
     * The file editor the pet swims beside. Not just the "selected" one: with focus in a tool window, that can be the
     * tool window's own editor (Copilot's chat box, AI Assistant's, a diff preview), and the pet would jump in there.
     * So only a main editor outside every tool window counts, and while focus is elsewhere it stays by the last one.
     */
    private fun fileEditor(): com.intellij.openapi.editor.Editor? {
        val selected = FileEditorManager.getInstance(project).selectedTextEditor
        if (selected != null && isFileEditor(selected)) lastFileEditor = selected
        val editor = lastFileEditor ?: return null
        if (editor.isDisposed) { lastFileEditor = null; return null }
        return editor.takeIf { it.component.isShowing && isFileEditor(it) }
    }

    private fun isFileEditor(editor: com.intellij.openapi.editor.Editor): Boolean {
        if (editor.editorKind != EditorKind.MAIN_EDITOR) return false
        val twm = ToolWindowManager.getInstance(project)
        return twm.toolWindowIds.none { id ->
            val window = twm.getToolWindow(id)
            window != null && window.isVisible && SwingUtilities.isDescendingFrom(editor.component, window.component)
        }
    }

    /**
     * The caret's x (in the pet layer) when you're working on a line the pet covers:
     * a roaming pet swims clear of it, one that stays put fades and lets clicks through.
     */
    private fun caretOverPet(editor: com.intellij.openapi.editor.Editor, o: FloatingPet, target: JLayeredPane): Double? {
        val content = editor.contentComponent
        if (!content.isFocusOwner) return null
        val xy = editor.visualPositionToXY(editor.caretModel.visualPosition)
        val p = SwingUtilities.convertPoint(content, xy, o)
        val pet = o.petBounds()
        val margin = JBUI.scale(24)
        val lineHit = p.y + editor.lineHeight > pet.y && p.y < pet.maxY
        val besidePet = p.x > pet.x - margin && p.x < pet.maxX + margin
        if (o.brain.vertical) {
            // Only when the caret is right beside it; then it swims clear up or down.
            return if (besidePet && p.y + editor.lineHeight > pet.y - margin && p.y < pet.maxY + margin) p.y.toDouble() else null
        }
        return if (lineHit && (o.brain.roam || besidePet)) p.x.toDouble() else null
    }

    private fun send(action: PetBrain.() -> Unit) {
        ApplicationManager.getApplication().invokeLater({ overlay?.brain?.action() }, project.disposed)
    }

    private fun listen() {
        if (listening) return
        listening = true
        val projectBus = project.messageBus.connect(this)
        val appBus = ApplicationManager.getApplication().messageBus.connect(this)

        EditorFactory.getInstance().eventMulticaster.addDocumentListener(object : DocumentListener {
            override fun documentChanged(event: DocumentEvent) {
                if (!inThisProject(event.document)) return
                val now = System.currentTimeMillis()
                val command = CommandProcessor.getInstance().currentCommandName.orEmpty()
                if (command.startsWith("Undo")) {
                    // Several undos in a few seconds.
                    undos.addLast(now)
                    while (undos.isNotEmpty() && now - undos.first() > 8000) undos.removeFirst()
                    if (undos.size >= 4) { undos.clear(); send { react("undo") } }
                    return
                }
                if (now - lastTyping > 400) { lastTyping = now; send { typing() } }
                val text = event.newFragment
                // Every 20th "{" typed drops a crumb for the pet.
                if (text.length <= 2 && text.contains('{') && ++braces % 20 == 0) feed("{ }", "crumb")
                // A big block appearing at once, not a paste: most likely an AI suggestion.
                if (text.length >= 120 && text.count { it == '\n' } >= 3 && !command.contains("Paste")) send { react("aiBig") }
            }
        }, this)

        // AI assistants and the terminal, by the tool window you open.

        // Branch switches. The VCS API isn't in every IDE, so this is best effort.
        runCatching {
            projectBus.subscribe(BranchChangeListener.VCS_BRANCH_CHANGED, object : BranchChangeListener {
                override fun branchWillChange(branchName: String) {}
                override fun branchHasChanged(branchName: String) { send { react("branch", mapOf("branch" to branchName)) } }
            })
        }

        // The IDE also saves on its own (when the window loses focus), so only react now and then.
        appBus.subscribe(FileDocumentManagerListener.TOPIC, object : FileDocumentManagerListener {
            override fun beforeDocumentSaving(document: Document) {
                if (!inThisProject(document)) return
                val now = System.currentTimeMillis()
                if (now - lastSave > 8000) { lastSave = now; send { saved() } }
            }
        })

        projectBus.subscribe(FileEditorManagerListener.FILE_EDITOR_MANAGER, object : FileEditorManagerListener {
            override fun selectionChanged(event: FileEditorManagerEvent) {
                if (event.newFile == null) return
                lastErrors = errorsInSelectedEditor()
                val errors = lastErrors
                send { fileChanged(errors) }
            }
        })

        projectBus.subscribe(DaemonCodeAnalyzer.DAEMON_EVENT_TOPIC, object : DaemonCodeAnalyzer.DaemonListener {
            override fun daemonFinished(fileEditors: Collection<FileEditor>) {
                val errors = errorsInSelectedEditor()
                if (errors != lastErrors) send { errorsChanged(errors) }
                lastErrors = errors
            }
        })

        projectBus.subscribe(ExecutionManager.EXECUTION_TOPIC, object : ExecutionListener {
            override fun processStarted(executorId: String, env: ExecutionEnvironment, handler: ProcessHandler) {
                val name = env.runProfile.name
                when (executorId) {
                    DefaultDebugExecutor.EXECUTOR_ID -> send { debug(true) }
                    DefaultRunExecutor.EXECUTOR_ID -> send { react(if (TEST_RUN.containsMatchIn(name)) "test" else "run", mapOf("task" to name)) }
                }
            }

            override fun processTerminated(executorId: String, env: ExecutionEnvironment, handler: ProcessHandler, exitCode: Int) {
                if (executorId == DefaultDebugExecutor.EXECUTOR_ID) { send { debug(false) }; return }
                // Stopped by hand: not a failure worth worrying about.
                if (handler.getUserData(ProcessHandler.TERMINATION_REQUESTED) == true) return
                val name = env.runProfile.name
                send { taskFinished(exitCode == 0, name) }
            }
        })
    }

    /** Drop a snack; [key] is the reaction to show with it ("feed" from the menu, "crumb" from typing). */
    fun feed(snack: String? = null, key: String = "feed") {
        send {
            val width = overlay?.width?.toDouble() ?: 400.0
            feed(width, snack)
            react(key)
        }
    }

    /** A file open in this project's editor: not the terminal, a console or a diff, whose text is documents too. */
    private fun inThisProject(document: Document): Boolean =
        FileDocumentManager.getInstance().getFile(document) != null &&
            EditorFactory.getInstance().getEditors(document, project).any { it.editorKind == EditorKind.MAIN_EDITOR }

    // The Terminal and AI tool windows, checked a few times a second: a reaction when one becomes
    // visible or gets focus, each time (the reaction's own cooldown stops doubles).
    private val shownWindows = HashSet<String>()
    private var activeWindow: String? = null
    private var lastWindowCheck = 0L

    private fun watchToolWindows() {
        val now = System.currentTimeMillis()
        if (now - lastWindowCheck < 300) return
        lastWindowCheck = now
        val twm = ToolWindowManager.getInstance(project)
        fun keyFor(id: String) = when {
            AI_WINDOWS.containsMatchIn(id) -> "ai"
            id.equals("Terminal", ignoreCase = true) -> "terminal"
            else -> null
        }
        for (id in twm.toolWindowIds) {
            val key = keyFor(id) ?: continue
            val visible = twm.getToolWindow(id)?.isVisible == true
            if (visible && shownWindows.add(id)) overlay?.brain?.react(key)
            if (!visible) shownWindows.remove(id)
        }
        val active = twm.activeToolWindowId
        if (active != null && active != activeWindow) keyFor(active)?.let { overlay?.brain?.react(it) }
        activeWindow = active
    }

    // What Claude Code is doing, from the Petabytes add-on for Claude Code: it writes its latest event to this file,
    // which every open window checks (a cheap look at the file's time, a read only when it changed).
    private val claudeEvents = File(System.getProperty("user.home"), ".petabytes/claude-code.json")
    private var claudeSeen = claudeEvents.lastModified()
    private var lastClaudeCheck = 0L

    private fun watchClaudeCode() {
        val now = System.currentTimeMillis()
        if (now - lastClaudeCheck < 800) return
        lastClaudeCheck = now
        val modified = claudeEvents.lastModified()
        if (modified <= claudeSeen) return
        claudeSeen = modified
        val text = runCatching { claudeEvents.readText() }.getOrNull() ?: return
        val key = CLAUDE_KEY.find(text)?.groupValues?.get(1) ?: return
        val at = CLAUDE_AT.find(text)?.groupValues?.get(1)?.toLongOrNull() ?: return
        // Only fresh news: an event from a minute ago isn't one to react to now.
        if (now - at < 15_000) overlay?.brain?.react(key)
    }

    private fun errorsInSelectedEditor(): Int {
        val editor = fileEditor() ?: return 0
        val markup = DocumentMarkupModel.forDocument(editor.document, project, false) ?: return 0
        return markup.allHighlighters.count { HighlightInfo.fromRangeHighlighter(it)?.severity == HighlightSeverity.ERROR }
    }

    override fun dispose() = hide()

    companion object {
        private val AI_WINDOWS = Regex("copilot|ai ?assistant|ai chat|jetbrains ai|junie|claude|gemini|ai relay|codeium|windsurf|tabnine|chatgpt|codex|cody|continue|cline|amazon q", RegexOption.IGNORE_CASE)
        private val CLAUDE_KEY = Regex("\"key\"\\s*:\\s*\"(\\w+)\"")
        private val CLAUDE_AT = Regex("\"at\"\\s*:\\s*(\\d+)")
        private val TEST_RUN = Regex("\\btests?\\b|spec", RegexOption.IGNORE_CASE)

        /** Apply changed settings in every open project. */
        fun refreshAll() {
            for (p in ProjectManager.getInstance().openProjects) if (!p.isDisposed) p.service<PetService>().refresh()
        }
    }
}
