package com.chelayel.tidepets

import com.chelayel.tidepets.pet.PetBrain
import com.chelayel.tidepets.pet.PetCatalog
import com.intellij.codeInsight.daemon.DaemonCodeAnalyzer
import com.intellij.codeInsight.daemon.impl.HighlightInfo
import com.intellij.execution.ExecutionListener
import com.intellij.execution.ExecutionManager
import com.intellij.execution.executors.DefaultDebugExecutor
import com.intellij.execution.executors.DefaultRunExecutor
import com.intellij.openapi.command.CommandProcessor
import com.intellij.openapi.vcs.BranchChangeListener
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ex.ToolWindowManagerListener
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
        current.brain.home = settings.home.toDouble()
        listen()
        if (!timer.isRunning) { lastTick = System.nanoTime(); timer.start() }
    }

    private fun hide() {
        timer.stop()
        overlay?.let { o -> layer?.remove(o); layer?.repaint() }
        overlay = null
        layer = null
    }

    private fun tick() {
        val o = overlay ?: return
        val nowNs = System.nanoTime()
        val dtMs = (nowNs - lastTick) / 1_000_000.0
        lastTick = nowNs

        val editor = FileEditorManager.getInstance(project).selectedTextEditor
        val frame = WindowManager.getInstance().getFrame(project) as? RootPaneContainer
        val target = frame?.layeredPane
        if (editor == null || target == null || !editor.component.isShowing) { o.isVisible = false; return }
        if (layer !== target) {
            layer?.remove(o)
            target.add(o, JLayeredPane.PALETTE_LAYER)
            layer = target
        }
        // The bottom strip of the editor, clear of the scrollbars.
        val r = SwingUtilities.convertRectangle(editor.component.parent, editor.component.bounds, target)
        val gap = JBUI.scale(14)
        val h = o.preferredHeight
        val bounds = Rectangle(r.x, r.y + r.height - h - gap, (r.width - gap).coerceAtLeast(0), h)
        if (o.bounds != bounds) o.bounds = bounds
        o.isVisible = true
        o.brain.avoid(caretOverPet(editor, o, target))
        o.brain.update(dtMs, bounds.width.toDouble(), o.painter.spriteWidth, room = JBUI.scale(10).toDouble())
        o.repaint()
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
        val nearby = !o.brain.roam && p.x > pet.x - margin && p.x < pet.maxX + margin
        return if (lineHit && (o.brain.roam || nearby)) p.x.toDouble() else null
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
        projectBus.subscribe(ToolWindowManagerListener.TOPIC, object : ToolWindowManagerListener {
            override fun toolWindowShown(toolWindow: ToolWindow) {
                val id = toolWindow.id
                when {
                    AI_WINDOWS.containsMatchIn(id) -> send { react("ai") }
                    id.equals("Terminal", ignoreCase = true) -> send { react("terminal") }
                }
            }
        })

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

    private fun inThisProject(document: Document) = EditorFactory.getInstance().getEditors(document, project).isNotEmpty()

    private fun errorsInSelectedEditor(): Int {
        val editor = FileEditorManager.getInstance(project).selectedTextEditor ?: return 0
        val markup = DocumentMarkupModel.forDocument(editor.document, project, false) ?: return 0
        return markup.allHighlighters.count { HighlightInfo.fromRangeHighlighter(it)?.severity == HighlightSeverity.ERROR }
    }

    override fun dispose() = hide()

    companion object {
        private val AI_WINDOWS = Regex("copilot|ai assistant|ai chat|junie|claude|gemini|ai relay|codeium|tabnine|chatgpt|cody|continue", RegexOption.IGNORE_CASE)
        private val TEST_RUN = Regex("\\btests?\\b|spec", RegexOption.IGNORE_CASE)

        /** Apply changed settings in every open project. */
        fun refreshAll() {
            for (p in ProjectManager.getInstance().openProjects) if (!p.isDisposed) p.service<PetService>().refresh()
        }
    }
}
