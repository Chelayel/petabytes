// Tide Pets: a sea creature in the Explorer that reacts to what you do.
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
      if (msg && msg.type === "ready") this.post(config());
    });
    view.onDidDispose(() => { this.view = undefined; });
  }

  post(msg) {
    if (this.view && this.view.visible) this.view.webview.postMessage(msg);
  }

  html() {
    const nonce = crypto.randomBytes(16).toString("base64");
    const media = path.join(this.extensionPath, "media");
    const page = fs.readFileSync(path.join(media, "pet.html"), "utf8");
    // Inlined as a script literal: escape "<" so the art can never close the script tag.
    const pets = fs.readFileSync(path.join(media, "pets.json"), "utf8").replace(/</g, "\\u003c");
    const csp = `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';`;
    return page.replaceAll("{{csp}}", csp).replaceAll("{{nonce}}", nonce).replaceAll("{{pets}}", () => pets);
  }
}

const PETS = [
  { id: "turtle", label: "Sea turtle", detail: "Shelly: swims, paddles, and hides in her shell" },
  { id: "jellyfish", label: "Jellyfish", detail: "Bloop: pulses, drifts, and glows" },
  { id: "octopus", label: "Octopus", detail: "Inky: waves eight arms and hides in an ink cloud" },
  { id: "crab", label: "Crab", detail: "Pinchy: scuttles along the sand and snaps its claws" },
  { id: "pufferfish", label: "Pufferfish", detail: "Puff: puffs up when errors appear" },
];

function config() {
  const settings = vscode.workspace.getConfiguration(SECTION);
  // An empty name means the pet's own (Shelly, Bloop, ...).
  return { type: "config", pet: settings.get("pet") || "turtle", name: settings.get("name") || "" };
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
  sub(vscode.commands.registerCommand("tidePets.choose", async () => {
    const current = vscode.workspace.getConfiguration(SECTION).get("pet");
    const choice = await vscode.window.showQuickPick(
      PETS.map((p) => ({ ...p, description: p.id === current ? "current" : "" })),
      { placeHolder: "Choose your pet" },
    );
    if (!choice) return;
    await vscode.workspace.getConfiguration(SECTION).update("pet", choice.id, vscode.ConfigurationTarget.Global);
    await setEnabled(true);
    vscode.commands.executeCommand(`${VIEW_ID}.focus`);
  }));

  sub(vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration(`${SECTION}.name`) || e.affectsConfiguration(`${SECTION}.pet`)) pet.post(config());
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
