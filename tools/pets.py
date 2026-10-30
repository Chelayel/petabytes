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


# ---- Whale --------------------------------------------------------------
weye = "#1E3A8A"
PETS["whale"] = {
  "label": "Whale", "name": "Blue", "flip": True, "floor": False, "speed": 0.6,
  "bob": [4, 3.6], "glow": "rgba(96,165,250,0.45)", "mouth": [104, 48], "head": [96, 22],
  "parts": [
    p("M20 42 Q8 30 3 21 Q11 25 17 33 Q13 21 15 13 Q21 25 23 38Z", "tail", fill="#3B82F6", pivot=[21, 40], rot=[12, 1.6, 0]),
    p("M14 44 Q14 18 52 16 Q92 14 104 36 Q110 48 100 56 Q80 66 46 64 Q16 62 14 44Z", "body", fill="#60A5FA"),
    p("M30 56 Q60 66 98 54 Q86 63 48 63 Q36 62 30 56Z", "body", fill="#DBEAFE"),
    p("M44 59 l2 4 M54 60 l1.5 4 M64 60 l1 3.6 M74 59 l0.5 3.4", "body", stroke="#93C5FD", sw=1.2),
    c(94, 46, 2.2, "body", fill="#F9A8D4", opacity=0.8),
    *eye_set(88, 40, 2.6, "body", weye),
    p("M92 49 q5 3 10 -1", "body", stroke=weye, sw=1.4),
    p("M84 33 l8 2", "body", stroke=weye, sw=1.4, when=["worried"]),
    p("M102 26 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    p("M70 15 q-6 -6 -10 -6 M70 15 q6 -6 10 -6 M70 15 l0 -9", "spout", stroke="#BFDBFE", sw=2.2, when=["happy"]),
    p("M60 56 q-4 10 -14 14 q4 -8 6 -16z", "fins", fill="#3B82F6", pivot=[58, 56], rot=[15, 1.6, 0.3]),
    *lens(112, 56),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.9, "ty": 6, "p": [60, 40]}, "tail": {"s": 0.8, "ty": 6, "p": [20, 40]}, "fins": {"ty": 6}},
    "sleeping": {"body": {"ty": 2}, "tail": {"ty": 2}, "fins": {"ty": 2}},
    "curious":  {"body": {"r": -5, "p": [60, 40]}},
  },
  "lines": {"click": ["Hello there!", "*whale song*", "Big hugs!", "Thar she blows!"],
            "pet": ["*happy whale song*", "Aww. *spouts*"], "fixed": ["*spouts* All clear!", "Fixed it! Whale done."]},
}

# ---- Clownfish ----------------------------------------------------------
fdark = "#1C1917"
PETS["clownfish"] = {
  "label": "Clownfish", "name": "Clem", "flip": True, "floor": False, "speed": 1.3,
  "bob": [3, 1.8], "glow": "rgba(251,146,60,0.45)", "mouth": [87, 44], "head": [82, 22],
  "parts": [
    p("M36 40 l-13 -12 q4 12 0 24z", "fins", fill="#FB923C", stroke=fdark, sw=1.2, pivot=[36, 40], rot=[18, 0.6, 0]),
    p("M50 26 q8 -10 18 -2 q-8 -1 -18 2z", "body", fill="#FB923C", stroke=fdark, sw=1.2),
    e(60, 40, 26, 15, "body", fill="#FB923C", stroke=fdark, sw=1.2),
    p("M47 26.5 Q51 40 47 53.5 Q43 53 41 51 Q45 40 41 29 Q44 27 47 26.5Z", "body", fill="#FFFFFF", stroke=fdark, sw=1.1),
    p("M68 25.4 Q73 40 68 54.6 Q64 55 61 54.6 Q65 40 61 25.4 Q64 25 68 25.4Z", "body", fill="#FFFFFF", stroke=fdark, sw=1.1),
    p("M80 29 Q84 40 80 51 Q78 50.6 76.5 50 Q79.5 40 76.5 30 Q78 29.4 80 29Z", "body", fill="#FFFFFF", stroke=fdark, sw=1.1),
    *eye_set(79, 36, 2.2, "body", fdark, sclera="#FFFFFF"),
    p("M83 44 q2 1.6 3.6 0", "body", stroke=fdark, sw=1.2),
    p("M74 29.5 l7 2", "body", stroke=fdark, sw=1.3, when=["worried"]),
    p("M88 22 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    p("M62 46 q-2 8 -8 10 q2 -6 2 -10z", "body", fill="#FB923C", stroke=fdark, sw=1, pivot=[62, 46], rot=[20, 0.5, 0.3]),
    *lens(96, 50),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.85, "ty": 4, "p": [60, 40]}, "fins": {"s": 0.85, "ty": 4, "p": [36, 40]}},
    "sleeping": {"body": {"ty": 2}, "fins": {"ty": 2}},
    "curious":  {"body": {"r": -8, "p": [60, 40]}},
  },
  "lines": {"click": ["Hi hi hi!", "*zooms*", "Just keep coding!", "Wheee!"],
            "pet": ["*wiggles*", "Hehe!"], "typing": ["Zoom zoom!", "Faster, faster!"]},
}

# ---- Seahorse -----------------------------------------------------------
hpink, hdark, heye = "#F9A8D4", "#EC4899", "#500724"
PETS["seahorse"] = {
  "label": "Seahorse", "name": "Sandy", "flip": True, "floor": False, "speed": 0.5,
  "bob": [6, 2.8], "glow": "rgba(249,168,212,0.5)", "mouth": [83, 20], "head": [74, 6],
  "parts": [
    p("M52 40 q-9 2 -11 9 q7 0 11 -4z", "fins", fill="#FBCFE8", stroke=hdark, sw=1, pivot=[52, 42], rot=[25, 0.35, 0]),
    p("M57 55 Q60 67 52 71 Q44 73 45 65 Q47 60 52 62", "body", stroke=hpink, sw=6),
    p("M56 26 Q75 30 70 44 Q66 55 58 56 Q50 54 52 42 Q50 32 56 26Z", "body", fill=hpink, stroke=hdark, sw=1.2),
    p("M58 32 q6 2 9 0 M57 38 q7 2 10 0 M56 44 q6 2 9 0 M56 50 q5 1.6 7 0", "body", stroke=hdark, sw=1, opacity=0.6),
    p("M58 16 l2 -6 l2 5 l3 -5 l1 6", "body", fill=hdark),
    c(64, 22, 8.5, "body", fill=hpink, stroke=hdark, sw=1.2),
    p("M71 19.5 l12 -1 l0 5 l-11 1z", "body", fill=hpink, stroke=hdark, sw=1.1),
    *eye_set(65, 20, 2.2, "body", heye),
    c(60, 25, 1.8, "body", fill="#FDA4AF", opacity=0.8),
    p("M61 14.5 l7 1.6", "body", stroke=heye, sw=1.3, when=["worried"]),
    p("M76 8 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    *lens(84, 40),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.85, "ty": 4, "p": [60, 50]}, "fins": {"s": 0.6, "p": [52, 42]}},
    "sleeping": {"body": {"r": 8, "p": [60, 50]}},
    "curious":  {"body": {"r": -6, "p": [60, 50]}},
  },
  "lines": {"click": ["Hello, hello!", "*bobs politely*", "Neigh! Just kidding."],
            "pet": ["*curls tail happily*", "Aww, thank you!"]},
}

# ---- Shark --------------------------------------------------------------
sgray, sdark, seye = "#94A3B8", "#64748B", "#0F172A"
PETS["shark"] = {
  "label": "Shark", "name": "Finn", "flip": True, "floor": False, "speed": 1.1,
  "bob": [3, 3.0], "glow": "rgba(148,163,184,0.45)", "mouth": [110, 46], "head": [100, 20],
  "parts": [
    p("M16 42 L5 25 Q13 32 19 39 Q13 47 5 57 Z", "tail", fill=sdark, pivot=[17, 42], rot=[12, 1.0, 0]),
    p("M56 27 q6 -18 18 -20 q-4 12 -2 20z", "body", fill=sdark),
    p("M10 42 Q30 26 70 26 Q100 28 112 42 Q100 54 70 56 Q30 56 10 42Z", "body", fill=sgray),
    p("M30 48 Q70 60 108 44 Q100 54 70 56 Q40 56 30 48Z", "body", fill="#F1F5F9"),
    p("M84 35 q-2 5 0 10 M88 35 q-2 5 0 10 M92 36 q-2 4 0 8", "body", stroke=sdark, sw=1.2),
    *eye_set(99, 36, 2.4, "body", seye),
    p("M96 46 q6 4 12 0", "body", stroke=seye, sw=1.4),
    p("M99 47.2 l1.5 2.2 l1.5 -2 M103 47.8 l1.5 2.2 l1.5 -2", "body", fill="#FFFFFF"),
    p("M95 30.5 l8 2", "body", stroke=seye, sw=1.4, when=["worried"]),
    p("M106 22 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    p("M62 50 q-6 10 -16 12 q6 -6 8 -12z", "fins", fill=sdark, pivot=[60, 50], rot=[12, 1.0, 0.3]),
    *lens(114, 56),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.88, "ty": 5, "p": [60, 42]}, "tail": {"s": 0.8, "ty": 5, "p": [17, 42]}, "fins": {"ty": 5}},
    "sleeping": {"body": {"ty": 2}, "tail": {"ty": 2}, "fins": {"ty": 2}},
    "curious":  {"body": {"r": -6, "p": [60, 42]}},
  },
  "lines": {"click": ["Don't worry, I'm vegetarian.", "Fin-tastic!", "*friendly shark noises*", "Chomp! Just kidding."],
            "pet": ["*happy fin wiggle*", "Aww, you're not scared of me!"],
            "yikes": ["Even sharks get scared sometimes.", "*hides behind a fin*"],
            "eatCurly": ["Chomp! Curly braces.", "Mmm, crunchy braces."]},
}


# ---- Dolphin ------------------------------------------------------------
dgray, ddark, deye = "#7C9CC0", "#5B7BA0", "#0F172A"
PETS["dolphin"] = {
  "label": "Dolphin", "name": "Splash", "flip": True, "floor": False, "speed": 1.4,
  "bob": [4, 2.2], "glow": "rgba(124,156,192,0.5)", "mouth": [114, 44], "head": [98, 22],
  "parts": [
    p("M15 44 L3 33 Q9 36 15 41 Q9 47 3 55 Z", "tail", fill=ddark, pivot=[15, 44], rot=[14, 0.9, 0]),
    p("M58 29 q4 -14 14 -18 q-2 10 0 18z", "body", fill=ddark),
    p("M10 44 Q20 30 50 28 Q80 26 98 36 Q106 40 117 43 Q107 46 98 47 Q80 58 48 56 Q24 54 10 44Z", "body", fill=dgray),
    p("M30 50 Q62 60 100 46 Q84 56 50 56 Q36 55 30 50Z", "body", fill="#E2E8F0"),
    *eye_set(92, 38, 2.4, "body", deye),
    p("M101 45 q6 2.5 12 -0.5", "body", stroke=deye, sw=1.3),
    c(96, 43, 1.8, "body", fill="#F9A8D4", opacity=0.7),
    p("M87 32 l8 2", "body", stroke=deye, sw=1.4, when=["worried"]),
    p("M104 24 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    p("M64 50 q-4 10 -14 12 q4 -6 6 -12z", "fins", fill=ddark, pivot=[62, 50], rot=[14, 0.9, 0.3]),
    *lens(116, 56),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.9, "ty": 5, "p": [60, 42]}, "tail": {"s": 0.85, "ty": 5, "p": [15, 44]}, "fins": {"ty": 5}},
    "sleeping": {"body": {"ty": 2}, "tail": {"ty": 2}, "fins": {"ty": 2}},
    "curious":  {"body": {"r": -6, "p": [60, 42]}},
  },
  "lines": {"click": ["Ee-ee-ee!", "*does a flip*", "Splash!", "Wanna race?"],
            "pet": ["*happy clicks*", "Ee-ee! Thank you!"], "fixed": ["*leaps* All clear!", "Fixed it! Ee-ee!"],
            "run": ["Here we go! *splash*", "It's alive! Ee-ee!"]},
}

