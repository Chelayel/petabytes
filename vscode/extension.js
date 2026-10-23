// Tide Pets: a sea turtle in the Explorer that reacts to what you do.
const vscode = require("vscode");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const VIEW_ID = "tidePets.pet";
const SECTION = "tidePets";

class PetView {
  constructor(extensionPath) {
    this.extensionPath = extensionPath;
    this.view = undefined;
  }

  resolveWebviewView(view) {
    this.view = view;
    view.webview.options = { enableScripts: true, localResourceRoots: [] };
    view.webview.html = this.html();
    view.webview.onDidReceiveMessage((msg) => {
      if (msg && msg.type === "ready") this.post({ type: "config", name: petName() });
    });
    view.onDidDispose(() => { this.view = undefined; });
  }

  post(msg) {
    if (this.view && this.view.visible) this.view.webview.postMessage(msg);
  }

  html() {
    const nonce = crypto.randomBytes(16).toString("base64");
    const page = fs.readFileSync(path.join(this.extensionPath, "media", "pet.html"), "utf8");
    const csp = `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';`;
    return page.replace("{{csp}}", csp).replace("{{nonce}}", nonce);
  }
}

function petName() {
  return vscode.workspace.getConfiguration(SECTION).get("name") || "Shelly";
}

function errorCount(uri) {
  return vscode.languages.getDiagnostics(uri)
    .filter((d) => d.severity === vscode.DiagnosticSeverity.Error).length;
}

function activate(context) {
  const pet = new PetView(context.extensionPath);
  const sub = (d) => context.subscriptions.push(d);
  const setEnabled = (value) =>
    vscode.workspace.getConfiguration(SECTION).update("enabled", value, vscode.ConfigurationTarget.Global);

  sub(vscode.window.registerWebviewViewProvider(VIEW_ID, pet));

  sub(vscode.commands.registerCommand("tidePets.toggle", async () => {
    const next = !vscode.workspace.getConfiguration(SECTION).get("enabled");
    await setEnabled(next);
    if (next) vscode.commands.executeCommand(`${VIEW_ID}.focus`);
  }));
  sub(vscode.commands.registerCommand("tidePets.show", async () => {
    await setEnabled(true);
    vscode.commands.executeCommand(`${VIEW_ID}.focus`);
  }));
  sub(vscode.commands.registerCommand("tidePets.hide", () => setEnabled(false)));

  sub(vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration(`${SECTION}.name`)) pet.post({ type: "config", name: petName() });
  }));

  // Typing: one message per burst; the turtle keeps swimming fast for a moment on its own.
  let lastTyping = 0;
  sub(vscode.workspace.onDidChangeTextDocument((e) => {
    const scheme = e.document.uri.scheme;
    if ((scheme !== "file" && scheme !== "untitled") || !e.contentChanges.length) return;
    const now = Date.now();
    if (now - lastTyping > 400) { lastTyping = now; pet.post({ type: "typing" }); }
  }));

  sub(vscode.workspace.onDidSaveTextDocument(() => pet.post({ type: "save" })));

  // Errors in the file you're looking at.
  let lastErrors = 0;
  sub(vscode.languages.onDidChangeDiagnostics(() => {
    const editor = vscode.window.activeTextEditor;
    const errors = editor ? errorCount(editor.document.uri) : 0;
    if (errors !== lastErrors) pet.post({ type: "errors", errors, before: lastErrors });
    lastErrors = errors;
  }));

  sub(vscode.window.onDidChangeActiveTextEditor((editor) => {
    if (!editor) return;
    lastErrors = errorCount(editor.document.uri);
    pet.post({ type: "file", errors: lastErrors });
  }));

  // Builds and test runs started as tasks.
  sub(vscode.tasks.onDidEndTaskProcess((e) => {
    if (typeof e.exitCode === "number") pet.post({ type: "task", ok: e.exitCode === 0, name: e.execution.task.name });
  }));

  sub(vscode.debug.onDidStartDebugSession(() => pet.post({ type: "debug", active: true })));
  sub(vscode.debug.onDidTerminateDebugSession(() => pet.post({ type: "debug", active: false })));
}

function deactivate() {}

module.exports = { activate, deactivate };
