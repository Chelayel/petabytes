"""Generates web/pets.json: every pet's art, motion and lines, shared by both IDEs.

Each pet is drawn in a 120x80 box facing right. A part is one shape
(path / circle / ellipse) in a group; groups take a pose per mood
(translate, scale, rotate about a pivot), and parts or groups can
oscillate (rot / sx / sy / ty: [amount, period in seconds, phase 0-1]).
`when` shows a part only in some states: eyesOpen, eyesClosed, eyesHappy,
worried, debugging, hiding.
Run: python3 tools/pets.py > web/pets.json
"""
import json, math

def p(d, group, **kw):  return {"path": d, "group": group, **kw}
def c(cx, cy, r, group, **kw): return {"circle": [cx, cy, r], "group": group, **kw}
def e(cx, cy, rx, ry, group, **kw): return {"ellipse": [cx, cy, rx, ry], "group": group, **kw}

def sweat(x, y): return p(f"M{x} {y} q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "face", fill="#7DD3FC", when=["worried"])
def lens(x, y):
    return [c(x, y, 5, "tool", fill="rgba(253,230,138,0.15)", stroke="#FACC15", sw=1.8, when=["debugging"]),
            p(f"M{x-3.5} {y+3.5} l-5 5", "tool", stroke="#FACC15", sw=2.2, when=["debugging"])]
def eye_set(cx, cy, r, grp, eye, sclera=None, hl=True):
    parts = []
    if sclera: parts.append(c(cx - 1.5, cy, r + 2.6, grp, fill=sclera, when=["eyesOpen"]))
    parts.append(c(cx, cy, r, grp, fill=eye, when=["eyesOpen"]))
    if hl: parts.append(c(cx + r * 0.4, cy - r * 0.4, r * 0.32, grp, fill="#FFFFFF", when=["eyesOpen"]))
    w = r * 1.25
    parts.append(p(f"M{cx-w} {cy} q{w} {r} {2*w} 0", grp, stroke=eye, sw=1.6, when=["eyesClosed"]))
    parts.append(p(f"M{cx-w} {cy+0.8} q{w} {-1.5*r} {2*w} 0", grp, stroke=eye, sw=1.6, when=["eyesHappy"]))
    return parts

PETS = {}

# ---- Sea turtle ---------------------------------------------------------
eye = "#0E1012"
PETS["turtle"] = {
  "label": "Sea turtle", "name": "Shelly", "flip": True, "floor": False, "speed": 1.0,
  "bob": [6, 3.2], "glow": "rgba(94,234,212,0.45)", "mouth": [116, 44], "head": [110, 30],
  "parts": [
    p("M36 48 q-14 4 -22 15 q13 2 26 -9z", "limbs", fill="#5EEAD4", pivot=[34, 49], rot=[20, 1.6, 0.5]),
    p("M21 45 l-9 3 l9 3z", "limbs", fill="#5EEAD4"),
    p("M22 46 Q60 58 98 46 Z", "body", fill="#FDBA74"),
    p("M20 46 Q22 14 60 14 Q96 14 100 46 Z", "body", fill="#0F766E", stroke="#5EEAD4", sw=2),
    p("M44 19 L52 31 L68 31 L76 19 M52 31 L46 45 M68 31 L74 45 M33 34 L52 31 M68 31 L87 34", "body", stroke="#5EEAD4", sw=1.5, opacity=0.7),
    p("M70 47 q6 15 26 19 q-4 -13 -18 -21z", "limbs", fill="#5EEAD4", pivot=[72, 48], rot=[20, 1.6, 0]),
    p("M95 41 q4 -10 14 -9 q9 1 9 10 q-2 8 -12 8 q-8 0 -11 -4z", "face", fill="#5EEAD4"),
    c(104, 45, 1.6, "face", fill="#2DD4BF"),
    *eye_set(109, 38, 2.5, "face", eye),
    p("M105 33.5 l7 2", "face", stroke=eye, sw=1.4, when=["worried"]),
    p("M111 45 q3 1.5 5.5 -1", "face", stroke=eye, sw=1.2),
    sweat(100, 29),
    *lens(117, 52),
  ],
  "poses": {
    "hiding":   {"face": {"tx": -14, "ty": 2, "s": 0.55, "p": [98, 42]}, "limbs": {"s": 0.5, "p": [60, 46]}},
    "sleeping": {"face": {"tx": -3, "ty": 3, "r": 8, "p": [98, 42]}},
    "curious":  {"face": {"tx": 3, "ty": -4, "r": -12, "p": [98, 42]}},
  },
  "lines": {"click": ["Hi!", "Hehe.", "Wheee!", "*happy flipper noises*", "You've got this."],
            "yikes": ["Yikes!", "I'll just hide for a sec.", "That's a lot of red."]},
}

# ---- Jellyfish ----------------------------------------------------------
jeye = "#3B0764"
tent = lambda d, x, y, ph: p(d, "tentacles", stroke="#E879F9", sw=2.5, pivot=[x, y], rot=[10, 2.0, ph])
PETS["jellyfish"] = {
  "label": "Jellyfish", "name": "Bloop", "flip": False, "floor": False, "speed": 0.6,
  "bob": [8, 3.4], "glow": "rgba(240,171,252,0.55)", "mouth": [60, 14], "head": [80, 14],
  "parts": [
    tent("M45 40 q-5 7 0 14 q5 7 0 14", 45, 40, 0),
    tent("M54 41 q-4 8 0 16 q4 8 0 14", 54, 41, 0.25),
    tent("M66 41 q4 8 0 16 q-4 8 0 14", 66, 41, 0.5),
    tent("M75 40 q5 7 0 14 q-5 7 0 14", 75, 40, 0.75),
    p("M58 42 q-2 10 2 18", "tentacles", stroke="#F5D0FE", sw=3.2, opacity=0.85, pivot=[58, 42], rot=[6, 1.6, 0.3]),
    p("M62 42 q2 10 -2 18", "tentacles", stroke="#F5D0FE", sw=3.2, opacity=0.85, pivot=[62, 42], rot=[6, 1.6, 0.8]),
    p("M34 40 Q34 12 60 12 Q86 12 86 40 Q80 44 73 40 Q66 45 60 40 Q54 45 47 40 Q40 44 34 40Z", "bell", fill="#F0ABFC", opacity=0.92, stroke="#FAE8FF", sw=1.5),
    p("M42 30 Q45 19 57 16", "bell", stroke="#FAE8FF", sw=2, opacity=0.6),
    c(47, 34, 2, "bell", fill="#F9A8D4", opacity=0.8), c(73, 34, 2, "bell", fill="#F9A8D4", opacity=0.8),
    *eye_set(53, 29, 2.4, "bell", jeye), *eye_set(67, 29, 2.4, "bell", jeye),
    p("M57 35 q3 2 6 0", "bell", stroke=jeye, sw=1.2),
    p("M50 24.5 l5 1.5", "bell", stroke=jeye, sw=1.3, when=["worried"]),
    p("M70 24.5 l-5 1.5", "bell", stroke=jeye, sw=1.3, when=["worried"]),
    p("M82 17 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "bell", fill="#7DD3FC", when=["worried"]),
    *lens(94, 46),
  ],
  "groupMotion": {"bell": {"sy": [0.07, 1.4, 0], "sx": [-0.04, 1.4, 0], "p": [60, 40]}},
  "poses": {
    "hiding":   {"tentacles": {"s": 0.45, "p": [60, 40]}, "bell": {"s": 0.85, "p": [60, 30]}},
    "sleeping": {"bell": {"ty": 2}, "tentacles": {"s": 0.85, "p": [60, 40]}},
    "curious":  {"bell": {"r": -8, "p": [60, 40]}},
  },
  "lines": {"click": ["Bloop!", "*wobbles*", "Wheee!", "*glows a little brighter*"],
            "typing": ["Ooh, typing!", "Pulse, pulse, pulse!", "Glowing with excitement."],
            "yikes": ["Eep!", "*shrinks*"]},
}

# ---- Octopus ------------------------------------------------------------
oeye, obody = "#1E1B4B", "#A78BFA"
arm = lambda d, x, y, ph: p(d, "arms", stroke=obody, sw=6, pivot=[x, y], rot=[12, 1.8, ph])
PETS["octopus"] = {
  "label": "Octopus", "name": "Inky", "flip": True, "floor": False, "speed": 0.8,
  "bob": [4, 3.0], "glow": "rgba(167,139,250,0.5)", "mouth": [78, 40], "head": [90, 12],
  "parts": [
    arm("M36 44 q-10 8 -6 18 q3 6 9 2", 38, 44, 0),
    arm("M46 47 q-6 10 -2 18 q3 5 8 1", 47, 47, 0.2),
    arm("M58 48 q0 10 4 17 q4 5 8 0", 58, 48, 0.4),
    arm("M70 47 q6 9 12 14 q6 3 8 -3", 70, 47, 0.6),
    arm("M80 43 q10 6 14 12 q3 6 -2 7", 80, 43, 0.8),
    p("M30 34 Q30 6 60 6 Q92 6 92 34 Q92 50 60 50 Q30 50 30 34Z", "head", fill=obody),
    c(42, 22, 3, "head", fill="#C4B5FD", opacity=0.8), c(51, 13, 2, "head", fill="#C4B5FD", opacity=0.8),
    c(38, 33, 2, "head", fill="#C4B5FD", opacity=0.8),
    *eye_set(69, 30, 2.4, "head", oeye, sclera="#F5F3FF"), *eye_set(82, 30, 2.4, "head", oeye, sclera="#F5F3FF"),
    p("M73 40 q3 2 6 0", "head", stroke=oeye, sw=1.4),
    p("M64 22.5 l8 2.5", "head", stroke=oeye, sw=1.4, when=["worried"]),
    p("M87 22.5 l-6 2.5", "head", stroke=oeye, sw=1.4, when=["worried"]),
    p("M92 12 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "head", fill="#7DD3FC", when=["worried"]),
    c(24, 46, 10, "ink", fill="#312E81", opacity=0.8, when=["hiding"]),
    c(36, 56, 12, "ink", fill="#312E81", opacity=0.8, when=["hiding"]),
    c(20, 60, 8, "ink", fill="#312E81", opacity=0.75, when=["hiding"]),
    c(48, 62, 9, "ink", fill="#312E81", opacity=0.7, when=["hiding"]),
    *lens(102, 44),
  ],
  "groupMotion": {"head": {"sy": [0.03, 1.8, 0], "p": [60, 50]}},
  "poses": {
    "hiding":   {"head": {"s": 0.8, "tx": -4, "ty": 6, "p": [60, 50]}, "arms": {"s": 0.7, "p": [60, 48]}},
    "sleeping": {"head": {"ty": 3}, "arms": {"s": 0.9, "p": [60, 48]}},
    "curious":  {"head": {"r": -8, "p": [60, 50]}},
  },
  "lines": {"click": ["Hi!", "*waves all eight arms*", "Eight arms, all yours.", "High five! And five more."],
            "yikes": ["*ink cloud*", "Hiding in my ink!"],
            "debugOn": ["Eight arms for bug hunting!", "Let's find it."]},
}

# ---- Crab ---------------------------------------------------------------
ceye, cshell, cdark = "#1C1917", "#FB923C", "#C2410C"
leg = lambda d, x, y, ph: p(d, "legs", stroke=cdark, sw=3.5, pivot=[x, y], rot=[14, 0.9, ph])
claw = lambda d, x, y, ph, **kw: p(d, "claws", pivot=[x, y], rot=[8, 1.2, ph], **kw)
PETS["crab"] = {
  "label": "Crab", "name": "Pinchy", "flip": False, "floor": True, "speed": 1.2,
  "bob": [1.5, 0.9], "glow": "rgba(251,146,60,0.45)", "mouth": [60, 22], "head": [80, 12],
  "parts": [
    leg("M40 52 l-12 8 l-2 7", 40, 52, 0), leg("M42 55 l-9 9 l1 6", 42, 55, 0.5), leg("M46 57 l-5 10", 46, 57, 0.25),
    leg("M80 52 l12 8 l2 7", 80, 52, 0.5), leg("M78 55 l9 9 l-1 6", 78, 55, 0), leg("M74 57 l5 10", 74, 57, 0.75),
    claw("M42 44 q-10 -4 -14 -12", 42, 44, 0, stroke=cshell, sw=4),
    claw("M28 33 q-11 -2 -13 -11 q6 2 10 6 q-2 -8 4 -12 q6 6 -1 17z", 42, 44, 0, fill="#F97316", stroke=cdark, sw=1),
    claw("M78 44 q10 -4 14 -12", 78, 44, 0.5, stroke=cshell, sw=4),
    claw("M92 33 q11 -2 13 -11 q-6 2 -10 6 q2 -8 -4 -12 q-6 6 1 17z", 78, 44, 0.5, fill="#F97316", stroke=cdark, sw=1),
    e(60, 48, 24, 13, "body", fill=cshell, stroke=cdark, sw=1.5),
    p("M44 52 q16 8 32 0", "body", stroke=cdark, sw=1.2, opacity=0.6),
    c(52, 42, 1.5, "body", fill=cdark, opacity=0.6), c(68, 42, 1.5, "body", fill=cdark, opacity=0.6), c(60, 39, 1.5, "body", fill=cdark, opacity=0.6),
    p("M56 50 q4 3 8 0", "body", stroke=ceye, sw=1.4),
    p("M54 37 l-2 -10", "eyes", stroke=cdark, sw=2.5), p("M66 37 l2 -10", "eyes", stroke=cdark, sw=2.5),
    c(52, 25, 4.2, "eyes", fill="#FFF7ED"), c(68, 25, 4.2, "eyes", fill="#FFF7ED"),
    *eye_set(53, 25, 2, "eyes", ceye, hl=False), *eye_set(69, 25, 2, "eyes", ceye, hl=False),
    p("M47 18.5 l6 2", "eyes", stroke=ceye, sw=1.4, when=["worried"]),
    p("M73 18.5 l-6 2", "eyes", stroke=ceye, sw=1.4, when=["worried"]),
    p("M78 14 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "eyes", fill="#7DD3FC", when=["worried"]),
    *lens(106, 20),
  ],
  "poses": {
    "hiding":   {"eyes": {"s": 0.55, "ty": 9, "p": [60, 37]}, "claws": {"s": 0.75, "p": [60, 44]}, "legs": {"s": 0.85, "p": [60, 52]}},
    "sleeping": {"eyes": {"s": 0.85, "ty": 5, "p": [60, 37]}},
    "curious":  {"eyes": {"ty": -3}},
  },
  "lines": {"click": ["Snip snip!", "*clack clack*", "Pinch!", "Sideways is the best way."],
            "taskOk": ["{task} passed! *clack clack*", "{task} worked!", "Snip! {task}: all good."],
            "yikes": ["*hides behind claws*", "Yikes!"]},
}

# ---- Pufferfish ---------------------------------------------------------
peye = "#1C1917"
spikes = []
for i in range(12):
    a = 2 * math.pi * i / 12
    bx, by = 60 + 19 * math.cos(a), 42 + 19 * math.sin(a)
    tx, ty = 60 + 27 * math.cos(a), 42 + 27 * math.sin(a)
    nx, ny = -math.sin(a) * 3, math.cos(a) * 3
    spikes.append(p(f"M{bx+nx:.1f} {by+ny:.1f} L{tx:.1f} {ty:.1f} L{bx-nx:.1f} {by-ny:.1f}Z", "body", fill="#F59E0B", when=["puffed"]))
PETS["pufferfish"] = {
  "label": "Pufferfish", "name": "Puff", "flip": True, "floor": False, "speed": 0.9,
  "bob": [3, 2.6], "glow": "rgba(253,230,138,0.45)", "mouth": [82, 44], "head": [88, 18],
  "parts": [
    p("M41 42 l-15 -11 q3 11 0 22z", "fins", fill="#FBBF24", pivot=[41, 42], rot=[15, 0.8, 0]),
    *spikes,
    c(60, 42, 20, "body", fill="#FDE68A"),
    p("M44 48 q16 14 32 0 q-16 6 -32 0z", "body", fill="#FEF3C7"),
    c(52, 31, 1.6, "body", fill="#D97706", opacity=0.7), c(58, 27, 1.4, "body", fill="#D97706", opacity=0.7),
    c(48, 37, 1.4, "body", fill="#D97706", opacity=0.7),
    *eye_set(70, 36, 3, "body", peye, sclera="#FFFFFF"),
    p("M64 28.5 l9 2.5", "body", stroke=peye, sw=1.4, when=["worried"]),
    c(80, 44, 2.2, "body", stroke=peye, sw=1.4),
    p("M50 44 q-9 2 -11 9 q7 0 11 -5z", "body", fill="#F59E0B", opacity=0.9, pivot=[50, 45], rot=[18, 0.7, 0.3]),
    p("M86 20 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    *lens(96, 56),
  ],
  "poses": {
    "worried":  {"body": {"s": 1.25, "p": [60, 42]}},
    "hiding":   {"body": {"s": 1.4, "p": [60, 42]}},
    "sleeping": {"body": {"ty": 2}},
    "curious":  {"body": {"r": -8, "p": [60, 42]}},
  },
  "lines": {"click": ["Puff!", "*puffs a little*", "Hi!", "Don't worry, I only puff for errors."],
            "worried": ["*puffs up*", "Uh oh.", "Hmm, an error."],
            "yikes": ["*PUFF*", "Too many errors!"],
            "fixed": ["*deflates* All clear!", "Phew. Fixed it!"]},
}

LINES = {
  "hello": ["Hi! I'm {name}."],
  "wake": ["Oh! I'm up.", "Back to work?", "Mm, what did I miss?"],
  "click": ["Hi!", "Hehe.", "Wheee!", "Keep going!"],
  "save": ["Saved!", "Nice save.", "Tucked away safely."],
  "savedWithErrors": ["Saved, but {errors} left."],
  "fixed": ["All clear!", "Fixed it!", "No more errors!", "Smooth sailing."],
  "worried": ["Uh oh.", "Hmm, an error.", "Something's off."],
  "yikes": ["Yikes!", "That's a lot of red."],
  "taskOk": ["{task} passed!", "{task} worked!", "{task}: all good."],
  "taskFail": ["{task} failed.", "{task} didn't work.", "Oof, {task}."],
  "debugOn": ["Bug hunting!", "Let's find it."],
  "debugOff": ["Done debugging.", "Bug hunt over."],
  "file": ["Ooh, a new file.", "What's in here?", "Looking around..."],
  "typing": ["Ooh, typing!", "Go go go!", "Full speed ahead."],
  "sleep": ["zzz..."],
}

print(json.dumps({"version": 1, "box": [120, 80], "lines": LINES, "pets": PETS}, indent=1))