# ---- Angelfish ----------------------------------------------------------
aeye, astripe = "#0F172A", "#334155"
PETS["angelfish"] = {
  "label": "Angelfish", "name": "Angie", "flip": True, "floor": False, "speed": 0.7,
  "bob": [4, 3.0], "glow": "rgba(251,191,36,0.4)", "mouth": [87, 40], "head": [80, 6],
  "parts": [
    p("M41 40 l-11 -9 q3 9 0 18z", "fins", fill="#FBBF24", pivot=[41, 40], rot=[16, 0.8, 0]),
    p("M58 16 Q50 6 43 1", "fins", stroke="#FBBF24", sw=2.2, pivot=[58, 16], rot=[8, 1.6, 0.2]),
    p("M58 64 Q50 74 43 79", "fins", stroke="#FBBF24", sw=2.2, pivot=[58, 64], rot=[8, 1.6, 0.7]),
    p("M40 40 Q56 10 66 6 Q70 24 87 40 Q70 56 66 74 Q56 70 40 40Z", "body", fill="#E2E8F0", stroke="#FBBF24", sw=1.4),
    p("M54 20 Q58 40 54 62 M64 12 Q68 40 64 70", "body", stroke=astripe, sw=3.2, opacity=0.85),
    p("M74 28 Q76 40 74 52", "body", stroke=astripe, sw=2.2, opacity=0.7),
    *eye_set(78, 36, 2.6, "body", aeye, sclera="#FFFFFF"),
    p("M84 40.5 q2 1.4 3.4 0", "body", stroke=aeye, sw=1.2),
    p("M73 29.5 l7 2", "body", stroke=aeye, sw=1.3, when=["worried"]),
    p("M88 22 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    p("M66 46 q-3 7 -8 9 q2 -5 2 -9z", "body", fill="#FDE68A", pivot=[66, 46], rot=[20, 0.6, 0.3]),
    *lens(96, 54),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.85, "ty": 3, "p": [62, 40]}, "fins": {"s": 0.8, "ty": 3, "p": [50, 40]}},
    "sleeping": {"body": {"r": 6, "p": [62, 40]}, "fins": {"r": 6, "p": [62, 40]}},
    "curious":  {"body": {"r": -8, "p": [62, 40]}},
  },
  "lines": {"click": ["Hello, darling.", "*glides gracefully*", "Aren't my fins lovely?"],
            "pet": ["*flutters fins*", "You're an angel too."]},
}

# ---- Blue tang ----------------------------------------------------------
teye = "#0F172A"
PETS["tang"] = {
  "label": "Blue tang", "name": "Indigo", "flip": True, "floor": False, "speed": 1.1,
  "bob": [3, 2.0], "glow": "rgba(37,99,235,0.45)", "mouth": [89, 42], "head": [84, 20],
  "parts": [
    p("M33 40 l-12 -11 q4 11 0 22z", "fins", fill="#FACC15", pivot=[33, 40], rot=[16, 0.7, 0]),
    e(60, 40, 28, 16, "body", fill="#2563EB", stroke="#1E3A8A", sw=1.2),
    p("M43 26 Q60 18 78 26", "body", stroke="#1E3A8A", sw=2),
    p("M42 34 Q56 24 74 30 Q66 36 54 36 Q60 44 74 45 Q60 51 44 44 Q38 40 42 34Z", "body", fill="#0F172A"),
    *eye_set(79, 36, 2.4, "body", teye, sclera="#FFFFFF"),
    p("M85 42 q2 1.5 3.5 0", "body", stroke=teye, sw=1.2),
    p("M74 29.5 l7 2", "body", stroke=teye, sw=1.3, when=["worried"]),
    p("M90 22 q-2.5 4.5 0 5.5 q2.5 -1 0 -5.5z", "body", fill="#7DD3FC", when=["worried"]),
    p("M65 46 q-2 7 -7 9 q2 -5 1 -9z", "body", fill="#93C5FD", pivot=[65, 46], rot=[20, 0.55, 0.3]),
    *lens(98, 54),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.85, "ty": 3, "p": [60, 40]}, "fins": {"s": 0.85, "ty": 3, "p": [33, 40]}},
    "sleeping": {"body": {"ty": 2}, "fins": {"ty": 2}},
    "curious":  {"body": {"r": -8, "p": [60, 40]}},
  },
  "lines": {"click": ["Hi! Wait, what was I doing?", "*swims in a happy circle*", "Hello, friend!"],
            "pet": ["*wiggles*", "Hehe, I forgot what I was saying. Hi!"],
            "file": ["Ooh, a new file! Or have I seen it?", "Where are we again?"]},
}

# ---- Home: pets that walk instead of swim ---------------------------------
# They live on the floor (or on top of the Mac's Dock) and get lines that don't mention water.
HOME_LINES = {
  "fixed": ["All clear!", "Fixed it!", "No more errors!", "Good job!"],
  "longSession": ["You've been at it a while. Stretch break?", "Walk break? I'll come.", "Blink a few times. Eyes need breaks too."],
  "lateNight": ["It's late. I'm sleepy.", "Coding past midnight? I'll keep you company.", "Night shift, huh?"],
  "morning": ["Good morning!", "Morning! Breakfast first?", "Rise and shine!"],
  "music": ["Ooh, music!", "*dances*", "Is this my song?"],
  "hot": ["It's getting hot in here.", "Your Mac's working hard.", "*pants*"],
  "file": ["Ooh, a new file.", "*sniffs around*", "What's in here?"],
}

def leg_stroke(x, y, dx, color, sw, ph, period=0.8):
    return p(f"M{x} {y} l{dx} 20", "legs", stroke=color, sw=sw, pivot=[x, y], rot=[14, period, ph])

# ---- Golden retriever ---------------------------------------------------
deye, gold, gold_dark, gold_light = "#2B1B10", "#E8A84A", "#C98A2B", "#F3C77A"
PETS["retriever"] = {
  "label": "Golden retriever", "name": "Biscuit", "set": "home", "flip": True, "floor": True, "speed": 1.1,
  "bob": [1.5, 0.5], "glow": "rgba(232,168,74,0.45)", "mouth": [111, 38], "head": [92, 16],
  "parts": [
    p("M34 40 q-12 -4 -18 -16 q8 3 18 9z", "tail", fill=gold_dark, pivot=[34, 40], rot=[22, 0.45, 0]),
    leg_stroke(40, 50, -2, gold_dark, 7, 0.5), leg_stroke(82, 50, 2, gold_dark, 7, 0),
    e(62, 44, 28, 13, "body", fill=gold),
    p("M78 36 q10 2 12 14 q-6 4 -12 2z", "body", fill=gold_light, opacity=0.8),
    leg_stroke(46, 50, 1, gold, 7, 0), leg_stroke(88, 50, -1, gold, 7, 0.5),
    c(92, 30, 13, "face", fill="#EDB458"),
    e(104, 35, 9, 6.5, "face", fill=gold_light),
    c(112, 33, 2.6, "face", fill=deye),
    p("M86 20 q-9 2 -9 15 q5 5 9 -1 q2 -7 0 -14z", "face", fill=gold_dark, pivot=[86, 21], rot=[8, 1.2, 0]),
    *eye_set(96, 27, 2.3, "face", deye),
    p("M104 39.5 q3.5 2.5 7 -0.5", "face", stroke=deye, sw=1.3),
    p("M106 40.5 q1 6 4 5 q2 -2 0 -5.5z", "face", fill="#F472B6", when=["eyesHappy"]),
    p("M92 22 l7 1.5", "face", stroke=deye, sw=1.4, when=["worried"]),
    sweat(84, 15),
    *lens(116, 50),
  ],
  "poses": {
    "hiding":   {"face": {"tx": -6, "ty": 7, "s": 0.85, "p": [90, 38]}, "tail": {"s": 0.5, "p": [34, 40]}},
    "sleeping": {"body": {"ty": 9}, "face": {"tx": -2, "ty": 12, "r": 10, "p": [88, 38]}, "legs": {"s": 0.35, "p": [64, 70]}, "tail": {"ty": 10}},
    "curious":  {"face": {"r": -14, "p": [90, 36]}},
  },
  "lines": {"click": ["Woof!", "*wags*", "Ball? Did someone say ball?", "Best day ever!"],
            "pet": ["*happy tail thumps*", "Good human!", "More scritches please."],
            "yikes": ["*whimpers*", "I'll hide under the desk."],
            "fixed": ["Good job! Good job!", "All clear! Treat?"],
            "eatCurly": ["Crunchy! Like kibble.", "Mmm, curly braces!"]},
}

# ---- German Spitz -------------------------------------------------------
def fluff(cx, cy, rx, ry, n=14, puff=1.2):
    """A fluffy, scalloped ellipse: n tufts bulging out between points on the ellipse."""
    pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        nx, ny = pts[(i + 1) % n]
        d += f" Q{cx + rx * puff * math.cos(a):.1f} {cy + ry * puff * math.sin(a):.1f} {nx:.1f} {ny:.1f}"
    return d + "Z"

# Loopee is a real dog: white and very fluffy, with a big mane, pink-lined ears and a pinkish-brown nose.
seye, snow, snow_line, snow_shade, nose = "#2B1A12", "#FFFFFF", "#CBD5E1", "#F1F5F9", "#B77B7B"
def short_leg(x, y, dx, color, ph):
    """A Spitz's short, fluffy leg: a soft outline under a white stroke, paddling quickly."""
    d = f"M{x} {y} l{dx} 13"
    return [p(d, "legs", stroke=snow_line, sw=7.5, pivot=[x, y], rot=[16, 0.5, ph]),
            p(d, "legs", stroke=color, sw=5, pivot=[x, y], rot=[16, 0.5, ph])]
PETS["spitz"] = {
  "label": "German Spitz", "name": "Loopee", "set": "home", "flip": True, "floor": True, "speed": 1.2,
  "bob": [1.5, 0.4], "glow": "rgba(226,232,240,0.5)", "mouth": [103, 41], "head": [86, 16],
  "parts": [
    *short_leg(48, 58, -1, snow_shade, 0.5), *short_leg(73, 58, 1, snow_shade, 0),
    # The plumed tail, curled up over the back.
    p(fluff(40, 32, 13, 11, 12, 1.25), "tail", fill=snow, stroke=snow_line, sw=1.4, pivot=[44, 44], rot=[12, 0.5, 0]),
    p(fluff(58, 52, 22, 13, 16, 1.18), "body", fill=snow, stroke=snow_line, sw=1.4),
    *short_leg(54, 60, 1, snow, 0), *short_leg(67, 60, -1, snow, 0.5),
    # Her mane: a big ruff of fur around the neck and chest, framing the face.
    p(fluff(84, 41, 17, 15, 15, 1.22), "face", fill=snow, stroke=snow_line, sw=1.4),
    # Upright, pointed ears with pink insides, then the head and a fox-like muzzle.
    p("M75 25 l3 -14 l9 10z", "face", fill=snow, stroke=snow_line, sw=1.3), p("M78 21 l1.5 -7 l4.5 4.5z", "face", fill="#F4A3B5"),
    p("M89 21 l7 -11 l2 13z", "face", fill=snow, stroke=snow_line, sw=1.3), p("M92 19 l3.5 -6 l1 6.5z", "face", fill="#F4A3B5"),
    p(fluff(86, 32, 13, 12, 13, 1.18), "face", fill=snow, stroke=snow_line, sw=1.4),
    p("M95 33 q8 1 10 5 q-3 4 -11 3z", "face", fill=snow, stroke=snow_line, sw=1.2),
    c(104.5, 37.5, 2.3, "face", fill=nose),
    *eye_set(86, 30, 2.4, "face", seye), *eye_set(95, 30, 2.2, "face", seye),
    p("M99 41 q2 2 4 0", "face", stroke=nose, sw=1.1),
    p("M100 43 q1 5 3 4 q1.5 -2 0 -4.5z", "face", fill="#F472B6", when=["eyesHappy"]),
    c(82, 37, 2.4, "face", fill="#FBCFE8", opacity=0.8),
    p("M81 25.5 l6 1.5 M97 25.5 l-5 1.5", "face", stroke=seye, sw=1.3, when=["worried"]),
    sweat(76, 18),
    *lens(116, 50),
  ],
  "poses": {
    "hiding":   {"face": {"tx": -6, "ty": 6, "s": 0.85, "p": [84, 40]}, "tail": {"s": 0.7, "p": [44, 40]}},
    "sleeping": {"body": {"ty": 8}, "face": {"tx": -2, "ty": 11, "r": 10, "p": [84, 40]}, "legs": {"s": 0.3, "p": [60, 74]}, "tail": {"ty": 8}},
    "curious":  {"face": {"r": -14, "p": [84, 40]}},
  },
  "lines": {"click": ["Yip!", "Floof incoming!", "I'm small but mighty.", "*zoomies*"],
            "pet": ["*tail-wag tornado*", "More! More!", "*happy little yips*"],
            "yikes": ["*yips at the error*", "Yip yip! Go away, bug!"],
            "typing": ["*zoomies around the keyboard*", "Yip! Typing!", "Go go go!"],
            "feed": ["A snack? For me?!", "Yip! Food!"],
            "eatCurly": ["Crunchy! Yip!", "Mmm, curly braces!"],
            "fixed": ["Yip yip! You did it!", "All clear! Zoomies time."],
            "hungry": ["*puppy eyes* Snack?", "I'm small, but I'm hungry."],
            "file": ["*sniff sniff*", "Ooh, a new file."]},
}

