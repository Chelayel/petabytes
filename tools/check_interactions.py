"""Exercise the real shared page in headless Chrome, including every pet and reduced motion.

Run: python3 tools/check_interactions.py [--vscode] [--preview /tmp/pet-care.png]
CHROME may name another Chromium executable. No browser automation dependency is needed.
"""
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "web/pets.json").read_text())
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
VS_CODE = False


def page(script, reduced=False):
    source = (ROOT / ("vscode/media/pet.html" if VS_CODE else "web/pet.html")).read_text()
    source = (source.replace("{{csp}}", "default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-checks'")
              .replace("{{nonce}}", "checks").replace("{{pets}}", json.dumps(DATA).replace("<", "\\u003c")))
    # Only test copies expose the closure; the shipped page keeps its normal receive-only API.
    source = source.replace("window.petabytes = { receive };",
                            "window.petabytes = { receive }; window.check = { state, feed, eat, poke, frame, flags, updateCare, render, reduced, get parts() { return parts; } };")
    source = source.replace('const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;',
                            "const reduced = " + str(reduced).lower() + ";")
    host = """
      window.vscodeHostMessages = [];
      window.acquireVsCodeApi = () => ({ postMessage: (message) => window.vscodeHostMessages.push(message) });
    """ if VS_CODE else ""
    shim = """<script nonce="checks">
      window.testTime = 10000000;
      Date.now = () => window.testTime;
      window.requestAnimationFrame = () => 0;
    """ + host + "</script>"
    return source.replace("<head>", "<head>" + shim, 1).replace("</body>", '<script nonce="checks">' + script + "</script></body>")


