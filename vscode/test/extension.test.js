const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));

/** Run the real extension with just the editor boundaries replaced; no VS Code process is needed. */
function editor(initial = {}) {
  const settings = { enabled: true, pet: "cat", name: "Byte", ...initial };
  const commands = new Map(), events = {}, packets = [], focused = [];
  let provider, onFocus;
  const disposable = () => ({ dispose() {} });
  const event = (name) => (handler) => { events[name] = handler; return disposable(); };
  const api = {
    workspace: {
      getConfiguration: () => ({ get: (key) => settings[key], update: async (key, value) => { settings[key] = value; } }),
      onDidChangeConfiguration: event("config"), onDidChangeTextDocument: event("typing"),
      onDidOpenTextDocument: event("open"), onDidSaveTextDocument: event("save"),
    },
    window: {
      registerWebviewViewProvider: (_id, value) => { provider = value; return disposable(); },
      onDidOpenTerminal: event("terminal"), onDidChangeActiveTerminal: event("activeTerminal"),
      onDidChangeActiveTextEditor: event("editor"), state: { focused: true },
    },
    commands: {
      registerCommand: (id, handler) => { commands.set(id, handler); return disposable(); },
      executeCommand: async (id) => { focused.push(id); if (onFocus) onFocus(); },
    },
    languages: { onDidChangeDiagnostics: event("diagnostics"), getDiagnostics: () => [] },
    tasks: { onDidStartTask: event("taskStart"), onDidEndTaskProcess: event("taskEnd") },
    debug: { onDidStartDebugSession: event("debugStart"), onDidTerminateDebugSession: event("debugEnd") },
    extensions: { getExtension: () => undefined },
    ConfigurationTarget: { Global: 1 }, TaskGroup: { Build: 1, Test: 2 },
  };
  const sandbox = {
    module: { exports: {} },
    require: (id) => id === "vscode" ? api : id === "fs" ? { ...fs, watchFile() {}, unwatchFile() {} } : require(id),
    setTimeout: () => 1, setInterval: () => 2, clearTimeout() {}, clearInterval() {},
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, "extension.js"), "utf8"), sandbox, { filename: "extension.js" });
  sandbox.module.exports.activate({ extensionPath: root, subscriptions: [] });

  function attach({ visible = true, ready = true, eager = false } = {}) {
    let message, visibility, dispose, html;
    const view = {
      visible,
      webview: {
        postMessage: (packet) => { packets.push(JSON.parse(JSON.stringify(packet))); return Promise.resolve(true); },
        onDidReceiveMessage: (handler) => { message = handler; return disposable(); },
        set html(value) { html = value; if (eager) message({ type: "ready" }); },
        get html() { return html; },
      },
      onDidChangeVisibility: (handler) => { visibility = handler; return disposable(); },
      onDidDispose: (handler) => { dispose = handler; return disposable(); },
      ready: () => message({ type: "ready" }),
      show: () => { view.visible = true; visibility(); },
      hide: () => { view.visible = false; visibility(); },
      dispose: () => dispose(),
    };
    provider.resolveWebviewView(view);
    if (ready && !eager) view.ready();
    return view;
  }
  return { settings, commands, events, packets, focused, attach, get provider() { return provider; },
    onFocus: (handler) => { onFocus = handler; }, run: (id) => commands.get(id)() };
}

test("Poke is contributed to the Command Palette and pet toolbar and sends every tap", async () => {
  const app = editor(); app.attach(); app.packets.length = 0;
  assert.ok(manifest.contributes.commands.some((command) => command.command === "petabytes.poke"));
  assert.ok(manifest.contributes.menus["view/title"].some((command) => command.command === "petabytes.poke"));
  for (let i = 0; i < 5; i++) await app.run("petabytes.poke");
  assert.deepEqual(app.packets, Array.from({ length: 5 }, () => ({ type: "poke" })));
  assert.equal(app.focused.length, 0);
});

test("first feed and poke enable and open the panel, then wait for configuration before delivery", async () => {
  const app = editor({ enabled: false });
  await app.run("petabytes.feed");
  await app.run("petabytes.poke");
  assert.equal(app.settings.enabled, true);
  assert.ok(app.focused.every((id) => id === "petabytes.pet.focus"));
  assert.equal(app.packets.length, 0);
  const view = app.attach({ ready: false });
  assert.equal(app.packets.length, 0);
  view.ready();
  assert.deepEqual(app.packets.map((packet) => packet.type), ["config", "feed", "poke"]);
  assert.equal(app.packets[0].pet, "cat");
  assert.equal(app.packets[0].externalTantrum, false);
  assert.equal(app.packets[0].externalSplatter, false);
});

test("five pokes while a panel starts are preserved", async () => {
  const app = editor();
  for (let i = 0; i < 5; i++) await app.run("petabytes.poke");
  app.attach({ eager: true });
  assert.deepEqual(app.packets.map((packet) => packet.type), ["config", "poke", "poke", "poke", "poke", "poke"]);
});

test("revealing an existing panel delivers the interaction once", async () => {
  const app = editor(); const view = app.attach(); app.packets.length = 0;
  view.hide();
  app.onFocus(() => view.show());
  await app.run("petabytes.poke");
  assert.equal(app.packets.length, 0);
  view.ready();
  assert.deepEqual(app.packets.map((packet) => packet.type), ["config", "poke"]);
});

test("background events remain dropped while hidden, and stale views cannot flush new interactions", async () => {
  const app = editor(); const old = app.attach(); app.packets.length = 0;
  old.visible = false;
  app.events.save();
  old.dispose();
  await app.run("petabytes.poke");
  const current = app.attach({ ready: false });
  old.ready(); old.dispose();
  assert.equal(app.packets.length, 0);
  current.ready();
  assert.deepEqual(app.packets.map((packet) => packet.type), ["config", "poke"]);
});

test("the extension embeds the latest art and renderer with a matching script nonce", () => {
  const app = editor(); const view = app.attach();
  for (const file of ["pet.html", "pets.json", "picker.html"]) {
    assert.deepEqual(fs.readFileSync(path.join(root, "media", file)), fs.readFileSync(path.join(root, "..", "web", file)));
  }
  const html = view.webview.html;
  const nonce = html.match(/<script nonce="([^"]+)"/)[1];
  assert.ok(html.includes("script-src 'nonce-" + nonce + "'"));
  assert.ok(!/\{\{(?:csp|nonce|pets)\}\}/.test(html));
  assert.ok(html.includes("function tantrumPosition()"));
  const data = JSON.parse(fs.readFileSync(path.join(root, "media", "pets.json"), "utf8"));
  for (const pet of Object.values(data.pets)) {
    assert.ok(pet.parts.some((part) => part.when?.includes("angry")), pet.name);
    assert.ok(pet.splatter);
  }
});