# ---- Cat ----------------------------------------------------------------
keye, grey, grey_dark = "#1F2937", "#9CA3AF", "#6B7280"
PETS["cat"] = {
  "label": "Cat", "name": "Byte", "set": "home", "flip": True, "floor": True, "speed": 0.8,
  "bob": [1, 0.6], "glow": "rgba(190,242,100,0.35)", "mouth": [93, 38], "head": [90, 16],
  "parts": [
    p("M34 44 q-14 -2 -14 -16 q0 -10 8 -13", "tail", stroke=grey_dark, sw=5, pivot=[34, 44], rot=[10, 2.2, 0]),
    leg_stroke(40, 50, -1, grey_dark, 5, 0.5, 1.0), leg_stroke(78, 50, 1, grey_dark, 5, 0, 1.0),
    e(60, 45, 26, 10, "body", fill=grey),
    p("M48 36 q2 5 0 9 M56 35 q2 5 0 10 M64 35 q2 5 0 10", "body", stroke=grey_dark, sw=2, opacity=0.8),
    leg_stroke(45, 50, 1, grey, 5, 0, 1.0), leg_stroke(84, 50, -1, grey, 5, 0.5, 1.0),
    p("M80 26 l2 -13 l9 8z", "face", fill=grey), p("M82.5 22 l1 -6 l4 4z", "face", fill="#F9A8D4"),
    p("M94 21 l7 -10 l2 13z", "face", fill=grey), p("M97 19 l3 -5 l1 6z", "face", fill="#F9A8D4"),
    c(91, 32, 12, "face", fill="#A3AAB5"),
    p("M86 22 l1.5 4 M91 21 l0 4.5 M96 22 l-1.5 4", "face", stroke=grey_dark, sw=1.5),
    *eye_set(87, 31, 2.2, "face", keye, sclera="#BEF264"), *eye_set(96, 31, 2.2, "face", keye, sclera="#BEF264"),
    p("M90.5 35.5 h3.5 l-1.75 2z", "face", fill="#F472B6"),
    p("M92.25 37.5 q-1.5 2 -3 1 M92.25 37.5 q1.5 2 3 1", "face", stroke=keye, sw=1),
    p("M84 36 l-9 -1.5 M84 38.5 l-9 2 M100 36 l9 -1.5 M100 38.5 l9 2", "face", stroke="#E5E7EB", sw=0.8),
    p("M83 26 l6 2 M100 26 l-6 2", "face", stroke=keye, sw=1.3, when=["worried"]),
    sweat(104, 22),
    *lens(115, 50),
  ],
  "poses": {
    "hiding":   {"face": {"ty": 6, "s": 0.9, "p": [91, 40]}, "body": {"ty": 4}, "legs": {"s": 0.6, "p": [62, 70]}, "tail": {"s": 0.7, "p": [34, 44]}},
    "sleeping": {"body": {"ty": 11}, "face": {"tx": -4, "ty": 14, "r": 14, "p": [90, 40]}, "legs": {"s": 0.3, "p": [62, 70]}, "tail": {"ty": 10}},
    "curious":  {"face": {"r": -10, "p": [91, 40]}},
  },
  "lines": {"click": ["Mrrp?", "*purrs*", "Meow.", "I'll allow it."],
            "pet": ["*purrs loudly*", "*headbutts your cursor*", "Okay, that's enough. One more."],
            "yikes": ["*hisses*", "*knocks errors off the desk*"],
            "save": ["Saved. I'm unimpressed, but saved.", "Purrfect.", "Saved!"],
            "eatSemicolon": ["A semicolon. Acceptable.", "*crunch* Fine."],
            "typing": ["*sits on your keyboard*", "Type faster, human.", "Ooh, typing!"]},
}

# ---- Bunny --------------------------------------------------------------
beye, fur, fur_line, pink = "#292524", "#F5F5F4", "#D6D3D1", "#FBCFE8"
PETS["bunny"] = {
  "label": "Bunny", "name": "Clover", "set": "home", "flip": True, "floor": True, "speed": 0.9,
  "bob": [3, 0.45], "glow": "rgba(251,207,232,0.45)", "mouth": [89, 44], "head": [78, 14],
  "parts": [
    c(39, 46, 5.5, "body", fill="#FFFFFF", stroke=fur_line, sw=1),
    e(48, 62, 10, 5, "legs", fill="#E7E5E4", stroke=fur_line, sw=1, pivot=[52, 60], rot=[10, 0.45, 0]),
    e(58, 50, 20, 15, "body", fill=fur, stroke=fur_line, sw=1),
    p("M70 56 l2 11", "legs", stroke="#E7E5E4", sw=5, pivot=[70, 56], rot=[12, 0.45, 0.5]),
    p("M74 31 q-4 -18 2 -24 q5 6 3 24z", "ears", fill=fur, stroke=fur_line, sw=1, pivot=[76, 31], rot=[4, 1.6, 0]),
    p("M75.5 29 q-2 -12 1 -18 q2.5 5 1.5 18z", "ears", fill=pink, pivot=[76, 31], rot=[4, 1.6, 0]),
    p("M80 31 q2 -18 9 -22 q3 7 -5 23z", "ears", fill=fur, stroke=fur_line, sw=1, pivot=[80, 31], rot=[5, 1.6, 0.4]),
    p("M81.5 29.5 q2 -12 6 -16 q1 5 -4 16z", "ears", fill=pink, pivot=[80, 31], rot=[5, 1.6, 0.4]),
    c(78, 40, 11, "face", fill=fur, stroke=fur_line, sw=1),
    *eye_set(82, 38, 2.2, "face", beye),
    c(88.5, 42, 1.5, "face", fill="#F472B6"),
    p("M86 45 q1.5 1.5 3 0", "face", stroke=beye, sw=1),
    c(83, 44, 2, "face", fill=pink, opacity=0.7),
    p("M79 33.5 l5 1.5", "face", stroke=beye, sw=1.3, when=["worried"]),
    sweat(70, 30),
    *lens(100, 52),
  ],
  "poses": {
    "hiding":   {"ears": {"r": -55, "p": [77, 32]}, "face": {"s": 0.9, "ty": 4, "p": [78, 46]}},
    "sleeping": {"ears": {"r": -65, "ty": 4, "p": [77, 32]}, "face": {"ty": 5, "p": [78, 46]}, "legs": {"s": 0.8, "p": [60, 66]}},
    "curious":  {"face": {"r": -10, "p": [78, 46]}, "ears": {"r": -6, "p": [77, 32]}},
  },
  "lines": {"click": ["*binky!*", "*nose wiggle*", "Hop hop!", "Hi!"],
            "pet": ["*happy nose wiggles*", "*flops over*"],
            "yikes": ["*thumps foot*", "*freezes*"],
            "eatParens": ["Parentheses! Like little carrots.", "(Crunch.)"]},
}

# ---- Hamster ------------------------------------------------------------
heye, ham, ham_dark = "#1C1917", "#E9A15B", "#C77E3A"
PETS["hamster"] = {
  "label": "Hamster", "name": "Nugget", "set": "home", "flip": True, "floor": True, "speed": 1.4,
  "bob": [1.2, 0.3], "glow": "rgba(233,161,91,0.45)", "mouth": [82, 52], "head": [72, 26],
  "parts": [
    e(50, 67, 4.5, 2.5, "legs", fill=pink, pivot=[50, 64], rot=[18, 0.3, 0]),
    e(70, 67, 4.5, 2.5, "legs", fill=pink, pivot=[70, 64], rot=[18, 0.3, 0.5]),
    c(64, 34, 5, "body", fill=ham), c(64, 34, 2.8, "body", fill=pink),
    e(58, 50, 23, 17, "body", fill=ham),
    e(64, 57, 15, 9, "body", fill="#FFF7ED"),
    p("M44 40 q6 -4 12 -2", "body", stroke=ham_dark, sw=1.5, opacity=0.6),
    c(76, 37, 4.5, "face", fill=ham), c(76, 37, 2.4, "face", fill=pink),
    *eye_set(75, 46, 2.3, "face", heye),
    e(78, 53, 6.5, 5, "face", fill="#F7B98B", when=["eyesHappy"]),
    c(81.5, 49.5, 1.4, "face", fill="#F472B6"),
    p("M79.5 52.5 q2 1.5 4 0", "face", stroke=heye, sw=1),
    p("M84 50 l7 -1.5 M84 52 l7 1.5", "face", stroke="#FFF7ED", sw=0.8),
    p("M72 41.5 l5 1.5", "face", stroke=heye, sw=1.3, when=["worried"]),
    sweat(68, 36),
    *lens(96, 56),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.85, "p": [60, 68]}, "face": {"s": 0.8, "tx": -4, "ty": 4, "p": [60, 68]}},
    "sleeping": {"body": {"s": 0.95, "p": [60, 68]}, "face": {"tx": -3, "ty": 3, "p": [60, 68]}},
    "curious":  {"body": {"ty": -3}, "face": {"ty": -4, "r": -8, "p": [76, 50]}},
  },
  "lines": {"click": ["Squeak!", "*stuffs cheeks*", "Wheel time?", "Hi!"],
            "pet": ["*happy squeaks*", "*cheeks puff up*"],
            "yikes": ["*hides in bedding*", "Squeak!"],
            "full": ["My cheeks are full.", "*saving the rest for later*"],
            "typing": ["Running on my wheel!", "Go go go!", "Full speed ahead."]},
}

# ---- Snacks: food with feet ------------------------------------------------

# ---- Burger -------------------------------------------------------------
ink, bun, bun_dark, seed = "#2B1D12", "#F7A928", "#D9861A", "#FFF3D6"
PETS["burger"] = {
  "label": "Burger", "name": "Patty", "set": "snacks", "flip": True, "floor": True, "speed": 1.0,
  "bob": [1.5, 0.45], "glow": "rgba(247,169,40,0.45)", "mouth": [68, 34], "head": [62, 12],
  "parts": [
    leg_stroke(48, 60, -2, bun_dark, 6.5, 0, 0.7), leg_stroke(72, 60, 2, bun_dark, 6.5, 0.5, 0.7),
    p("M30 56 Q30 66 60 66 Q90 66 90 56 Z", "body", fill=bun, stroke=ink, sw=1.6),
    p("M28 50 l7 7 l7 -6 l8 8 l7 -7 l8 8 l7 -7 l8 7 l7 -6 l5 3 l-2 -7 z", "fill", fill="#FDE047", stroke=ink, sw=1.2),
    e(60, 50, 32, 5.5, "fill", fill="#7C4A2D", stroke=ink, sw=1.4),
    e(44, 46, 9, 3.2, "fill", fill="#EF4444", stroke=ink, sw=1.2), e(74, 46, 10, 3.2, "fill", fill="#EF4444", stroke=ink, sw=1.2),
    p("M93 41 L27 41 L27 44" + " q4 6 8 0" * 8 + " L93 44 Z", "fill", fill="#4ADE80", stroke=ink, sw=1.2),
    p("M27 42 Q27 10 60 10 Q93 10 93 42 Z", "top", fill=bun, stroke=ink, sw=1.6),
    p("M33 34 Q36 18 52 14", "top", stroke="#FFD27A", sw=2.2, opacity=0.8),
    e(42, 22, 1.8, 1, "top", fill=seed), e(50, 16, 1.8, 1, "top", fill=seed), e(76, 18, 1.8, 1, "top", fill=seed),
    e(84, 26, 1.8, 1, "top", fill=seed), e(38, 30, 1.8, 1, "top", fill=seed),
    *eye_set(57, 27, 2.6, "top", ink, sclera="#FFFFFF"), *eye_set(70, 27, 2.6, "top", ink, sclera="#FFFFFF"),
    p("M63 34 q4 3.5 8 0", "top", stroke=ink, sw=1.5),
    p("M53 21 l6 1.5 M74 21 l-6 1.5", "top", stroke=ink, sw=1.4, when=["worried"]),
    sweat(86, 18),
    # A thumbs-up arm, and one hugging its middle.
    p("M92 38 q10 -4 10 -16", "arms", stroke=bun, sw=6, pivot=[92, 38], rot=[10, 1.4, 0]),
    c(102, 19, 4.5, "arms", fill=bun, stroke=ink, sw=1.2, pivot=[92, 38], rot=[10, 1.4, 0]),
    p("M101.5 15 l0.5 -6", "arms", stroke=bun, sw=3.5, pivot=[92, 38], rot=[10, 1.4, 0]),
    p("M28 40 q-8 6 -2 12 q5 3 10 -1", "arms", stroke=bun, sw=6),
    *lens(108, 52),
  ],
  "groupMotion": {"fill": {"sy": [0.06, 0.9, 0], "p": [60, 46]}},
  "poses": {
    "hiding":   {"top": {"ty": 5, "s": 0.95, "p": [60, 42]}, "fill": {"sy": 0.6, "s": 0.9, "p": [60, 50]}, "arms": {"s": 0.6, "p": [60, 44]}},
    "sleeping": {"top": {"ty": 3, "r": 4, "p": [60, 42]}, "legs": {"s": 0.4, "p": [60, 70]}, "arms": {"s": 0.8, "p": [60, 44]}},
    "curious":  {"top": {"r": -9, "p": [60, 42]}},
  },
  "lines": {"click": ["Nom!", "I'm on a roll!", "Extra cheese, please.", "Lettuce celebrate!"],
            "pet": ["*happy sizzle*", "Hehe, careful, I'm saucy.", "*thumbs up*"],
            "yikes": ["*clamps buns shut*", "Don't eat me!"],
            "typing": ["Sizzling!", "Fast food, fast code.", "Ooh, typing!"],
            "save": ["Saved! Fresh off the grill.", "Order up!", "Saved!"],
            "fixed": ["Well done! Like my patty.", "All clear!", "Order up: no errors!"],
            "hungry": ["I'm hungry. Ironic, I know.", "Snack break?"],
            "lateNight": ["Midnight snack time?", "It's late. Kitchen's closing."],
            "eatCurly": ["Curly fries! Wait, braces.", "Crunchy!"],
            "full": ["I'm stuffed.", "No room, I'm a single patty."]},
}