CHECKS = "const DATA = " + json.dumps(DATA).replace("<", "\\u003c") + ";\n" + r"""
(() => {
  const { state, feed, eat, poke, frame, flags, updateCare, reduced } = window.check;
  const send = window.vscodeHostMessages
    ? (data) => window.dispatchEvent(new MessageEvent('message', { data })) : window.petabytes.receive;
  const failures = [];
  let checks = 0, frameTime = performance.now();
  const assert = (ok, message) => { checks++; if (!ok && !failures.includes(message)) failures.push(message); };
  const step = (ms = 17) => { window.testTime += ms; frameTime += ms; frame(frameTime); };
  const settle = () => { for (let i = 0; i < 35; i++) step(); };
  const snack = () => { feed(); eat(); settle(); };
  const reset = (id) => { send({ type: 'config', pet: id, ground: true, externalTantrum: false }); state.food = null; };
  if (window.vscodeHostMessages) assert(window.vscodeHostMessages.some((message) => message.type === 'ready'),
    'the VS Code page must complete its ready handshake under the nonce policy');
  // Switching twice guarantees a fresh instance even for the initial turtle.
  reset('cat'); reset('turtle');
  for (const id of Object.keys(DATA.pets)) {
    reset(id);
    const before = state.eaten;
    feed(); feed();
    assert(state.eaten === before && state.meal === 0, id + ': dropping food must not count as eating');
    eat(); settle(); snack(); snack();
    assert(state.meal === 3 && state.fullness === 0, id + ': the first three snacks must not grow the pet');
    let size = 0;
    for (let n = 4; n < DATA.care.burstAt; n++) {
      snack();
      assert(state.meal === n && state.fullness > size, id + ': every extra snack must grow the pet');
      size = state.fullness;
    }
    feed();
    state.food.x = 20; // Still reachable when an enlarged pet has its mouth near its centre.
    let mealFrames = 0;
    while (state.food && mealFrames++ < 3000) step();
    assert(state.food === null, id + ': an enlarged pet must still be able to reach its snack ' + JSON.stringify({ x: state.x, dir: state.dir, food: state.food, fullness: state.fullness }));
    assert(state.burstAt !== null, id + ': snack eight must start a burst');
    const burstAt = state.burstAt;
    feed(); poke();
    assert(state.food === null && state.burstAt === burstAt, id + ': input during a burst must be ignored');
    step(DATA.care.windupMs + 1);
    assert(state.splashed && document.getElementById('pet').style.visibility === 'hidden', id + ': the pet disappears in its splash');
    assert(document.getElementById('mess').children.length === 1, id + ': the splash must cover the page');
    assert(document.querySelectorAll('#mess .splat').length <= 50, id + ': splash geometry must stay bounded');
    step(DATA.care.burstMs);
    assert(state.burstAt === null && state.meal === 0 && state.fullness === 0, id + ': recovery must reset the meal');
    assert(document.getElementById('mess').children.length === 0 && document.getElementById('pet').style.visibility === 'visible', id + ': recovery must clear the screen');
    for (let i = 0; i < 5; i++) {
      document.getElementById('pet').dispatchEvent(new MouseEvent('click', { detail: i % 2 + 1 }));
      if (i % 2) document.getElementById('pet').dispatchEvent(new MouseEvent('dblclick'));
      step(100);
    }
    assert(flags().angry && !flags().happy, id + ': five pokes including double-clicks must cause anger');
    assert(!flags().eyesOpen && !flags().worried, id + ': anger must use its own scowling eyes, not worried eyes');
    // The angry face is the calm one plus a brow per eye, two puffs of steam and a vein.
    assert(window.check.parts.filter(({part, el}) => part.when?.length === 1 && part.when[0] === 'angry' && el.style.display !== 'none').length >= 4,
      id + ': brows, steam and a vein must be visible');
    assert(window.check.parts.some(({part, el}) => part.when?.includes('eyesOpen') && part.when.includes('angry') && el.style.display !== 'none'),
      id + ': anger must keep the pet\'s own eyes');
    if (DATA.pets[id].set === 'games') assert(DATA.pets[id].parts.filter((part) => part.when?.includes('angry')).every((part) => part.path && !/[qQcCaA]/.test(part.path)),
      id + ': pixel pets must keep blocky angry expressions');
    const angryLines = DATA.pets[id].lines.angry || DATA.lines.angry;
    assert(angryLines.includes(document.getElementById('say').textContent), id + ': anger must use the authored safe lines');
    send({ type: 'save' }); send({ type: 'react', key: 'pet' });
    assert(flags().angry && angryLines.includes(document.getElementById('say').textContent), id + ': IDE events must not erase the angry response');
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, restingFrames = 0, previousBox;
    const caption = document.getElementById('say'), firstLine = caption.textContent;
    const captionBox = caption.getBoundingClientRect();
    for (let i = 0; i < 100; i++) {
      step();
      const box = document.getElementById('pet').getBoundingClientRect();
      minX = Math.min(minX, box.x); maxX = Math.max(maxX, box.x);
      minY = Math.min(minY, box.y); maxY = Math.max(maxY, box.y);
      const visible = document.getElementById('root').getBoundingClientRect();
      assert(visible.x >= -1 && visible.y >= -1 && visible.right <= innerWidth + 1 && visible.bottom <= innerHeight + 1,
        id + ': tantrum must stay on screen');
      const textBox = caption.getBoundingClientRect();
      assert(textBox.x === captionBox.x && textBox.y === captionBox.y && textBox.width === captionBox.width,
        id + ': the caption must stay fixed while the pet stomps');
      assert(textBox.x >= 0 && textBox.y >= 0 && textBox.right <= innerWidth && textBox.bottom <= innerHeight && caption.scrollWidth <= caption.clientWidth,
        id + ': the complete shout must fit on screen');
      if (previousBox && Math.abs(previousBox.x - box.x) < 0.01 && Math.abs(previousBox.y - box.y) < 0.01) restingFrames++;
      previousBox = box;
    }
    assert(maxX - minX <= 5 && maxY - minY <= 19 && (reduced || maxY - minY > 1),
      id + ': stomps must be short and stay near the original spot');
    assert(restingFrames >= 65, id + ': the pet must pause long enough to see its expression');
    assert(document.getElementById('pet').getBoundingClientRect().width >= 180, id + ': the angry character must be enlarged where space allows');
    assert(caption.textContent === firstLine, id + ': the shout must remain readable for three seconds');
    const angryAt = state.angryAt;
    poke();
    assert(state.angryAt === angryAt && caption.textContent === firstLine, id + ': repeated pokes must extend without restarting motion or replacing the caption');
    step(DATA.care.angerLineMs);
    assert(caption.textContent !== firstLine, id + ': a later shout must appear after the reading pause');
    step(DATA.care.angerMs + 1); poke();
    assert(!flags().angry && state.pokes === 1, id + ': a pause must cool the pet down');
    for (const [w, h] of [[420, 300], [610, 170], [240, 170], [220, 120], [180, 200]]) {
      const sea = document.getElementById('sea');
      sea.style.width = w + 'px'; sea.style.height = h + 'px';
      for (let i = 0; i < 5; i++) poke();
      step(900);
      let body = document.getElementById('root').getBoundingClientRect();
      for (const line of angryLines) {
        caption.textContent = line; step();
        body = document.getElementById('root').getBoundingClientRect();
        const text = caption.getBoundingClientRect();
        assert(text.x >= 0 && text.y >= 0 && text.right <= w + 1 && text.bottom <= h + 1 && caption.scrollWidth <= caption.clientWidth,
          id + ': shout must fit the ' + w + 'x' + h + ' panel: ' + line);
        assert(text.right <= body.x || text.x >= body.right || text.bottom <= body.y || text.y >= body.bottom,
          id + ': caption must leave the character visible in the ' + w + 'x' + h + ' panel');
      }
      assert(body.x >= -1 && body.y >= -1 && body.right <= w + 1 && body.bottom <= h + 1,
        id + ': the character must fit the ' + w + 'x' + h + ' panel');
      step(DATA.care.angerMs + 1);
      sea.style.width = ''; sea.style.height = '';
    }
    snack(); snack(); snack(); snack();
    step(DATA.care.mealGapMs + 1); settle();
    assert(state.meal === 0 && state.fullness < 0.02, id + ': a meal break must digest the extra size');
    snack();
    assert(state.meal === 1 && state.fullness < 0.02, id + ': a later meal must start fresh');
  }
  reset('turtle');
  for (let i = 0; i < 5; i++) poke();
  snack();
  assert(!flags().angry && state.pokes === 0, 'an eaten snack should soothe a poked pet');
  reset('cat'); reset('turtle');
  // Exercise actual sinking and mouth hit testing, including the reduced-motion path.
  feed();
  let frames = 0;
  while (state.food && frames++ < 3000) step();
  assert(state.food === null && state.meal === 1, 'a sinking snack must reach the pet, including with reduced motion');
  for (let i = 1; i < 8; i++) { feed(); eat(); }
  step(DATA.care.windupMs + 1);
  reset('robot');
  assert(!state.splashed && state.burstAt === null && state.meal === 0 && !flags().angry, 'choosing a pet must reset all interaction state');
  assert(document.getElementById('mess').children.length === 0, 'choosing a pet must remove any splash');
  reset('cat'); reset('turtle');
  if (window.vscodeHostMessages) assert(!window.vscodeHostMessages.some((message) => message.type === 'tantrum'),
    'VS Code tantrums must stay inside the panel without requesting desktop overlays');
  const hostMessages = window.vscodeHostMessages || [];
  window.webkit = { messageHandlers: { host: { postMessage: (message) => hostMessages.push(message) } } };
  send({ type: 'config', externalTantrum: true });
  for (let i = 0; i < 5; i++) poke();
  step();
  assert(reduced || hostMessages.some((m) => m.type === 'tantrum'), 'desktop anger must request a full-display animation');
  assert(reduced || document.getElementById('pet').style.visibility === 'hidden', 'the original desktop pet must not duplicate the jumping pet');
  feed(); step();
  assert(!state.externalTantrumActive && document.getElementById('pet').style.visibility === 'visible', 'feeding must interrupt the desktop animation');
  assert(reduced || hostMessages.some((m) => m.type === 'tantrumEnd'), 'feeding must close the desktop animation window');
  eat();
  reset('cat'); reset('robot');
  send({ type: 'tantrum', pet: 'robot', durationMs: 1800, fullness: 2 });
  step();
  assert(state.tantrumScene && flags().angry && document.body.classList.contains('tantrum-stage'), 'the desktop scene must render the correct angry pet');
  const overlayLine = document.getElementById('say').textContent, overlayOrigin = state.tantrumOrigin;
  send({ type: 'tantrum', pet: 'robot', durationMs: 1800, fullness: 2, x: 5, y: 5 }); step();
  assert(document.getElementById('say').textContent === overlayLine && state.tantrumOrigin === overlayOrigin,
    'refreshing a desktop tantrum must preserve its caption and location');
  step(1801);
  assert(state.framePaused && document.getElementById('sea').style.visibility === 'hidden', 'a finished desktop scene must stop drawing');
  send({ type: 'tantrum', pet: 'robot', durationMs: 1800 }); step();
  assert(!state.framePaused && flags().angry, 'a refreshed desktop scene must resume drawing');
  send({ type: 'splatter', pet: 'robot' }); step();
  send({ type: 'tantrum', pet: 'cat', durationMs: 1800 }); step();
  assert(!state.effectOnly && !state.framePaused && document.getElementById('mess').children.length === 0,
    'reusing a desktop overlay must clear the old splash and resume the tantrum');
  document.documentElement.dataset.checks = failures.length ? 'failed' : 'passed';
  const result = document.createElement('pre'); result.id = 'results';
  result.textContent = JSON.stringify({ checks, failures }); document.body.appendChild(result);
})();
"""


