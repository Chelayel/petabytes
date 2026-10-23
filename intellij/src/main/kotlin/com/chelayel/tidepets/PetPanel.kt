package com.chelayel.tidepets

import com.intellij.codeInsight.daemon.DaemonCodeAnalyzer
import com.intellij.codeInsight.daemon.impl.HighlightInfo
import com.intellij.execution.ExecutionListener
import com.intellij.execution.ExecutionManager
import com.intellij.execution.executors.DefaultDebugExecutor
import com.intellij.execution.process.ProcessHandler
import com.intellij.execution.runners.ExecutionEnvironment
import com.intellij.lang.annotation.HighlightSeverity
import com.intellij.openapi.Disposable
import com.intellij.openapi.application.ApplicationManager
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
import com.intellij.openapi.util.Disposer
import com.intellij.ui.ColorUtil
import com.intellij.ui.JBColor
import com.intellij.ui.jcef.JBCefBrowser
import com.intellij.util.ui.UIUtil
import org.cef.browser.CefBrowser
import org.cef.browser.CefFrame
import org.cef.handler.CefLoadHandlerAdapter
import java.awt.BorderLayout
import java.awt.Color
import javax.swing.JPanel

/**
 * The pet's tool window: the shared pet page in a JCEF view, and the IDE events
 * it reacts to (typing, saving, errors in the open file, switching files, run
 * configurations finishing, debugging).
 */
class PetPanel(private val project: Project) : JPanel(BorderLayout()), Disposable {

    // Off-screen rendering, the IDE's own default for JCEF: the page is painted into
    // the component at its current size and scale, so it survives monitor changes.
    private val browser = JBCefBrowser.createBuilder().setOffScreenRendering(true).build()
    private val pending = ArrayList<String>()
    @Volatile private var pageReady = false

    private var lastTyping = 0L
    private var lastSave = 0L
    private var lastErrors = 0

    init {
        Disposer.register(this, browser)
        browser.jbCefClient.addLoadHandler(object : CefLoadHandlerAdapter() {
            override fun onLoadEnd(b: CefBrowser?, frame: CefFrame?, httpStatusCode: Int) {
                if (frame?.isMain != true) return
                synchronized(pending) { pageReady = true; pending.forEach(::run); pending.clear() }
            }
        }, browser.cefBrowser)
        add(browser.component, BorderLayout.CENTER)
        browser.loadHTML(page())
        send("config", "name" to PetSettings.get().state.name, "background" to hex(UIUtil.getPanelBackground()), "vars" to themeVars())
        listen()
    }

    private fun listen() {
        val projectBus = project.messageBus.connect(this)
        val appBus = ApplicationManager.getApplication().messageBus.connect(this)

        EditorFactory.getInstance().eventMulticaster.addDocumentListener(object : DocumentListener {
            override fun documentChanged(event: DocumentEvent) {
                if (!inThisProject(event.document)) return
                val now = System.currentTimeMillis()
                if (now - lastTyping > 400) { lastTyping = now; send("typing") }
            }
        }, this)

        // The IDE also saves on its own (when the window loses focus), so only react now and then.
        appBus.subscribe(FileDocumentManagerListener.TOPIC, object : FileDocumentManagerListener {
            override fun beforeDocumentSaving(document: Document) {
                if (!inThisProject(document)) return
                val now = System.currentTimeMillis()
                if (now - lastSave > 8000) { lastSave = now; send("save") }
            }
        })

        projectBus.subscribe(FileEditorManagerListener.FILE_EDITOR_MANAGER, object : FileEditorManagerListener {
            override fun selectionChanged(event: FileEditorManagerEvent) {
                if (event.newFile == null) return
                lastErrors = errorsInSelectedEditor()
                send("file", "errors" to lastErrors)
            }
        })

        projectBus.subscribe(DaemonCodeAnalyzer.DAEMON_EVENT_TOPIC, object : DaemonCodeAnalyzer.DaemonListener {
            override fun daemonFinished(fileEditors: Collection<FileEditor>) {
                val errors = errorsInSelectedEditor()
                if (errors != lastErrors) send("errors", "errors" to errors, "before" to lastErrors)
                lastErrors = errors
            }
        })

        projectBus.subscribe(ExecutionManager.EXECUTION_TOPIC, object : ExecutionListener {
            override fun processStarted(executorId: String, env: ExecutionEnvironment, handler: ProcessHandler) {
                if (executorId == DefaultDebugExecutor.EXECUTOR_ID) send("debug", "active" to true)
            }

            override fun processTerminated(executorId: String, env: ExecutionEnvironment, handler: ProcessHandler, exitCode: Int) {
                if (executorId == DefaultDebugExecutor.EXECUTOR_ID) { send("debug", "active" to false); return }
                // Stopped by hand: not a failure worth worrying about.
                if (handler.getUserData(ProcessHandler.TERMINATION_REQUESTED) == true) return
                send("task", "ok" to (exitCode == 0), "name" to env.runProfile.name)
            }
        })
    }

    private fun inThisProject(document: Document) = EditorFactory.getInstance().getEditors(document, project).isNotEmpty()

    private fun errorsInSelectedEditor(): Int {
        val editor = FileEditorManager.getInstance(project).selectedTextEditor ?: return 0
        val markup = DocumentMarkupModel.forDocument(editor.document, project, false) ?: return 0
        return markup.allHighlighters.count { HighlightInfo.fromRangeHighlighter(it)?.severity == HighlightSeverity.ERROR }
    }

    // ---- host → page --------------------------------------------------------

    private fun send(type: String, vararg fields: Pair<String, Any?>) {
        val call = "window.tidePets && window.tidePets.receive(" + json(mapOf("type" to type) + fields) + ")"
        synchronized(pending) { if (pageReady) run(call) else pending.add(call) }
    }

    private fun run(js: String) = browser.cefBrowser.executeJavaScript(js, browser.cefBrowser.url, 0)

    private fun page(): String {
        val html = javaClass.getResourceAsStream("/pet/pet.html")?.bufferedReader()?.readText()
            ?: error("pet.html is missing from the plugin")
        return html
            .replace("{{csp}}", "default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-idea';")
            .replace("{{nonce}}", "idea")
    }

    /** The page's text and speech-bubble colors, from the IDE's current look. */
    private fun themeVars(): Map<String, String> {
        val bg = UIUtil.getPanelBackground()
        val dark = ColorUtil.isDark(bg)
        return mapOf(
            "--fg" to hex(UIUtil.getLabelForeground()),
            "--muted" to hex(UIUtil.getContextHelpForeground()),
            "--widget" to hex(if (dark) ColorUtil.brighter(bg, 1) else ColorUtil.darker(bg, 1)),
            "--border" to hex(JBColor.border()),
        )
    }

    private fun hex(c: Color) = "#" + ColorUtil.toHex(c)

    private fun json(value: Any?): String = when (value) {
        null -> "null"
        is Boolean, is Number -> value.toString()
        is Map<*, *> -> value.entries.joinToString(",", "{", "}") { json(it.key.toString()) + ":" + json(it.value) }
        else -> buildString {
            append('"')
            for (ch in value.toString()) when {
                ch == '"' -> append("\\\"")
                ch == '\\' -> append("\\\\")
                ch < ' ' || ch == ' ' || ch == ' ' -> append(String.format("\\u%04x", ch.code))
                else -> append(ch)
            }
            append('"')
        }
    }

    override fun dispose() {}
}