def snack_face(x1, x2, y, group, mouth_dy=7):
    """Two big eyes, a smile and worried brows, the way every snack wears them."""
    mx = (x1 + x2) / 2
    return [*eye_set(x1, y, 2.5, group, ink, sclera="#FFFFFF"), *eye_set(x2, y, 2.5, group, ink, sclera="#FFFFFF"),
            p(f"M{mx-4} {y+mouth_dy} q4 3.5 8 0", group, stroke=ink, sw=1.5),
            p(f"M{x1-4} {y-6} l6 1.5 M{x2+4} {y-6} l-6 1.5", group, stroke=ink, sw=1.4, when=["worried"])]

def circle_path(cx, cy, r, reverse=False):
    """A circle as path commands, so two can make a ring (a hole needs the inner one drawn the other way)."""
    k = 0.5523 * r
    if not reverse:
        return (f"M{cx+r} {cy} C{cx+r} {cy+k} {cx+k} {cy+r} {cx} {cy+r} C{cx-k} {cy+r} {cx-r} {cy+k} {cx-r} {cy} "
                f"C{cx-r} {cy-k} {cx-k} {cy-r} {cx} {cy-r} C{cx+k} {cy-r} {cx+r} {cy-k} {cx+r} {cy}Z")
    return (f"M{cx+r} {cy} C{cx+r} {cy-k} {cx+k} {cy-r} {cx} {cy-r} C{cx-k} {cy-r} {cx-r} {cy-k} {cx-r} {cy} "
            f"C{cx-r} {cy+k} {cx-k} {cy+r} {cx} {cy+r} C{cx+k} {cy+r} {cx+r} {cy+k} {cx+r} {cy}Z")

# ---- Sushi --------------------------------------------------------------
PETS["sushi"] = {
  "label": "Sushi", "name": "Nori", "set": "snacks", "flip": True, "floor": True, "speed": 0.9,
  "bob": [1.2, 0.5], "glow": "rgba(251,146,60,0.4)", "mouth": [74, 55], "head": [72, 22],
  "parts": [
    leg_stroke(46, 56, -1, "#CBD5E1", 6, 0, 0.75), leg_stroke(76, 56, 1, "#CBD5E1", 6, 0.5, 0.75),
    p("M30 44 Q30 36 40 36 L80 36 Q90 36 90 44 L90 56 Q90 64 80 64 L40 64 Q30 64 30 56 Z", "body", fill="#F8FAFC", stroke=ink, sw=1.5),
    e(38, 56, 2, 1.1, "body", fill="#E2E8F0"), e(84, 58, 2, 1.1, "body", fill="#E2E8F0"), e(50, 60, 2, 1.1, "body", fill="#E2E8F0"),
    p("M40 34 L50 34 L50 64 L40 64 Z", "body", fill="#14532D", stroke=ink, sw=1.2),
    *snack_face(68, 80, 48, "face"),
    c(63, 55, 2.6, "face", fill="#F9A8D4", opacity=0.7), c(85, 55, 2.6, "face", fill="#F9A8D4", opacity=0.7),
    p("M25 39 Q28 22 60 22 Q93 20 97 34 Q95 41 86 39 Q60 34 35 43 Q26 45 25 39Z", "top", fill="#FB923C", stroke=ink, sw=1.5),
    p("M38 33 q9 -5 18 -3 M58 28 q10 -3 18 0 M78 27 q8 -1 13 3", "top", stroke="#FFEDD5", sw=2.2),
    p("M40 22 L50 22 L50 38 L40 40 Z", "top", fill="#14532D", stroke=ink, sw=1.2),
    sweat(92, 44),
    *lens(106, 56),
  ],
  "poses": {
    "hiding":   {"top": {"ty": 9, "s": 1.05, "p": [60, 36]}, "face": {"s": 0.9, "ty": 2, "p": [74, 52]}},
    "sleeping": {"top": {"ty": 4, "p": [60, 36]}, "face": {"ty": 1}, "legs": {"s": 0.4, "p": [60, 76]}},
    "curious":  {"face": {"r": -8, "p": [74, 52]}, "top": {"r": -4, "p": [60, 36]}},
  },
  "lines": {"click": ["Rice to meet you!", "Fresh!", "Roll with it.", "Soy happy to see you!"],
            "pet": ["*happy wiggle*", "Careful, I'm raw."],
            "yikes": ["*hides under the salmon*", "Wasabi! Too spicy!"],
            "typing": ["Rolling, rolling!", "Raw speed!", "Ooh, typing!"],
            "save": ["Saved! Rolled up tight.", "Saved!"],
            "fixed": ["Rice work!", "All clear!"],
            "lateNight": ["Late-night sushi? Bold.", "Coding past midnight? I'll keep you company."],
            "eatCurly": ["Braces? I was expecting chopsticks.", "Crunchy!"]},
}

# ---- Pizza --------------------------------------------------------------
PETS["pizza"] = {
  "label": "Pizza", "name": "Pepe", "set": "snacks", "flip": True, "floor": True, "speed": 1.0,
  "bob": [1.2, 0.5], "glow": "rgba(252,211,77,0.4)", "mouth": [66, 46], "head": [64, 18],
  "parts": [
    leg_stroke(46, 52, -1, "#D97706", 6, 0, 0.7), leg_stroke(70, 52, 1, "#D97706", 6, 0.5, 0.7),
    p("M32 16 Q24 40 32 64 L98 42 Q101 40 98 38 Z", "body", fill="#FCD34D", stroke=ink, sw=1.5),
    p("M70 51 q3 7 -1 10 q-4 -2 -2 -9z", "body", fill="#FCD34D", stroke=ink, sw=1.2),
    c(44, 27, 5, "body", fill="#DC2626", stroke=ink, sw=1.2), c(45, 53, 5, "body", fill="#DC2626", stroke=ink, sw=1.2),
    c(86, 40, 3.5, "body", fill="#DC2626", stroke=ink, sw=1.2),
    p("M32 16 Q22 40 32 64", "body", stroke=ink, sw=11), p("M32 16 Q22 40 32 64", "body", stroke="#E8A050", sw=8),
    *snack_face(60, 72, 38, "face"),
    c(56, 45, 2.4, "face", fill="#F9A8D4", opacity=0.7), c(76, 44, 2.2, "face", fill="#F9A8D4", opacity=0.7),
    sweat(80, 28),
    *lens(106, 52),
  ],
  "poses": {
    "hiding":   {"body": {"r": 12, "p": [30, 40]}, "face": {"r": 12, "s": 0.9, "p": [30, 40]}},
    "sleeping": {"body": {"r": 6, "p": [30, 40]}, "face": {"r": 6, "p": [30, 40]}, "legs": {"s": 0.4, "p": [58, 72]}},
    "curious":  {"face": {"r": -8, "p": [66, 40]}},
  },
  "lines": {"click": ["Slice to meet you!", "Extra cheese!", "Pizza my heart.", "Cheesy, I know."],
            "pet": ["*cheese stretches*", "Hehe, don't fold me."],
            "yikes": ["*curls up its crust*", "Pineapple?! Oh, it's just an error."],
            "typing": ["Hot and fresh!", "Code delivered in 30 minutes!", "Ooh, typing!"],
            "save": ["Saved! Hot out of the oven.", "Saved!"],
            "fixed": ["That's a-more like it!", "All clear!"],
            "hungry": ["I'm hungry. Weird for a pizza.", "Snack break?"],
            "lateNight": ["Midnight pizza? Classic.", "Night shift, huh?"]},
}

# ---- Donut --------------------------------------------------------------
sprinkle = lambda x, y, angle, color: p(f"M{x} {y} l{3 * math.cos(math.radians(angle)):.2f} {3 * math.sin(math.radians(angle)):.2f}", "body", stroke=color, sw=1.8)
PETS["donut"] = {
  "label": "Donut", "name": "Sprinkles", "set": "snacks", "flip": False, "floor": True, "speed": 0.8,
  "bob": [2, 0.5], "glow": "rgba(244,114,182,0.45)", "mouth": [60, 57], "head": [60, 16],
  "parts": [
    leg_stroke(50, 56, -1, "#C2783A", 6, 0, 0.7), leg_stroke(70, 56, 1, "#C2783A", 6, 0.5, 0.7),
    p(circle_path(60, 40, 22) + " " + circle_path(60, 36, 6.5, reverse=True), "body", fill="#E8A35E", stroke=ink, sw=1.5),
    p("M41 34 Q42 18 60 17 Q78 18 79 34 Q80 42 74 40 Q72 46 66 42 Q60 48 54 42 Q48 46 46 40 Q40 42 41 34Z " + circle_path(60, 36, 8.5, reverse=True),
      "body", fill="#F472B6", stroke=ink, sw=1.3),
    p(circle_path(60, 36, 8.5) + " " + circle_path(60, 36, 6.5, reverse=True), "body", fill="#D98E48"),
    sprinkle(46, 28, 30, "#FDE047"), sprinkle(52, 22, -40, "#60A5FA"), sprinkle(68, 22, 20, "#FFFFFF"),
    sprinkle(74, 30, -60, "#4ADE80"), sprinkle(48, 36, 80, "#60A5FA"), sprinkle(72, 37, 10, "#FDE047"),
    *snack_face(54, 66, 50, "face", mouth_dy=6),
    sweat(80, 26),
    *lens(96, 50),
  ],
  "groupMotion": {"body": {"sy": [0.03, 0.9, 0], "sx": [-0.02, 0.9, 0], "p": [60, 62]}},
  "poses": {
    "hiding":   {"body": {"s": 0.88, "p": [60, 62]}, "face": {"s": 0.8, "p": [60, 62]}},
    "sleeping": {"body": {"ty": 3}, "face": {"ty": 3}, "legs": {"s": 0.4, "p": [60, 76]}},
    "curious":  {"body": {"r": -8, "p": [60, 40]}, "face": {"r": -8, "p": [60, 40]}},
  },
  "lines": {"click": ["Donut worry!", "Hole-y moly!", "Glazed and amazed.", "Sweet!"],
            "pet": ["*sprinkles sparkle*", "So sweet of you."],
            "worried": ["Donut panic...", "Uh oh."],
            "yikes": ["Donut panic!", "*glaze melts*"],
            "typing": ["Sugar rush!", "Glazing through it!", "Ooh, typing!"],
            "save": ["Saved! Sweet.", "Saved!"],
            "fixed": ["Donut worry, all fixed!", "All clear!"],
            "lateNight": ["Midnight snack? I won't tell.", "Night shift, huh?"]},
}

# ---- Taco ---------------------------------------------------------------
PETS["taco"] = {
  "label": "Taco", "name": "Tuesday", "set": "snacks", "flip": False, "floor": True, "speed": 1.0,
  "bob": [1.5, 0.45], "glow": "rgba(251,191,36,0.45)", "mouth": [60, 53], "head": [60, 12],
  "parts": [
    leg_stroke(48, 58, -1, "#D97706", 6, 0, 0.7), leg_stroke(72, 58, 1, "#D97706", 6, 0.5, 0.7),
    e(60, 33, 32, 7, "filling", fill="#7C4A2D", stroke=ink, sw=1.2),
    c(38, 29, 4.5, "filling", fill="#EF4444", stroke=ink, sw=1.1), c(80, 28, 4.5, "filling", fill="#EF4444", stroke=ink, sw=1.1),
    p("M24 35" + " q4 -8 8 0" * 9 + " Z", "filling", fill="#4ADE80", stroke=ink, sw=1.2),
    p("M66 28 l4 -6 l3 6 M50 27 l3 -5 l3 5", "filling", stroke="#FDE047", sw=2.2),
    p("M23 34 Q23 66 60 66 Q97 66 97 34 Z", "body", fill="#FBBF24", stroke=ink, sw=1.6),
    e(34, 46, 1.6, 1, "body", fill="#D97706"), e(84, 44, 1.6, 1, "body", fill="#D97706"), e(42, 58, 1.6, 1, "body", fill="#D97706"),
    e(80, 56, 1.6, 1, "body", fill="#D97706"),
    *snack_face(54, 66, 46, "face"),
    c(48, 53, 2.6, "face", fill="#F9A8D4", opacity=0.7), c(72, 53, 2.6, "face", fill="#F9A8D4", opacity=0.7),
    sweat(86, 38),
    *lens(106, 54),
  ],
  "groupMotion": {"filling": {"sy": [0.05, 0.9, 0], "p": [60, 35]}},
  "poses": {
    "hiding":   {"filling": {"ty": 7, "s": 0.85, "p": [60, 36]}, "face": {"s": 0.9, "ty": 2, "p": [60, 50]}},
    "sleeping": {"filling": {"ty": 3, "p": [60, 36]}, "legs": {"s": 0.4, "p": [60, 76]}},
    "curious":  {"face": {"r": -8, "p": [60, 50]}, "filling": {"r": -5, "p": [60, 36]}},
  },
  "lines": {"click": ["It's taco time!", "Let's taco 'bout it.", "Crunch!", "Every day is Tuesday."],
            "pet": ["*happy crunch*", "Hehe, don't spill me."],
            "yikes": ["*spills lettuce*", "Hot sauce! Too hot!"],
            "typing": ["Spicy typing!", "Crunch time!", "Ooh, typing!"],
            "save": ["Saved! All wrapped up.", "Saved!"],
            "fixed": ["Nacho problem anymore!", "All clear!"],
            "lateNight": ["Late-night taco run?", "Night shift, huh?"]},
}

