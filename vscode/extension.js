// Petabytes: a pet in the Explorer that reacts to what you do.
const vscode = require("vscode");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const VIEW_ID = "petabytes.pet";
const SECTION = "petabytes";

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
  { id: "whale", label: "Whale", detail: "Blue: cruises slowly and spouts when happy" },
  { id: "clownfish", label: "Clownfish", detail: "Clem: zippy, stripy and always excited" },
  { id: "seahorse", label: "Seahorse", detail: "Sandy: bobs upright and flutters its fin" },
  { id: "shark", label: "Shark", detail: "Finn: friendly, and vegetarian" },
  { id: "dolphin", label: "Dolphin", detail: "Splash: fast, chatty and loves a flip" },
  { id: "angelfish", label: "Angelfish", detail: "Angie: glides gracefully, trailing long fins" },
  { id: "tang", label: "Blue tang", detail: "Indigo: friendly, if a little forgetful" },
  { id: "retriever", label: "Golden retriever", detail: "Biscuit: wags, tilts its head, and loves a treat" },
  { id: "cat", label: "Cat", detail: "Byte: purrs, judges, and sits on your keyboard" },
  { id: "bunny", label: "Bunny", detail: "Clover: hops, wiggles its nose, and flattens its ears" },
  { id: "hamster", label: "Hamster", detail: "Nugget: scurries, and stuffs its cheeks with snacks" },
  { id: "burger", label: "Burger", detail: "Patty: a burger with legs, and a thumbs-up for your code" },
  { id: "sushi", label: "Sushi", detail: "Nori: rolls along, and hides under its salmon" },
  { id: "pizza", label: "Pizza", detail: "Pepe: a pepperoni slice that droops when it's scared" },
  { id: "donut", label: "Donut", detail: "Sprinkles: sweet, sprinkled, and full of donut puns" },
  { id: "taco", label: "Taco", detail: "Tuesday: crunchy, and every day is its day" },
  { id: "slime", label: "Slime", detail: "Squish: a bouncy pixel slime, level 1" },
  { id: "ghost", label: "Ghost", detail: "Boo: a shy pixel ghost that floats and blushes" },
  { id: "knight", label: "Knight", detail: "Sir Pix: a pixel knight on a quest to slay your bugs" },
  { id: "robot", label: "Robot", detail: "Bolt: a pixel robot with a screen for a face" },
];

// Terminal commands worth a reaction, checked in order.
const COMMANDS = [
  [/\brm\s+-[a-z]*r[a-z]*f|\bgit\s+push\b.*--force|\bgit\s+reset\s+--hard|\bdrop\s+(table|database)\b/i, "danger"],
  [/\bgit\s+push\b/i, "gitPush"],
  [/\b(npm|pnpm|yarn|bun)\s+(i|install|add|ci)\b|\bpip3?\s+install\b|\bbrew\s+install\b|\bcargo\s+add\b/i, "install"],
  [/\b(test|jest|vitest|pytest|mocha)\b|gradlew?\s+.*\btest\b|\bmvn\s+.*\btest\b|\bgo\s+test\b|\bcargo\s+test\b/i, "test"],
  [/\b(build|compile|tsc|webpack|vite\s+build)\b|gradlew?\s+.*\b(build|assemble)\b/i, "build"],
  [/\b(npm|pnpm|yarn|bun)\s+(run\s+)?(start|dev|serve)\b|\bpython3?\s+\S+\.py\b|\bnode\s+\S+|\bcargo\s+run\b|\bgo\s+run\b/i, "run"],
];

