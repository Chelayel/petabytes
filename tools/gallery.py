"""Draws the README's pictures of the pets: docs/pets.png (every pet) and docs/moods.png (reactions).

Each card is web/pet.html, the page VS Code and the Mac show, sent the messages an editor would send,
then photographed by headless Chrome. Randomness is seeded so the pictures come out the same each time.
Run: python3 tools/gallery.py   (CHROME=/path/to/chrome to choose the browser)
"""
import glob, html, json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = (ROOT / "web/pet.html").read_text()
DATA = json.loads((ROOT / "web/pets.json").read_text())
COLUMNS, CARD_W, CARD_H, CAPTION, GAP, PAD = 5, 290, 190, 34, 22, 30


def chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for path in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 *sorted(glob.glob(os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/*")), reverse=True)]:
        if os.path.exists(path):
            return path
    sys.exit("No Chrome found; set CHROME.")


def card_page(seed, script):
    """pet.html with seeded randomness, a movable clock, and a script of messages to play."""
    shim = f"""<script>
      (() => {{
        let s = {seed};
        Math.random = () => (s = s * 16807 % 2147483647) / 2147483647;
        const now = Date.now.bind(Date);
        window.skip = 0;
        Date.now = () => now() + window.skip;
      }})();
    </script>"""
    page = (PAGE.replace("{{csp}}", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
            .replace("{{nonce}}", "gallery")
            .replace("{{pets}}", json.dumps(DATA).replace("<", "\\u003c"))
            .replace("<head>", "<head>" + shim, 1))
    play = f"""<script>
      const send = (m) => window.petabytes.receive(m);
      const say = (text) => {{ const el = document.getElementById("say"); el.style.transition = "none"; el.textContent = text; el.classList.add("on"); }};
      {script}
    </script>"""
    return page.replace("</body>", play + "</body>")


def sheet(cards, out):
    """cards: (pet id, caption, script run in the card, line it ends up saying)."""
    rows = (len(cards) + COLUMNS - 1) // COLUMNS
    width = PAD * 2 + COLUMNS * CARD_W + (COLUMNS - 1) * GAP
    height = PAD * 2 + rows * (CARD_H + CAPTION) + (rows - 1) * GAP
    items = []
    for i, (pet, caption, script, line) in enumerate(cards):
        name = DATA["pets"][pet]["name"]
        # The pet says its line once everything has settled (the timeline's last step).
        full = f"send({{ type: 'config', pet: '{pet}', name: '{name}' }});\n{script}\nsetTimeout(() => say({json.dumps(line)}), 5600);"
        items.append(f"""<figure><iframe srcdoc="{html.escape(card_page(i + 7, full))}"></iframe><figcaption>{html.escape(caption)}</figcaption></figure>""")
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>
      body {{ margin: 0; padding: {PAD}px; background: #0E1012; font: 15px -apple-system, "Segoe UI", sans-serif; color: #E4E4E7;
             display: grid; grid-template-columns: repeat({COLUMNS}, {CARD_W}px); gap: {GAP}px; }}
      figure {{ margin: 0; }}
      iframe {{ width: {CARD_W}px; height: {CARD_H}px; border: 1px solid #2A2E33; border-radius: 10px; background: #1A1D21; display: block; box-sizing: border-box; }}
      figcaption {{ height: {CAPTION}px; line-height: {CAPTION}px; }}
    </style></head><body>{''.join(items)}</body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(doc)
    subprocess.run([chrome(), "--headless", "--hide-scrollbars", "--force-device-scale-factor=2", "--virtual-time-budget=6500",
                    f"--window-size={width},{height}", f"--screenshot={out}", f"file://{f.name}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(f.name)
    print(out)


def first_line(pet, key):
    p = DATA["pets"][pet]
    return (p.get("lines", {}).get(key) or DATA["lines"][key])[0].replace("{name}", p["name"])


pets = [(id, f"{p['name']} the {p['label'].lower()}", "", first_line(id, "click")) for id, p in ((id, DATA["pets"][id]) for id in DATA["order"])]
sheet(pets, ROOT / "docs/pets.png")

moods = [
    ("turtle", "You're typing", "setInterval(() => send({ type: 'typing' }), 1000);", "Ooh, typing!"),
    ("knight", "You fixed every error", "send({ type: 'errors', errors: 2, before: 0 }); setTimeout(() => send({ type: 'errors', errors: 0, before: 2 }), 4800);", "LEVEL UP!"),
    ("pufferfish", "A new error appeared", "setTimeout(() => send({ type: 'errors', errors: 1, before: 0 }), 4000);", "Uh oh."),
    ("cat", "Your tests failed", "setTimeout(() => send({ type: 'task', ok: false, name: 'npm test' }), 4800);", "Oof, npm test."),
    ("duck", "You're debugging", "send({ type: 'debug', active: true });", "Explain it to me, line by line."),
    ("retriever", "You stepped away", "setTimeout(() => { window.skip = 4 * 60 * 1000; }, 300);", "zzz..."),
    ("shark", "You opened Copilot", "setTimeout(() => send({ type: 'react', key: 'ai' }), 4800);", "Two assistants are better than one."),
    ("hamster", "You fed it five snacks", "setTimeout(() => send({ type: 'react', key: 'full' }), 5000);", "My cheeks are full."),
    ("bunny", "You double-clicked it", "setTimeout(() => send({ type: 'react', key: 'pet' }), 4900);", "*happy nose wiggles*"),
    ("burger", "You saved a file", "setTimeout(() => send({ type: 'save' }), 4800);", "Saved! Fresh off the grill."),
    ("pizza", "You took a screenshot", "setTimeout(() => send({ type: 'react', key: 'screenshot' }), 4900);", "Cheese!"),
    ("clownfish", "You switched to the terminal", "setTimeout(() => send({ type: 'react', key: 'terminal' }), 4800);", "Command line time!"),
    ("slime", "You committed", "setTimeout(() => send({ type: 'react', key: 'commit' }), 4800);", "Achievement unlocked: Commit!"),
    ("ghost", "It's past midnight", "", "Midnight? My favorite hour."),
    ("robot", "You opened your AI assistant", "setTimeout(() => send({ type: 'react', key: 'ai' }), 4800);", "A fellow AI! Beep!"),
]
sheet(moods, ROOT / "docs/moods.png")