# ---- Games: original 8-bit characters ---------------------------------------
# Drawn as pixel art: each map row is a row of pixels, each letter a color from the palette, "." empty.
GAMES_LINES = {
  "hello": ["{name} joined the game!", "Player 2 has entered!"],
  "wake": ["Unpaused!", "Back in the game!"],
  "save": ["+1 coin!", "Progress saved!", "Checkpoint!"],
  "fixed": ["LEVEL UP!", "Boss defeated!", "Quest complete!"],
  "worried": ["Enemy spotted!", "Uh oh, a bug!", "Something's off."],
  "yikes": ["Too many enemies!", "Retreat!"],
  "taskOk": ["{task}: victory!", "{task} cleared!"],
  "taskFail": ["GAME OVER: {task}.", "{task} failed. Continue?"],
  "commit": ["Achievement unlocked: Commit!", "Saved to the high scores."],
  "typing": ["Combo!", "Button mashing!", "Ooh, typing!"],
  "debugOn": ["Bug hunt! Equip magnifier.", "Let's find it."],
  "feed": ["Power-up!", "Ooh, an item!"],
  "eatCurly": ["1UP!", "Power-up acquired!"],
  "eatSemicolon": ["+10 points!", "Crunchy semicolon!"],
  "morning": ["Player 1, ready!", "Press start!"],
  "lateNight": ["One more level? It's late.", "Night quest, huh?"],
  "longSession": ["You've been playing a while. Stretch?", "Save and take a break?"],
}

def pixels(rows, x0, y0, s, palette, group, **kw):
    """One part per color: runs of same-colored pixels in a row become one rectangle each."""
    out = []
    for key, color in palette.items():
        d = []
        for r, row in enumerate(rows):
            c = 0
            while c < len(row):
                if row[c] != key:
                    c += 1
                    continue
                start = c
                while c < len(row) and row[c] == key:
                    c += 1
                d.append(f"M{x0 + start * s} {y0 + r * s}h{(c - start) * s}v{s}h{-(c - start) * s}z")
        if d:
            out.append(p(" ".join(d), group, fill=color, **kw))
    return out

def pixel_eyes(cols, row, x0, y0, s, group, white="#FFFFFF", pupil="#0E1012"):
    """Pixel eyes two pixels wide: open (white with a pupil), closed (a line) and happy (^)."""
    parts = []
    for c in cols:
        x, y = x0 + c * s, y0 + row * s
        parts += [p(f"M{x} {y}h{2*s}v{2*s}h{-2*s}z", group, fill=white, when=["eyesOpen"]),
                  p(f"M{x+s} {y}h{s}v{2*s}h{-s}z", group, fill=pupil, when=["eyesOpen"]),
                  p(f"M{x} {y+s}h{2*s}v{s}h{-2*s}z", group, fill=pupil, when=["eyesClosed"]),
                  p(f"M{x} {y+s}h{s}v{s}h{-s}z M{x+s} {y}h{s}v{s}h{-s}z", group, fill=pupil, when=["eyesHappy"])]
    return parts

def pixel_sweat(x, y, s=3):
    return p(f"M{x} {y}h{s}v{s}h{-s}z M{x-s} {y+s}h{3*s}v{s}h{-3*s}z", "face", fill="#7DD3FC", when=["worried"])

# ---- Slime --------------------------------------------------------------
S4 = 4
slime_rows = [
  "......DDDD......",
  "....DDGGGGDD....",
  "...DGGLLGGGGD...",
  "..DGGLLGGGGGGD..",
  ".DGGGGGGGGGGGGD.",
  ".DGGGGGGGGGGGGD.",
  "DGGGGGGGGGGGGGGD",
  "DGGGGGGGGGGGGGGD",
  "DGGGGGGKKGGGGGGD",
  ".DGGGGGGGGGGGGD.",
  "..DDDDDDDDDDDD..",
]
PETS["slime"] = {
  "label": "Slime", "name": "Squish", "set": "games", "flip": False, "floor": True, "speed": 0.7,
  "bob": [3, 0.55], "glow": "rgba(74,222,128,0.45)", "mouth": [60, 62], "head": [60, 28],
  "parts": [
    *pixels(slime_rows, 28, 28, S4, {"D": "#166534", "G": "#4ADE80", "L": "#BBF7D0", "K": "#14532D"}, "body"),
    *pixel_eyes([4, 10], 5, 28, 28, S4, "face"),
    pixel_sweat(84, 34),
    *lens(98, 58),
  ],
  "groupMotion": {"body": {"sy": [0.08, 0.55, 0], "sx": [-0.05, 0.55, 0], "p": [60, 72]},
                  "face": {"sy": [0.08, 0.55, 0], "sx": [-0.05, 0.55, 0], "p": [60, 72]}},
  "poses": {
    "hiding":   {"body": {"s": 0.75, "p": [60, 72]}, "face": {"s": 0.75, "p": [60, 72]}},
    "sleeping": {"body": {"s": 0.9, "p": [60, 72]}, "face": {"s": 0.9, "p": [60, 72]}},
    "curious":  {"body": {"r": -6, "p": [60, 72]}, "face": {"r": -6, "p": [60, 72]}},
  },
  "lines": {"click": ["*squish*", "Boing!", "A wild slime appears!", "I'm level 1, be gentle."],
            "pet": ["*happy wobble*", "Sticky hugs!"],
            "yikes": ["*splits in two* Just kidding.", "*wobbles nervously*"]},
}

# ---- Ghost --------------------------------------------------------------
ghost_rows = [
  "....OOOOOO....",
  "..OOWWWWWWOO..",
  ".OWWWWWWWWWWO.",
  ".OWWWWWWWWWWO.",
  "OWWWWWWWWWWWWO",
  "OWWWWWWWWWWWWO",
  "OWWWWWWWWWWWWO",
  "OWPWWWWWWWWPWO",
  "OWWWWWKKWWWWWO",
  "OWWWWWWWWWWWWO",
  "OWWWWWWWWWWWWO",
  "OWWOWWOOWWOWWO",
  ".OO.OO..OO.OO.",
]
PETS["ghost"] = {
  "label": "Ghost", "name": "Boo", "set": "games", "flip": False, "floor": False, "speed": 0.7,
  "bob": [6, 2.6], "glow": "rgba(226,232,240,0.5)", "mouth": [60, 50], "head": [60, 14],
  "parts": [
    *pixels(ghost_rows, 32, 14, S4, {"O": "#64748B", "W": "#F1F5F9", "P": "#F9A8D4", "K": "#334155"}, "body", pivot=[60, 66], rot=[3, 2.6, 0]),
    *pixel_eyes([3, 9], 4, 32, 14, S4, "face", white="#334155", pupil="#0E1012"),
    pixel_sweat(90, 18),
    *lens(96, 50),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.8, "ty": 4, "p": [60, 40]}, "face": {"s": 0.8, "ty": 4, "p": [60, 40]}},
    "sleeping": {"body": {"ty": 4}, "face": {"ty": 4}},
    "curious":  {"body": {"r": -8, "p": [60, 40]}, "face": {"r": -8, "p": [60, 40]}},
  },
  "lines": {"click": ["Boo!", "Did I scare you?", "Wooo... hi.", "*floats happily*"],
            "pet": ["*blushes*", "Your hand went right through me. Hehe."],
            "yikes": ["*turns transparent*", "Eek! And I'm the ghost!"],
            "lateNight": ["Midnight? My favorite hour.", "Spooky hours. I love it."]},
}

# ---- Knight -------------------------------------------------------------
knight_rows = [
  ".....RR.....",
  "....RRR.....",
  "...SSSSSS...",
  "..SSSSSSSS..",
  "..SSKKKKSS..",
  "..SSSSSSSS..",
  "...SSSSSS...",
  "..BBBBBBBB..",
  ".BBBBYYBBBB.",
  ".BBBBYYBBBB.",
  "..BBBBBBBB..",
]
PETS["knight"] = {
  "label": "Knight", "name": "Sir Pix", "set": "games", "flip": True, "floor": True, "speed": 1.0,
  "bob": [1.2, 0.5], "glow": "rgba(147,197,253,0.4)", "mouth": [66, 26], "head": [60, 10],
  "parts": [
    p("M48 56h8v16h-8z", "legs", fill="#475569", pivot=[52, 56], rot=[14, 0.7, 0]),
    p("M64 56h8v16h-8z", "legs", fill="#475569", pivot=[68, 56], rot=[14, 0.7, 0.5]),
    p("M82 20h4v24h-4z M78 40h12v4h-12z M82 44h4v8h-4z", "arms", fill="#CBD5E1", pivot=[84, 48], rot=[10, 1.4, 0]),
    *pixels(knight_rows, 36, 12, S4, {"R": "#EF4444", "S": "#94A3B8", "K": "#1E293B", "B": "#3B82F6", "Y": "#FACC15"}, "body"),
    p("M48 28h4v4h-4z M64 28h4v4h-4z", "face", fill="#FDE047", when=["eyesOpen", "eyesHappy"]),
    pixel_sweat(84, 12),
    *lens(100, 56),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.9, "ty": 4, "p": [60, 56]}, "face": {"s": 0.9, "ty": 4, "p": [60, 56]}, "arms": {"s": 0.6, "p": [84, 48]}},
    "sleeping": {"body": {"ty": 4}, "face": {"ty": 4}, "legs": {"s": 0.5, "p": [60, 72]}, "arms": {"r": 60, "p": [84, 48]}},
    "curious":  {"body": {"r": -6, "p": [60, 56]}, "face": {"r": -6, "p": [60, 56]}},
  },
  "lines": {"click": ["For the codebase!", "Huzzah!", "En garde!", "*salutes*"],
            "pet": ["*clank of joy*", "Thou art kind."],
            "yikes": ["*hides behind shield*", "Retreat!"],
            "debugOn": ["A quest! Find the bug.", "I shall slay this bug."],
            "fixed": ["The bug is slain!", "LEVEL UP!"]},
}

# ---- Robot --------------------------------------------------------------
robot_rows = [
  "......A......",
  "..GGGGGGGGG..",
  "..GCCCCCCCG..",
  "..GCCCCCCCG..",
  "..GCCCCCCCG..",
  "..GCCCCCCCG..",
  "..GGGGGGGGG..",
  "...BBBBBBB...",
  "..BBBRRRBBB..",
  "...BBBBBBB...",
]
PETS["robot"] = {
  "label": "Robot", "name": "Bolt", "set": "games", "flip": False, "floor": True, "speed": 0.9,
  "bob": [1, 0.6], "glow": "rgba(103,232,249,0.4)", "mouth": [60, 32], "head": [60, 8],
  "parts": [
    p("M48 58h8v14h-8z", "legs", fill="#64748B", pivot=[52, 58], rot=[12, 0.8, 0]),
    p("M64 58h8v14h-8z", "legs", fill="#64748B", pivot=[68, 58], rot=[12, 0.8, 0.5]),
    *pixels(robot_rows, 34, 18, S4, {"A": "#94A3B8", "G": "#CBD5E1", "C": "#0E7490", "B": "#94A3B8", "R": "#EF4444"}, "body"),
    p("M58 10h4v4h-4z", "body", fill="#FDE047"),
    *pixel_eyes([4, 8], 3, 34, 18, S4, "face", white="#67E8F9", pupil="#083344"),
    p("M54 38h12v4h-12z", "face", fill="#67E8F9", when=["eyesOpen", "eyesHappy"]),
    pixel_sweat(88, 16),
    *lens(100, 56),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.85, "p": [60, 58]}, "face": {"s": 0.85, "p": [60, 58]}},
    "sleeping": {"body": {"ty": 3}, "face": {"ty": 3}, "legs": {"s": 0.5, "p": [60, 72]}},
    "curious":  {"body": {"r": -6, "p": [60, 58]}, "face": {"r": -6, "p": [60, 58]}},
  },
  "lines": {"click": ["Beep boop!", "Hello, human.", "01101000 01101001!", "Battery: 100% happy."],
            "pet": ["*happy whirring*", "Affection.exe running."],
            "yikes": ["Error! Error!", "*reboots nervously*"],
            "ai": ["A fellow AI! Beep!", "Hello, colleague."]},
}

# ---- Gadgets: things on your desk ------------------------------------------

def outlined(d, group, color, sw, **kw):
    """A thick line with an ink outline: the ink drawn wider underneath, then the color."""
    return [p(d, group, stroke=ink, sw=sw + 2.5, **kw), p(d, group, stroke=color, sw=sw, **kw)]