function commandReaction(line) {
  const hit = COMMANDS.find(([re]) => re.test(line));
  if (!hit) return null;
  const key = hit[1] === "gitPush" && new Date().getDay() === 5 ? "gitPushFriday" : hit[1];
  return key;
}

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

  sub(vscode.commands.registerCommand("petabytes.toggle", async () => {
    const next = !vscode.workspace.getConfiguration(SECTION).get("enabled");
    await setEnabled(next);
    if (next) vscode.commands.executeCommand(`${VIEW_ID}.focus`);
  }));
  sub(vscode.commands.registerCommand("petabytes.show", async () => {
    await setEnabled(true);
    vscode.commands.executeCommand(`${VIEW_ID}.focus`);
  }));
  sub(vscode.commands.registerCommand("petabytes.hide", () => setEnabled(false)));
  sub(vscode.commands.registerCommand("petabytes.choose", async () => {
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

  sub(vscode.commands.registerCommand("petabytes.feed", async () => {
    if (!vscode.workspace.getConfiguration(SECTION).get("enabled")) await setEnabled(true);
    pet.post({ type: "feed", key: "feed" });
  }));

  sub(vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration(`${SECTION}.name`) || e.affectsConfiguration(`${SECTION}.pet`)) pet.post(config());
  }));

  // Typing: one message per burst; the pet keeps swimming fast for a moment on its own.
  let lastTyping = 0;
  let braces = 0;
  const undos = [];
  const Undo = vscode.TextDocumentChangeReason && vscode.TextDocumentChangeReason.Undo;
  sub(vscode.workspace.onDidChangeTextDocument((e) => {
    const scheme = e.document.uri.scheme;
    if ((scheme !== "file" && scheme !== "untitled") || !e.contentChanges.length) return;
    const now = Date.now();
    if (Undo && e.reason === Undo) {
      // Several undos in a few seconds.
      undos.push(now);
      while (undos.length && now - undos[0] > 8000) undos.shift();
      if (undos.length >= 4) { undos.length = 0; pet.post({ type: "react", key: "undo" }); }
      return;
    }
    if (now - lastTyping > 400) { lastTyping = now; pet.post({ type: "typing" }); }
    for (const change of e.contentChanges) {
      // Every 20th "{" typed drops a crumb for the pet.
      if (change.text.length <= 2 && change.text.includes("{") && ++braces % 20 === 0) pet.post({ type: "feed", snack: "{ }", key: "crumb" });
      // A big block appearing at once: an AI suggestion, or a paste.
      if (change.text.length >= 120 && change.text.split("\n").length >= 4) pet.post({ type: "react", key: "aiBig" });
    }
  }));

  // AI edits: Copilot's chat and agent edits open documents under their own schemes.
  sub(vscode.workspace.onDidOpenTextDocument((doc) => {
    if (/^(chat-editing|vscode-chat|copilot)/i.test(doc.uri.scheme)) pet.post({ type: "react", key: "ai" });
  }));

  // The terminal: opening it, and what runs in it (shell integration, VS Code 1.93+).
  sub(vscode.window.onDidOpenTerminal(() => pet.post({ type: "react", key: "terminal" })));
  sub(vscode.window.onDidChangeActiveTerminal((t) => { if (t) pet.post({ type: "react", key: "terminal" }); }));
  if (vscode.window.onDidStartTerminalShellExecution) {
    sub(vscode.window.onDidStartTerminalShellExecution((e) => {
      const key = commandReaction(e.execution.commandLine.value || "");
      if (key) pet.post({ type: "react", key, vars: { task: e.execution.commandLine.value.split(/\s+/).slice(0, 2).join(" ") } });
    }));
    sub(vscode.window.onDidEndTerminalShellExecution((e) => {
      if (typeof e.exitCode === "number" && e.exitCode !== 0 && e.exitCode !== 130) pet.post({ type: "react", key: "commandFail" });
    }));
  }

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
  sub(vscode.tasks.onDidStartTask((e) => {
    const group = e.execution.task.group;
    if (group === vscode.TaskGroup.Build) pet.post({ type: "react", key: "build" });
    else if (group === vscode.TaskGroup.Test) pet.post({ type: "react", key: "test" });
  }));
  sub(vscode.tasks.onDidEndTaskProcess((e) => {
    if (typeof e.exitCode === "number") pet.post({ type: "task", ok: e.exitCode === 0, name: e.execution.task.name });
  }));

  // Run without debugging is "running the app"; with the debugger, it's a bug hunt.
  sub(vscode.debug.onDidStartDebugSession((s) => {
    if (s.configuration && s.configuration.noDebug) pet.post({ type: "react", key: "run", vars: { task: s.name } });
    else pet.post({ type: "debug", active: true });
  }));
  sub(vscode.debug.onDidTerminateDebugSession((s) => {
    if (!(s.configuration && s.configuration.noDebug)) pet.post({ type: "debug", active: false });
  }));

  watchGit(pet, context);
}

/** Commits and branch switches, through VS Code's built-in Git extension. */
async function watchGit(pet, context) {
  const ext = vscode.extensions.getExtension("vscode.git");
  if (!ext) return;
  try {
    const git = (ext.isActive ? ext.exports : await ext.activate()).getAPI(1);
    const watch = (repo) => {
      let branch = repo.state.HEAD && repo.state.HEAD.name;
      let commit = repo.state.HEAD && repo.state.HEAD.commit;
      context.subscriptions.push(repo.state.onDidChange(() => {
        const head = repo.state.HEAD || {};
        if (head.name && branch && head.name !== branch) pet.post({ type: "react", key: "branch", vars: { branch: head.name } });
        // Same branch, new commit, and now ahead of the remote: you just committed.
        else if (head.commit && commit && head.commit !== commit && head.name === branch && (head.ahead || 0) > 0) pet.post({ type: "react", key: "commit" });
        branch = head.name;
        commit = head.commit;
      }));
    };
    git.repositories.forEach(watch);
    context.subscriptions.push(git.onDidOpenRepository(watch));
  } catch {
    // No Git, or an API this VS Code doesn't have: the pet just won't react to commits.
  }
}

function deactivate() {}

module.exports = { activate, deactivate };