def chrome(file, *args):
    with tempfile.TemporaryDirectory(prefix="petabytes-chrome-") as profile:
        return subprocess.run([CHROME, "--headless", "--no-first-run", "--no-default-browser-check",
                               "--hide-scrollbars", "--user-data-dir=" + profile, *args, file.as_uri()],
                              check=True, capture_output=True, text=True, timeout=60)


def main():
    global VS_CODE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vscode", action="store_true", help="Check synced VS Code assets with its message bridge and nonce policy")
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--tantrum-preview", type=Path)
    args = parser.parse_args()
    VS_CODE = args.vscode
    with tempfile.TemporaryDirectory(prefix="petabytes-care-") as folder:
        folder = Path(folder)
        for reduced in (False, True):
            file = folder / "checks.html"
            file.write_text(page(CHECKS, reduced))
            result = chrome(file, "--dump-dom", "--window-size=" + ("420,300" if VS_CODE else "800,600"))
            start = result.stdout.find('<pre id="results">')
            end = result.stdout.find("</pre>", start)
            if start < 0:
                raise SystemExit("Browser checks did not finish: " + result.stderr[-2000:])
            report = json.loads(html.unescape(result.stdout[start + len('<pre id="results">'):end]))
            print(("Reduced motion" if reduced else "Normal motion") + ": " + str(report["checks"]) + " checks")
            if report["failures"]:
                raise SystemExit("\n".join(report["failures"]))
        if args.preview:
            cards = []
            for pet in ("turtle", "cat", "burger", "robot"):
                for count, pokes, caption in ((3, 0, "3 snacks"), (4, 0, "4 snacks"), (7, 0, "7 snacks"), (0, 5, "5 pokes"), (8, 0, "Snack overflow")):
                    script = f"""
                      const {{state, feed, eat, poke, frame}} = window.check;
                      window.petabytes.receive({{type:'config', pet:'{pet}', ground:true}});
                      for (let i=0; i<{count}; i++) {{ feed(); eat(); }}
                      for (let i=0; i<{pokes}; i++) poke();
                      for (let i=0; i<30; i++) {{ window.testTime += 17; frame(performance.now()+17*i); }}
                      document.getElementById('say').style.transition = 'none';
                    """
                    cards.append('<figure><iframe srcdoc="' + html.escape(page(script)) + '"></iframe><figcaption>' + DATA["pets"][pet]["name"] + ' · ' + caption + '</figcaption></figure>')
            preview = folder / "preview.html"
            preview.write_text('''<!doctype html><meta charset="utf-8"><style>
              body { background:#0E1012; color:#E4E4E7; margin:24px; display:grid; grid-template-columns:repeat(5, 240px); gap:16px; font:13px -apple-system,sans-serif; }
              figure { margin:0; } iframe { width:240px; height:170px; border:1px solid #2A2E33; border-radius:10px; background:#1A1D21; } figcaption { padding:8px 0 12px; }
            </style>''' + "".join(cards))
            chrome(preview, "--window-size=1320,940", "--virtual-time-budget=1200", "--screenshot=" + str(args.preview.resolve()))
            print(args.preview.resolve())
        if args.tantrum_preview:
            cards = []
            for pet, age in (("turtle", 900), ("cat", 1700), ("burger", 3300), ("robot", 5100)):
                script = f"""
                  const {{state, frame}} = window.check;
                  window.petabytes.receive({{type:'tantrum', pet:'{pet}', durationMs:6000, x:20, y:220}});
                  window.testTime += {age}; frame(performance.now()+17);
                  document.getElementById('say').style.transition = 'none';
                """
                cards.append('<figure><iframe srcdoc="' + html.escape(page(script)) + '"></iframe><figcaption>' + DATA["pets"][pet]["name"] + ' · ' + str(age) + ' ms into the tantrum</figcaption></figure>')
            preview = folder / "tantrum.html"
            preview.write_text('''<!doctype html><meta charset="utf-8"><style>
              body { background:#0E1012; color:#E4E4E7; margin:24px; display:grid; grid-template-columns:repeat(2, 610px); gap:20px; font:13px -apple-system,sans-serif; }
              figure { margin:0; } iframe { width:610px; height:300px; border:1px solid #2A2E33; border-radius:10px; background:#1A1D21; } figcaption { padding:10px 0; }
            </style>''' + "".join(cards))
            chrome(preview, "--window-size=1300,760", "--virtual-time-budget=800", "--screenshot=" + str(args.tantrum_preview.resolve()))
            print(args.tantrum_preview.resolve())


if __name__ == "__main__":
    main()