# ---- Laptop -------------------------------------------------------------
PETS["laptop"] = {
  "label": "Laptop", "name": "Lappy", "set": "gadgets", "flip": False, "floor": True, "speed": 0.9,
  "bob": [1, 0.5], "glow": "rgba(96,165,250,0.4)", "mouth": [60, 42], "head": [60, 12],
  "parts": [
    leg_stroke(46, 58, -1, "#6B7280", 6, 0, 0.7), leg_stroke(74, 58, 1, "#6B7280", 6, 0.5, 0.7),
    p("M30 54 H90 L98 60 H22 Z", "body", fill="#CBD5E1", stroke=ink, sw=1.5),
    p("M36 57 h48", "body", stroke="#94A3B8", sw=1.5),
    p("M36 14 H84 Q88 14 88 18 V54 H32 V18 Q32 14 36 14 Z", "lid", fill="#374151", stroke=ink, sw=1.5),
    p("M36 18 H84 V50 H36 Z", "lid", fill="#60A5FA"),
    p("M36 18 H84 V50 H36 Z", "lid", fill="#1E3A8A", when=["sleeping"]),
    p("M40 22 l8 0", "lid", stroke="#BFDBFE", sw=1.5, opacity=0.7),
    *snack_face(54, 66, 33, "lid"),
    sweat(84, 10),
    *lens(104, 56),
  ],
  "poses": {
    "hiding":   {"lid": {"ty": 10, "s": 0.75, "p": [60, 54]}},
    "sleeping": {"lid": {"ty": 3, "s": 0.95, "p": [60, 54]}, "legs": {"s": 0.4, "p": [60, 78]}},
    "curious":  {"lid": {"r": -6, "p": [60, 54]}},
  },
  "lines": {"click": ["*whirrs happily*", "Fully charged!", "Hello, world!", "Don't spill coffee on me."],
            "pet": ["*happy fan noises*", "Hehe, that's my trackpad."],
            "yikes": ["*closes its lid*", "Blue screen! Kidding."],
            "typing": ["Clack clack clack!", "My keys are on fire!", "Ooh, typing!"],
            "save": ["Saved to my SSD!", "Saved!"],
            "hot": ["My fans are spinning!", "I'm overheating!"],
            "batteryLow": ["I'm running low! Charger, please.", "{percent} left. Plug me in?"],
            "charging": ["Ahh, power.", "Charging! Thank you."]},
}

# ---- Gaming controller --------------------------------------------------
PETS["controller"] = {
  "label": "Controller", "name": "Joy", "set": "gadgets", "flip": False, "floor": True, "speed": 1.0,
  "bob": [1.2, 0.5], "glow": "rgba(129,140,248,0.45)", "mouth": [60, 44], "head": [60, 16],
  "parts": [
    leg_stroke(44, 56, -1, "#4F46E5", 6, 0, 0.7), leg_stroke(76, 56, 1, "#4F46E5", 6, 0.5, 0.7),
    p("M30 30 Q30 22 40 22 H80 Q90 22 90 30 Q99 46 95 56 Q91 63 84 58 L76 50 H44 L36 58 Q29 63 25 56 Q21 46 30 30 Z", "body", fill="#6366F1", stroke=ink, sw=1.6),
    p("M37 33 h6 v-6 h4 v6 h6 v4 h-6 v6 h-4 v-6 h-6z", "body", fill="#1E1B4B"),
    c(80, 29, 2.6, "buttons", fill="#EF4444", stroke=ink, sw=0.8), c(86, 35, 2.6, "buttons", fill="#22C55E", stroke=ink, sw=0.8),
    c(74, 35, 2.6, "buttons", fill="#3B82F6", stroke=ink, sw=0.8), c(80, 41, 2.6, "buttons", fill="#FACC15", stroke=ink, sw=0.8),
    *snack_face(54, 66, 36, "face"),
    sweat(90, 18),
    *lens(104, 54),
  ],
  "groupMotion": {"buttons": {"sx": [0.12, 0.6, 0], "sy": [0.12, 0.6, 0], "p": [80, 35]}},
  "poses": {
    "hiding":   {"body": {"r": 10, "s": 0.9, "p": [60, 50]}, "face": {"r": 10, "s": 0.9, "p": [60, 50]}, "buttons": {"r": 10, "s": 0.9, "p": [60, 50]}},
    "sleeping": {"body": {"ty": 3}, "face": {"ty": 3}, "buttons": {"ty": 3}, "legs": {"s": 0.4, "p": [60, 76]}},
    "curious":  {"face": {"r": -8, "p": [60, 40]}},
  },
  "lines": {"click": ["Player 1 ready!", "Press start!", "Up, up, down, down...", "Combo!"],
            "pet": ["*happy rumble*", "Hehe, that's my trigger."],
            "yikes": ["*rumbles nervously*", "Controller disconnected!"],
            "typing": ["Button mashing!", "Combo!", "Ooh, typing!"],
            "taskFail": ["GAME OVER: {task}.", "{task} failed. Continue?"],
            "fixed": ["LEVEL UP!", "High score!"],
            "game": ["Game time! Pick me!", "Let's play!"]},
}

# ---- Coffee mug ---------------------------------------------------------
PETS["mug"] = {
  "label": "Coffee mug", "name": "Java", "set": "gadgets", "flip": True, "floor": True, "speed": 0.8,
  "bob": [1, 0.5], "glow": "rgba(248,113,113,0.4)", "mouth": [57, 47], "head": [57, 8],
  "parts": [
    leg_stroke(48, 58, -1, "#DC2626", 6, 0, 0.75), leg_stroke(66, 58, 1, "#DC2626", 6, 0.5, 0.75),
    *outlined("M78 32 q12 0 12 11 q0 11 -12 11", "body", "#F87171", 5),
    p("M36 24 H78 V54 Q78 62 70 62 H44 Q36 62 36 54 Z", "body", fill="#F87171", stroke=ink, sw=1.6),
    e(57, 24, 21, 4, "body", fill="#6F4E37", stroke=ink, sw=1.3),
    p("M50 18 q-4 -5 0 -9 q4 -4 0 -9", "steam", stroke="#CBD5E1", sw=2.2, opacity=0.75, pivot=[50, 18], rot=[8, 1.6, 0]),
    p("M60 18 q-4 -5 0 -9 q4 -4 0 -9", "steam", stroke="#CBD5E1", sw=2.2, opacity=0.75, pivot=[60, 18], rot=[8, 1.6, 0.4]),
    p("M70 18 q-4 -5 0 -9", "steam", stroke="#CBD5E1", sw=2.2, opacity=0.6, pivot=[70, 18], rot=[8, 1.6, 0.8], when=["happy"]),
    *snack_face(51, 63, 40, "face"),
    c(45, 47, 2.4, "face", fill="#FECACA", opacity=0.8), c(69, 47, 2.4, "face", fill="#FECACA", opacity=0.8),
    sweat(82, 20),
    *lens(100, 52),
  ],
  "poses": {
    "hiding":   {"face": {"s": 0.85, "ty": 3, "p": [57, 50]}, "steam": {"s": 0.3, "p": [60, 20]}},
    "sleeping": {"steam": {"s": 0.4, "p": [60, 20]}, "legs": {"s": 0.4, "p": [57, 78]}},
    "curious":  {"face": {"r": -8, "p": [57, 45]}},
  },
  "lines": {"click": ["Espresso yourself!", "Brewing ideas.", "Refill?", "Latte love for you."],
            "pet": ["*warm and cozy*", "Careful, I'm hot!"],
            "yikes": ["*spills a little*", "Grounds for concern!"],
            "typing": ["Caffeinated typing!", "Brewing code!", "Ooh, typing!"],
            "save": ["Saved! Fresh brew.", "Saved!"],
            "longSession": ["Refill time? We've been at it a while.", "Coffee break? I insist."],
            "morning": ["Good morning! Coffee first.", "Rise and grind!"],
            "lateNight": ["Decaf, maybe?", "Coffee this late? Bold."]},
}

# ---- Rubber duck --------------------------------------------------------
PETS["duck"] = {
  "label": "Rubber duck", "name": "Quackers", "set": "gadgets", "flip": True, "floor": False, "speed": 0.7,
  "bob": [4, 2.4], "glow": "rgba(250,204,21,0.45)", "mouth": [96, 36], "head": [80, 14],
  "parts": [
    p("M30 46 Q30 32 50 34 Q70 36 74 44 Q86 44 88 52 Q86 66 58 66 Q32 66 30 46 Z", "body", fill="#FACC15", stroke=ink, sw=1.6, pivot=[58, 66], rot=[4, 2.4, 0]),
    p("M30 46 q-6 -8 -2 -14 q4 4 6 10", "body", fill="#FACC15", stroke=ink, sw=1.4, pivot=[58, 66], rot=[4, 2.4, 0]),
    p("M46 46 q10 -4 18 4 q-8 6 -18 -4z", "body", fill="#EAB308", stroke=ink, sw=1.2, pivot=[58, 66], rot=[4, 2.4, 0]),
    c(80, 30, 13, "head", fill="#FACC15", stroke=ink, sw=1.6),
    p("M90 31 q9 -1 11 3 q-3 4 -11 2z", "head", fill="#F97316", stroke=ink, sw=1.2),
    *eye_set(83, 26, 2.5, "head", ink, sclera="#FFFFFF"),
    p("M79 20 l6 2", "head", stroke=ink, sw=1.4, when=["worried"]),
    c(77, 34, 2.4, "head", fill="#FB923C", opacity=0.6),
    sweat(70, 14),
    *lens(108, 50),
  ],
  "poses": {
    "hiding":   {"head": {"tx": -6, "ty": 8, "s": 0.85, "p": [72, 40]}},
    "sleeping": {"head": {"tx": -2, "ty": 4, "r": 10, "p": [72, 40]}},
    "curious":  {"head": {"r": -12, "p": [76, 40]}},
  },
  "lines": {"click": ["Quack!", "*squeak*", "Explain it to me.", "I'm listening."],
            "pet": ["*squeak squeak*", "Quack quack!"],
            "yikes": ["QUACK!", "*squeaks in panic*"],
            "debugOn": ["Explain it to me, line by line.", "Talk me through it.", "What should it do? What does it do?"],
            "debugOff": ["See? Talking it through works.", "Quack. You figured it out."],
            "fixed": ["See? Talking it through works.", "Quack-tastic!"],
            "worried": ["Hmm. Explain that line to me?", "Uh oh."],
            "typing": ["Quack quack quack!", "Ooh, typing!"]},
}

# ---- Cactus -------------------------------------------------------------
PETS["cactus"] = {
  "label": "Cactus", "name": "Spike", "set": "gadgets", "flip": False, "floor": True, "speed": 0.5,
  "bob": [0.8, 0.8], "glow": "rgba(74,222,128,0.4)", "mouth": [60, 40], "head": [60, 10],
  "parts": [
    p("M47 18 Q47 12 60 12 Q73 12 73 18 V54 H47 Z", "body", fill="#4ADE80", stroke=ink, sw=1.6),
    p("M54 18 V50 M66 18 V50", "body", stroke="#22C55E", sw=1.5),
    *outlined("M47 40 h-6 q-5 0 -5 -5 v-9", "arms", "#4ADE80", 6, pivot=[47, 40], rot=[6, 2.2, 0]),
    *outlined("M73 34 h6 q5 0 5 -5 v-8", "arms", "#4ADE80", 6, pivot=[73, 34], rot=[6, 2.2, 0.5]),
    p("M50 24 l-3 -1 M70 22 l3 -1 M52 46 l-3 1 M68 44 l3 1", "body", stroke="#F0FDF4", sw=1),
    c(60, 9, 4, "flower", fill="#F472B6", stroke=ink, sw=1, when=["happy"]),
    c(60, 9, 1.6, "flower", fill="#FDE047", when=["happy"]),
    p("M40 52 H80 V58 H40 Z", "pot", fill="#C2410C", stroke=ink, sw=1.5),
    p("M42 58 H78 L74 74 H46 Z", "pot", fill="#EA580C", stroke=ink, sw=1.5),
    *snack_face(55, 65, 30, "face"),
    c(51, 37, 2.2, "face", fill="#F9A8D4", opacity=0.7), c(69, 37, 2.2, "face", fill="#F9A8D4", opacity=0.7),
    sweat(76, 12),
    *lens(96, 52),
  ],
  "poses": {
    "hiding":   {"arms": {"s": 0.45, "p": [60, 38]}, "face": {"s": 0.9, "ty": 2, "p": [60, 34]}},
    "sleeping": {"arms": {"s": 0.8, "p": [60, 38]}, "face": {"ty": 2}},
    "curious":  {"body": {"r": -5, "p": [60, 54]}, "face": {"r": -5, "p": [60, 54]}, "arms": {"r": -5, "p": [60, 54]}},
  },
  "lines": {"click": ["Hug? Careful.", "Low maintenance, high spirits.", "Looking sharp!", "I'm a succulent for you."],
            "pet": ["*prickly happiness*", "Ow, careful! Hehe."],
            "yikes": ["*pulls in its arms*", "Prickly situation!"],
            "fixed": ["Look, I bloomed!", "All clear!"],
            "hungry": ["Water? Just a sip.", "A little sunshine, please."],
            "feed": ["A snack? I usually just drink.", "Ooh, food!"],
            "typing": ["Growing with every line!", "Ooh, typing!"]},
}

# ---- Floppy disk --------------------------------------------------------
PETS["floppy"] = {
  "label": "Floppy disk", "name": "Floppy", "set": "gadgets", "flip": False, "floor": True, "speed": 0.9,
  "bob": [1, 0.5], "glow": "rgba(37,99,235,0.4)", "mouth": [60, 50], "head": [60, 12],
  "parts": [
    leg_stroke(48, 58, -1, "#1E40AF", 6, 0, 0.7), leg_stroke(72, 58, 1, "#1E40AF", 6, 0.5, 0.7),
    p("M36 16 H80 L86 22 V60 H36 Z", "body", fill="#2563EB", stroke=ink, sw=1.6),
    p("M47 16 H73 V30 H47 Z", "body", fill="#CBD5E1", stroke=ink, sw=1.2),
    p("M64 19 H69 V27 H64 Z", "body", fill="#475569"),
    p("M42 36 H80 V58 H42 Z", "body", fill="#F8FAFC", stroke=ink, sw=1.2),
    p("M46 40 h14", "body", stroke="#93C5FD", sw=1.5),
    *snack_face(55, 67, 46, "face", mouth_dy=6),
    sweat(84, 12),
    *lens(102, 54),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.85, "p": [60, 60]}, "face": {"s": 0.85, "p": [60, 60]}},
    "sleeping": {"body": {"ty": 2}, "face": {"ty": 2}, "legs": {"s": 0.4, "p": [60, 78]}},
    "curious":  {"body": {"r": -6, "p": [60, 60]}, "face": {"r": -6, "p": [60, 60]}},
  },
  "lines": {"click": ["I'm the save icon!", "Remember me?", "1.44 MB of personality.", "Insert me!"],
            "pet": ["*happy whirring*", "Hehe, careful with my shutter."],
            "yikes": ["*ejects itself*", "Disk error!"],
            "save": ["Saved! The old-fashioned way.", "1.44 MB of pure joy!", "Saved to disk. That's me!"],
            "typing": ["Writing to disk!", "Ooh, typing!"],
            "fixed": ["Error-free, like a fresh disk.", "All clear!"]},
}

# ---- Computer mouse -----------------------------------------------------
PETS["mouse"] = {
  "label": "Mouse", "name": "Click", "set": "gadgets", "flip": True, "floor": True, "speed": 1.2,
  "bob": [1, 0.4], "glow": "rgba(229,231,235,0.4)", "mouth": [70, 50], "head": [66, 20],
  "parts": [
    leg_stroke(52, 56, -1, "#6B7280", 5, 0, 0.5), leg_stroke(76, 56, 1, "#6B7280", 5, 0.5, 0.5),
    p("M40 56 q-10 0 -14 -10 q-4 -10 -14 -8", "tail", stroke="#6B7280", sw=2.6, pivot=[40, 56], rot=[14, 0.9, 0]),
    p("M40 60 Q40 26 66 24 Q92 26 92 60 Z", "body", fill="#E5E7EB", stroke=ink, sw=1.6),
    p("M66 24 V40", "body", stroke="#9CA3AF", sw=1.4),
    p("M64 28 H68 V36 H64 Z", "body", fill="#6B7280"),
    *snack_face(60, 74, 46, "face", mouth_dy=6),
    c(55, 52, 2.2, "face", fill="#F9A8D4", opacity=0.7), c(80, 52, 2.2, "face", fill="#F9A8D4", opacity=0.7),
    sweat(90, 22),
    *lens(106, 54),
  ],
  "poses": {
    "hiding":   {"body": {"s": 0.88, "p": [66, 60]}, "face": {"s": 0.88, "p": [66, 60]}, "tail": {"s": 0.6, "p": [40, 56]}},
    "sleeping": {"body": {"ty": 2}, "face": {"ty": 2}, "legs": {"s": 0.4, "p": [64, 76]}},
    "curious":  {"face": {"r": -8, "p": [66, 50]}},
  },
  "lines": {"click": ["Click!", "Double-click me!", "Right-click for options.", "*scrolls happily*"],
            "pet": ["*happy scroll*", "Cursor cuddles!"],
            "yikes": ["*unplugs itself*", "Eek! A mouse! Wait, that's me."],
            "typing": ["Keyboard shortcuts? I see how it is.", "Ooh, typing!"],
            "fixed": ["Point and fixed!", "All clear!"]},
}

# ---- Headphones ---------------------------------------------------------
PETS["headphones"] = {
  "label": "Headphones", "name": "Beats", "set": "gadgets", "flip": False, "floor": True, "speed": 1.0,
  "bob": [2, 0.5], "glow": "rgba(236,72,153,0.45)", "mouth": [60, 34], "head": [60, 8],
  "parts": [
    leg_stroke(33, 56, -1, "#BE185D", 5, 0, 0.6), leg_stroke(87, 56, 1, "#BE185D", 5, 0.5, 0.6),
    *outlined("M33 40 Q33 10 60 10 Q87 10 87 40", "body", "#E5E7EB", 6),
    p("M24 36 Q24 32 28 32 H38 Q42 32 42 36 V54 Q42 58 38 58 H28 Q24 58 24 54 Z", "body", fill="#EC4899", stroke=ink, sw=1.5),
    p("M78 36 Q78 32 82 32 H92 Q96 32 96 36 V54 Q96 58 92 58 H82 Q78 58 78 54 Z", "body", fill="#EC4899", stroke=ink, sw=1.5),
    *eye_set(33, 44, 3, "face", ink, sclera="#FFFFFF"), *eye_set(87, 44, 3, "face", ink, sclera="#FFFFFF"),
    p("M28 36 l7 2 M92 36 l-7 2", "face", stroke=ink, sw=1.4, when=["worried"]),
    p("M64 18 v-10 l7 -2 v10", "notes", stroke="#F9A8D4", sw=1.6, when=["happy"]),
    c(62, 18, 2.2, "notes", fill="#F9A8D4", when=["happy"]), c(69, 16, 2.2, "notes", fill="#F9A8D4", when=["happy"]),
    sweat(98, 26),
    *lens(106, 52),
  ],
  "groupMotion": {"body": {"sy": [0.03, 0.5, 0], "p": [60, 58]}},
  "poses": {
    "hiding":   {"body": {"s": 0.85, "p": [60, 58]}, "face": {"s": 0.85, "p": [60, 58]}},
    "sleeping": {"body": {"ty": 2}, "face": {"ty": 2}, "legs": {"s": 0.4, "p": [60, 76]}},
    "curious":  {"body": {"r": -7, "p": [60, 40]}, "face": {"r": -7, "p": [60, 40]}},
  },
  "lines": {"click": ["Turn it up!", "*bass drop*", "Now playing: you.", "Testing, one, two."],
            "pet": ["*happy bass*", "Hehe, that's my ear cup."],
            "yikes": ["*noise cancelling engaged*", "Too loud!"],
            "music": ["My jam!", "*bops along*", "Turn it up!"],
            "meeting": ["Mic check, one, two.", "You're on mute. Probably."],
            "typing": ["Typing to the beat!", "Ooh, typing!"]},
}

# ---- Sticky note --------------------------------------------------------
PETS["sticky"] = {
  "label": "Sticky note", "name": "Post", "set": "gadgets", "flip": False, "floor": True, "speed": 0.8,
  "bob": [1.2, 0.6], "glow": "rgba(253,230,138,0.45)", "mouth": [59, 44], "head": [60, 10],
  "parts": [
    leg_stroke(48, 56, -1, "#CA8A04", 5, 0, 0.7), leg_stroke(70, 56, 1, "#CA8A04", 5, 0.5, 0.7),
    p("M34 14 H86 V50 L76 60 H34 Z", "body", fill="#FDE68A", stroke=ink, sw=1.5),
    p("M86 50 H76 V60 Z", "body", fill="#FCD34D", stroke=ink, sw=1.2),
    p("M50 10 H70 V18 H50 Z", "body", fill="#E0F2FE", opacity=0.85),
    p("M40 24 h18 M40 29 h12", "body", stroke="#92400E", sw=1.6),
    p("M62 24 l2 2 l4 -5", "body", stroke="#16A34A", sw=1.8, when=["happy"]),
    *snack_face(53, 65, 38, "face", mouth_dy=6),
    sweat(84, 12),
    *lens(100, 52),
  ],
  "poses": {
    "hiding":   {"body": {"r": 8, "s": 0.88, "p": [60, 14]}, "face": {"r": 8, "s": 0.88, "p": [60, 14]}},
    "sleeping": {"body": {"r": 4, "p": [60, 14]}, "face": {"r": 4, "p": [60, 14]}, "legs": {"s": 0.4, "p": [60, 76]}},
    "curious":  {"body": {"r": -6, "p": [60, 14]}, "face": {"r": -6, "p": [60, 14]}},
  },
  "lines": {"click": ["Don't forget the tests!", "Note to self: you're great.", "TODO: pet me.", "Remember to drink water."],
            "pet": ["TODO: pet me. Done!", "*happy rustle*"],
            "yikes": ["*falls off the monitor*", "*curls up at the edges*"],
            "save": ["Noted!", "Saved. I'll remember."],
            "fixed": ["Crossed off the list!", "All clear!"],
            "commit": ["Added to the changelog.", "Committed! Noted."],
            "worried": ["Note: something's off.", "Uh oh."],
            "typing": ["Taking notes!", "Ooh, typing!"]},
}

for pet in PETS.values():
    pet.setdefault("set", "tide")
    if pet["set"] == "gadgets":
        pet["lines"] = {**HOME_LINES, **pet["lines"]}
    if pet["set"] == "games":
        pet["lines"] = {**HOME_LINES, **GAMES_LINES, **pet["lines"]}
    if pet["set"] in ("home", "snacks"):
        pet["lines"] = {**HOME_LINES, **pet["lines"]}

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

# Snacks dropped by Feed (and every 20th "{" typed); each has its own lines.
SNACKS = [
  {"text": "{ }", "key": "eatCurly"},
  {"text": "[ ]", "key": "eatSquare"},
  {"text": "( )", "key": "eatParens"},
  {"text": "< >", "key": "eatAngle"},
  {"text": ";", "key": "eatSemicolon"},
]

# What happens on an event the IDE reports with a key (pet.react(key, vars)).
# mood: happy | excited | curious | hiding | spin; ms: how long; bubbles / hearts: how many;
# chance: how often it also says something; cooldown: seconds before it reacts to the key again.
# Lines live in LINES (or a pet's own "lines") under the same key.
REACTIONS = {
  "ai":          {"mood": "curious", "ms": 1500, "bubbles": 2, "cooldown": 15},
  "aiBig":       {"mood": "curious", "ms": 1500, "chance": 0.8, "cooldown": 30},
  "terminal":    {"mood": "curious", "ms": 1200, "cooldown": 15},
  "gitPush":     {"mood": "happy", "ms": 1100, "bubbles": 5, "cooldown": 20},
  "gitPushFriday": {"mood": "hiding", "ms": 1500, "cooldown": 20},
  "test":        {"mood": "excited", "ms": 3000, "cooldown": 30},
  "install":     {"mood": "excited", "ms": 3000, "cooldown": 60},
  "danger":      {"mood": "hiding", "ms": 2200, "cooldown": 10},
  "commandFail": {"mood": "curious", "ms": 1200, "cooldown": 10},
  "run":         {"mood": "spin", "ms": 800, "bubbles": 4, "cooldown": 15},
  "build":       {"mood": "excited", "ms": 3000, "chance": 0.6, "cooldown": 60},
  "commit":      {"mood": "happy", "ms": 1100, "bubbles": 6, "cooldown": 10},
  "branch":      {"mood": "curious", "ms": 1500, "cooldown": 10},
  "undo":        {"mood": "curious", "ms": 1200, "cooldown": 60},
  "pet":         {"mood": "happy", "ms": 1100, "hearts": 5, "cooldown": 0},
  "lateNight":   {"cooldown": 3 * 3600},
  "morning":     {"cooldown": 6 * 3600},
  "longSession": {"mood": "curious", "ms": 1500, "cooldown": 3600},
  "feed":        {"cooldown": 0},
  "crumb":       {"chance": 0.8, "cooldown": 0},
  "hungry":      {"mood": "curious", "ms": 1500, "cooldown": 1800},
  "full":        {"mood": "happy", "ms": 1100, "hearts": 3, "cooldown": 300},
}

LINES.update({
  "ai": ["Ooh, an AI! Are we friends?", "Two assistants are better than one.", "Make sure it writes the tests too.",
         "Beep boop. Just kidding, I'm a {kind}.", "Tell the AI I said hi.", "Asking the AI? I'd have said the same.",
         "Don't forget to read what it writes.", "I can't code, but I can cheer!", "The robot's back!"],
  "aiBig": ["Did an AI write that? I won't tell.", "Whoa, that's a lot of code at once.", "That appeared fast!"],
  "terminal": ["Ooh, the terminal. Type something cool.", "Command line time!", "I like the blinking cursor.",
               "Terminal! Where the magic happens.", "Back to the command line?", "Careful with rm -rf.", "What are we running?"],
  "gitPush": ["Ship it!", "Off it goes!", "Pushed! Bon voyage, little commits."],
  "gitPushFriday": ["Pushing on a Friday? Brave.", "A Friday push... I'll be in my shell."],
  "test": ["Fingers crossed!", "Testing, testing...", "Come on, green!"],
  "install": ["Downloading the internet...", "So many packages.", "node_modules is getting bigger."],
  "danger": ["Careful with that!", "*hides* Are you sure about that one?"],
  "commandFail": ["That one didn't work.", "Hmm, the command failed.", "Exit code says no."],
  "run": ["Here we go!", "It's alive!", "Running {task}!", "Let's see it go!"],
  "build": ["Building...", "Compiling, hold on.", "Construction in progress."],
  "commit": ["Committed! Nice.", "Another one for the history books.", "Saved to the logbook."],
  "branch": ["New branch: {branch}.", "Ooh, {branch}.", "Off to {branch}!"],
  "undo": ["Rewinding time?", "Undo, undo, undo...", "Let's pretend that never happened."],
  "pet": ["*happy noises*", "Hehe, that tickles.", "I like you too!"],
  "lateNight": ["It's late. The tide's out.", "Coding past midnight? I'll keep you company.", "Night shift, huh?"],
  "morning": ["Good morning!", "Fresh tide, fresh code.", "Morning! Coffee first?"],
  "feed": ["Ooh, snack time!", "Food!"],
  "crumb": ["You dropped a crumb!", "A curly brace fell in!", "Ooh, a snack from your code."],
  "hungry": ["I'm hungry. Got any curly braces?", "*tummy rumbles* Feed me a semicolon?", "Snack break?"],
  "full": ["I'm so full.", "*happy and full*", "No more braces, please. Okay, one more."],
  "eatCurly": ["Mmm, curly braces!", "Crunchy!", "A matched pair. Delicious."],
  "eatSquare": ["Square brackets! Very crisp.", "Mmm, arrays."],
  "eatParens": ["Parentheses! Smooth.", "(Yum.)"],
  "eatAngle": ["Angle brackets. Generic, but tasty.", "Mmm, <T>-bone."],
  "eatSemicolon": ["A semicolon! My favorite.", "Statement terminated. Yum.", "Crunchy little semicolon."],
  "longSession": ["You've been at it a while. Stretch break?", "Water break? I'm already in water.", "Blink a few times. Eyes need breaks too."],
})

# What Claude Code tells the Mac app it's doing (the Petabytes add-on for Claude Code sends these).
REACTIONS.update({
  "claudeStart":   {"mood": "curious", "ms": 1500, "cooldown": 5},
  "claudeRead":    {"mood": "curious", "ms": 1200, "chance": 0.5, "cooldown": 30},
  "claudeEdit":    {"mood": "excited", "ms": 2500, "chance": 0.6, "cooldown": 30},
  "claudeWeb":     {"mood": "curious", "ms": 1500, "chance": 0.7, "cooldown": 30},
  "claudeAgent":   {"mood": "excited", "ms": 2000, "cooldown": 30},
  "claudeTestsOk": {"mood": "happy", "ms": 1100, "bubbles": 6, "cooldown": 5},
  "claudeTestsFailed": {"mood": "hiding", "ms": 2200, "cooldown": 5},
  "claudeDone":    {"mood": "happy", "ms": 1100, "bubbles": 3, "cooldown": 5},
})

LINES.update({
  "claudeStart": ["On it!", "Ooh, a new task.", "Let's go!", "Claude's on it.", "Good one."],
  "claudeRead": ["Reading up...", "Looking around the code.", "What's in here?", "Research time."],
  "claudeEdit": ["Ooh, new code.", "Look at it go!", "Fresh code, coming up.", "Claude's typing!"],
  "claudeWeb": ["To the internet!", "Researching!", "Looking it up."],
  "claudeAgent": ["Calling in a friend!", "Teamwork!", "More helpers!"],
  "claudeTestsOk": ["All green!", "Tests passed!", "Woohoo, it works!"],
  "claudeTestsFailed": ["Oof, tests failed.", "Red. We'll get it.", "*hides* Not green..."],
  "claudeDone": ["Done! Nice work.", "All done!", "Ta-da!", "Claude's done. Your turn!"],
})

# Things only the Mac app sees: the Mac itself, and the apps you switch to. Switching apps always gets a
# reaction and a line; the cooldowns keep a busy afternoon of switching from turning into chatter.
REACTIONS.update({
  "ide":         {"mood": "excited", "ms": 2000, "cooldown": 300},
  "meeting":     {"mood": "hiding", "ms": 2000, "cooldown": 300},
  "music":       {"mood": "happy", "ms": 1100, "bubbles": 3, "cooldown": 600},
  "batteryLow":  {"mood": "curious", "ms": 1500, "cooldown": 1800},
  "charging":    {"mood": "happy", "ms": 1100, "bubbles": 4, "cooldown": 120},
  "offline":     {"mood": "hiding", "ms": 2000, "cooldown": 60},
  "online":      {"mood": "happy", "ms": 1100, "cooldown": 60},
  "download":    {"mood": "curious", "ms": 1200, "cooldown": 20},
  "screenshot":  {"mood": "happy", "ms": 1100, "cooldown": 10},
  "copy":        {"chance": 0.08, "cooldown": 300},
  "hot":         {"mood": "worried", "ms": 2500, "cooldown": 900},
  "darkMode":    {"mood": "curious", "ms": 1200, "cooldown": 30},
  "unlock":      {"mood": "happy", "ms": 1100, "hearts": 2, "cooldown": 60},
  "browser":     {"mood": "curious", "ms": 1200, "cooldown": 300},
  "chat":        {"mood": "curious", "ms": 1200, "cooldown": 300},
  "mail":        {"mood": "curious", "ms": 1200, "cooldown": 600},
  "design":      {"mood": "happy", "ms": 1100, "bubbles": 3, "cooldown": 600},
  "notes":       {"mood": "curious", "ms": 1200, "cooldown": 600},
  "calendar":    {"mood": "curious", "ms": 1200, "cooldown": 900},
  "game":        {"mood": "excited", "ms": 3000, "cooldown": 600},
  "video":       {"mood": "happy", "ms": 1100, "cooldown": 900},
  "activity":    {"mood": "curious", "ms": 1500, "cooldown": 600},
  "docker":      {"mood": "curious", "ms": 1200, "cooldown": 600},
  "database":    {"mood": "hiding", "ms": 1500, "cooldown": 600},
  "api":         {"mood": "curious", "ms": 1200, "cooldown": 600},
  "simulator":   {"mood": "spin", "ms": 800, "bubbles": 3, "cooldown": 300},
  "settings":    {"mood": "curious", "ms": 1200, "cooldown": 600},
  "appStore":    {"mood": "curious", "ms": 1200, "cooldown": 900},
  "passwords":   {"mood": "hiding", "ms": 1500, "cooldown": 600},
})

LINES.update({
  "ide": ["Code time!", "Back to the editor!", "What are we building today?"],
  "meeting": ["A call? I'll be quiet.", "*hides from the camera*", "Mute yourself when you sneeze."],
  "music": ["Ooh, music!", "Is this a sea shanty?", "*bobs along*"],
  "batteryLow": ["Battery's low. Got a charger?", "Running on fumes here.", "{percent} battery left."],
  "charging": ["Ahh, power.", "Charging! Snack for the laptop.", "Plugged in. Nice."],
  "offline": ["The internet's gone!", "Offline. Just us now.", "No Wi-Fi? I'll still keep you company."],
  "online": ["We're back online!", "Internet's back."],
  "download": ["Something landed in Downloads.", "Download done!", "Ooh, a new file."],
  "screenshot": ["Cheese!", "Did you get my good side?", "Screenshot! Was I in it?"],
  "copy": ["Copy-paste? I saw nothing.", "Ctrl+C, Ctrl+V. Classic."],
  "hot": ["It's getting hot in here.", "Your Mac's working hard.", "Is the water warming up?"],
  "darkMode": ["Lights out!", "Ooh, new look.", "Switching modes?"],
  "unlock": ["Welcome back!", "You're back!", "Missed you."],
  "browser": ["Just one tab, right?", "Researching? Or scrolling?", "Look it up, I won't judge."],
  "chat": ["Say hi from me!", "Back to the chats?", "Who's messaging?"],
  "mail": ["Inbox zero?", "Any good emails?", "Reply-all with care."],
  "design": ["Ooh, pretty!", "Make it pop.", "Can you draw me next?"],
  "notes": ["Taking notes?", "Write that down.", "Writing something?"],
  "calendar": ["Another meeting?", "What's on today?", "Is there time for a snack?"],
  "game": ["Game time! Can I play?", "Break time!", "One more round?"],
  "video": ["Movie time? I'll be quiet.", "Popcorn?", "Ooh, what are we watching?"],
  "activity": ["Who's using all the memory?", "Something hogging the CPU?", "It wasn't me."],
  "docker": ["Containers! Cozy.", "Spinning up the whales?", "It works on my container."],
  "database": ["Careful with that DROP TABLE.", "Back up first?", "*peeks at the rows*"],
  "api": ["Sending requests?", "200 OK, I hope.", "Fingers crossed for no 500s."],
  "simulator": ["It's alive! On a tiny phone.", "Running it on the simulator!"],
  "settings": ["Tweaking things?", "Don't turn me off!", "Fiddling with settings?"],
  "appStore": ["Shopping?", "Ooh, a new app?"],
  "passwords": ["*covers eyes*", "I'm not looking!"],
})

PETS["crab"]["lines"].update({"pet": ["*happy clacks*", "Snip! I mean, thanks!"], "run": ["Scuttling into action!", "It's alive! *clack clack*"]})
PETS["octopus"]["lines"].update({"pet": ["*hugs you with all eight arms*", "Eight arms, all for you."], "ai": ["An AI? I have eight arms, it has a million parameters."]})
PETS["pufferfish"]["lines"].update({"pet": ["*puffs happily*", "Hehe, don't pop me."], "danger": ["*PUFF* Careful!", "*maximum puff*"]})
PETS["jellyfish"]["lines"].update({"pet": ["*glows brighter*", "Bloop! Thank you."], "lateNight": ["It's late. Good thing I glow."]})
PETS["turtle"]["lines"].update({"pet": ["*happy flipper flaps*", "Hehe, my shell is ticklish."], "longSession": ["Even turtles take breaks. Stretch?"]})

# Antics: what a pet does on its own, now and then, while you pause (not while it sleeps, hides, eats or worries).
# Each is a reaction (mood, bubbles, hearts, and how likely it is to say something), picked at random every
# ANTIC_EVERY seconds or so. "glyph" is what the Dock icon's corner shows when the line can't go above the icon.
ANTICS = {
  "anticSpin":    {"mood": "spin", "ms": 800, "bubbles": 2, "chance": 0.5, "glyph": "!"},
  "anticHop":     {"mood": "happy", "ms": 1100, "chance": 0.5, "glyph": "♥"},
  "anticLook":    {"mood": "curious", "ms": 1800, "chance": 0.6, "glyph": "?"},
  "anticZoomies": {"mood": "excited", "ms": 3500, "chance": 0.6, "glyph": "!"},
  "anticHum":     {"chance": 1, "glyph": "♪"},
  "anticHearts":  {"hearts": 3, "chance": 0.5, "glyph": "♥"},
  "anticThink":   {"mood": "curious", "ms": 1200, "chance": 1, "glyph": "?"},
  "anticYawn":    {"chance": 1, "glyph": "…"},
  "anticBubbles": {"bubbles": 6, "chance": 0.3, "glyph": "○"},
}
ANTIC_EVERY = [70, 160]
REACTIONS.update(ANTICS)

LINES.update({
  "anticSpin": ["Wheee!", "Did you see that?", "Again! Again!", "*twirls*"],
  "anticHop": ["Boing!", "Hop!", "Just stretching my legs.", "*does a little dance*"],
  "anticLook": ["Did you hear that?", "What's over there?", "Hmm...", "*looks around*"],
  "anticZoomies": ["Zoomies!", "Gotta go fast!", "Can't stop, won't stop!", "*races around*"],
  "anticHum": ["♪ la la la ♪", "♪ do-do-do ♪", "*hums a little tune*", "♪ hmm hmm hmm ♪"],
  "anticHearts": ["I like it here.", "You're doing great.", "Best desk ever.", "*happy sigh*"],
  "anticThink": ["Do bugs have bugs?", "Is a semicolon a snack?", "What if the cloud is just someone else's computer?",
                 "Tabs or spaces? Don't answer.", "I wonder what's for lunch.", "Is it Friday yet?", "Thinking about snacks."],
  "anticYawn": ["*yawns*", "*stretches*", "*big stretch*", "Mm, cozy."],
  "anticBubbles": ["Blub blub.", "Bubble time!", "*blows bubbles*"],
})

# Each set does them its own way too (a pet's own lines still come first).
SET_ANTIC_LINES = {
  "tide": {"anticZoomies": ["Full speed ahead!", "Riding the current!", "*splashes around*"],
           "anticHum": ["*sings a sea shanty*", "♪ yo ho, yo ho ♪", "*hums with the waves*"]},
  "home": {"anticZoomies": ["Zoomies!", "*runs in circles*", "*chases own tail*"],
           "anticLook": ["*sniffs around*", "Did someone say treat?", "*ears perk up*"]},
  "snacks": {"anticThink": ["Do I need more salt?", "Am I a sandwich?", "Feeling saucy.", "Is it snack o'clock?"],
             "anticHop": ["*sizzles*", "Fresh out of the oven!", "Hot and ready!"]},
  "games": {"anticSpin": ["Combo!", "*double jump*", "Achievement unlocked: spin!"],
            "anticThink": ["Is there a save point nearby?", "I should grind some XP.", "Side quest?"]},
  "gadgets": {"anticThink": ["Have you tried turning it off and on again?", "Running diagnostics... all good!", "*defragments quietly*"],
              "anticHum": ["*beeps a tune*", "♪ beep boop ♪", "*whirrs along*"]},
}
for pet in PETS.values():
    pet["lines"] = {**SET_ANTIC_LINES.get(pet["set"], {}), **pet["lines"]}

print(json.dumps({"version": 1, "box": [120, 80], "lines": LINES, "reactions": REACTIONS, "snacks": SNACKS,
                  "antics": list(ANTICS), "anticEvery": ANTIC_EVERY, "order": list(PETS), "pets": PETS}, indent=1))
