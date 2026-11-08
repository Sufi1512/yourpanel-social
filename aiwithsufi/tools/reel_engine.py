"""@aiwithsufi explainer Reel engine.

Usage:  python3 reel_engine.py script.json OUT.mp4 [--preview]
Builds a 1080x1920 Reel from a JSON script: Fenrir voice (Kokoro, offline), English captions,
Charcoal & Gold palette, Montserrat font, flat style (no glow, no gradients).

Script format:
{
  "title": "AI Agents", "next": "MCP",
  "scenes": [
    {"type": "hook", "chips": ["ChatGPT", "AI Agent"], "title": "AI AGENTS", "subtitle": "...", "lines": [{"vo": "...", "cap": "..."}]},
    {"type": "flow",    "label": "STEP 1 · ...", "nodes": [{"t": "Goal", "s": "optional sub text", "at": 0}], "lines": [...]},
    {"type": "cycle",   "label": "...", "center": "Agent", "nodes": [{"t": "Think"}, {"t": "Act"}, {"t": "Observe"}], "lines": [...]},
    {"type": "hub",     "label": "...", "center": "LLM", "nodes": [{"t": "Web search"}, ...], "lines": [...]},
    {"type": "list",    "label": "...", "items": [{"t": "...", "s": "...", "at": 1}], "lines": [...]},
    {"type": "compare", "label": "...", "left": "Chatbot", "right": "Agent", "rows": [["answers", "acts"], ...], "lines": [...]},
    {"type": "bars",    "label": "...", "title": "...", "bars": [{"t": "Paris", "v": 82, "unit": "%"}], "lines": [...]},
    {"type": "code",    "label": "...", "title": "...", "code": "line1\nline2", "at": 1, "note": "...", "lines": [...]},  (typewriter)
    {"type": "quiz",    "label": "...", "question": "...", "options": ["...", "...", "..."], "answer": 1, "reveal": 2, "lines": [...]},  (pause & guess)
    {"type": "outro",   "recap": ["Goal", "Tools", "Memory", "Loop"], "lines": [...]}
  ]
}
Discussion style (default for new Reels): add "speakers": {"A": {"name": "Arjun", "voice": "am_fenrir"},
"B": {"name": "Riya", "voice": "af_heart"}} and give every line "who": "A" (host who explains) or "B" (curious
co-host who asks what viewers would ask). Captions then show the speaker's name with a live waveform and
highlight word by word. See scripts/2026-11-09-ai-agents-discussion.json.
Every element may carry "at": the index of the voiceover line at which it appears (default: spread evenly).
In captions, words in ALL CAPS are highlighted in gold.
"""
import json, math, os, subprocess, sys, tempfile, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SS = 1080, 1920, 30, 2
BG = (20, 20, 22); CARD = (32, 32, 35); CARD2 = (38, 38, 42); LINE = (70, 70, 74)
TEXT = (240, 236, 226); MUTED = (150, 146, 138); GOLD = (196, 164, 104)
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/.cache/aiwithsufi"); os.makedirs(CACHE, exist_ok=True)
FONT = os.path.join(HERE, "Montserrat.ttf")
AVATAR = os.path.join(HERE, "avatar.png")
DL = {
    FONT: "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    os.path.join(CACHE, "kokoro-v1.0.onnx"): "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    os.path.join(CACHE, "voices-v1.0.bin"): "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
MONO = os.path.join(HERE, "PlexMono.ttf")
DL[MONO] = "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-Medium.ttf"
VOICE, SPEED = "am_fenrir", 1.0

def fetch(path):
    if not os.path.exists(path):
        print("downloading", os.path.basename(path)); urllib.request.urlretrieve(DL[path], path)
    return path

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def inout(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def mix(a, b, t): t = clamp(t); return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def fade(c, a): return mix(BG, c, a)

_fc = {}
def font(size, weight="Bold", scale=SS):
    k = (round(size, 1), weight, scale)
    if k not in _fc:
        f = ImageFont.truetype(fetch(FONT), max(1, int(size * scale)))
        f.set_variation_by_name("ExtraBold" if size >= 56 and weight == "Bold" else weight)
        _fc[k] = f
    return _fc[k]

class Canvas:
    def __init__(self):
        self.im = Image.new("RGB", (W * SS, H * SS), BG); self.d = ImageDraw.Draw(self.im)
    def s(self, v): return int(round(v * SS))
    def circle(self, x, y, r, fill=None, outline=None, width=0):
        self.d.ellipse([self.s(x - r), self.s(y - r), self.s(x + r), self.s(y + r)], fill=fill, outline=outline, width=self.s(width))
    def line(self, pts, fill, width):
        self.d.line([(self.s(x), self.s(y)) for x, y in pts], fill=fill, width=max(1, self.s(width)), joint="curve")
    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, width=0):
        if x1 <= x0 or y1 <= y0: return
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        self.d.rounded_rectangle([self.s(x0), self.s(y0), self.s(x1), self.s(y1)], radius=self.s(r), fill=fill, outline=outline, width=self.s(width))
    def poly(self, pts, fill): self.d.polygon([(self.s(x), self.s(y)) for x, y in pts], fill=fill)
    def text(self, x, y, t, size, fill, weight="Bold", anchor="mm"):
        self.d.text((self.s(x), self.s(y)), t, font=font(size, weight), fill=fill, anchor=anchor)
    def tw(self, t, size, weight="Bold"):
        b = self.d.textbbox((0, 0), t, font=font(size, weight)); return (b[2] - b[0]) / SS
    def arrow(self, x0, y0, x1, y1, col, w=4, head=16):
        self.line([(x0, y0), (x1, y1)], col, w)
        a = math.atan2(y1 - y0, x1 - x0)
        self.poly([(x1, y1), (x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45)),
                   (x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))], col)
    def fit(self, t, size, maxw, weight="Bold"):
        while size > 18 and self.tw(t, size, weight) > maxw: size -= 1
        return size
    def out(self): return self.im.reduce(SS)

_av = {}
def avatar(c, x, y, r, t, a):
    if not os.path.exists(AVATAR): return
    size = int(2 * r * SS)
    if size not in _av:
        im = Image.open(AVATAR).convert("RGB"); s = min(im.size)
        im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((size, size), Image.LANCZOS)
        m = Image.new("L", (size * 2, size * 2), 0); ImageDraw.Draw(m).ellipse([0, 0, size * 2 - 1, size * 2 - 1], fill=255)
        _av[size] = (im, m.resize((size, size), Image.LANCZOS))
    im, m = _av[size]
    if a < 1: m = m.point(lambda v: int(v * a))
    c.im.paste(im, (c.s(x - r), c.s(y - r)), m)
    st = (t * 60) % 360
    bb = [c.s(x - r - 16), c.s(y - r - 16), c.s(x + r + 16), c.s(y + r + 16)]
    c.d.arc(bb, 0, 360, fill=fade(LINE, a), width=c.s(4)); c.d.arc(bb, st, st + 90, fill=fade(GOLD, a), width=c.s(6))

# ---------- shared ----------
def node(c, x, y, t, s, a, hi, w=None, h=None, size=40):
    w = w or max(260, c.tw(t, size) + 80); h = h or (120 if s else 96)
    c.rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, 22, fill=fade(CARD2, a), outline=fade(GOLD if hi else LINE, a), width=3 if hi else 2)
    size = c.fit(t, size, w - 40)
    if s:
        c.text(x, y - 18, t, size, fade(TEXT, a)); c.text(x, y + 28, s, 30, fade(MUTED, a), "Medium")
    else:
        c.text(x, y, t, size, fade(TEXT, a))
    return w, h

def reveal_times(items, sc):
    L = sc["lines"]; n = len(items); out = []
    for i, it in enumerate(items):
        if "at" in it:
            li = min(int(it["at"]), len(L) - 1); out.append(L[li]["start"] + 0.15 * sum(1 for j in items[:i] if j.get("at") == it.get("at")))
        else:
            span = (L[-1]["end"] - L[0]["start"]) * 0.75
            out.append(L[0]["start"] + 0.3 + span * i / max(1, n))
    return out

def chrome(c, sc, t, T, TOTAL):
    c.rrect(60, 70, W - 60, 78, 4, fill=LINE)
    c.rrect(60, 70, 60 + (W - 120) * T / TOTAL, 78, 4, fill=GOLD)
    c.text(W / 2, 130, "@aiwithsufi", 32, fade(GOLD, 0.9), "Medium")
    lab = sc.get("label")
    if lab:
        a = ease(t / 0.5); w = c.tw(lab, 28) + 60
        c.rrect(W / 2 - w / 2, 190, W / 2 + w / 2, 244, 27, fill=fade(CARD2, a), outline=fade(GOLD, a), width=2)
        c.text(W / 2, 217, lab, 28, fade(TEXT, a))

CHAR = {
    "A": dict(skin=(196, 138, 98), hair=(28, 22, 20), shirt=GOLD, beard=True, long=False),
    "B": dict(skin=(214, 164, 124), hair=(58, 34, 26), shirt=TEXT, beard=False, long=True),
}
_chars = {}
def character(c, x, y, r, who, talking, level, T, dim):
    """Flat illustrated host avatar; mouth moves with the voice level, eyes blink."""
    st = CHAR.get(who, CHAR["A"]); S = int(2 * r * SS); im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    u = S / 200.0
    def E(cx, cy, rx, ry, col): d.ellipse([(cx - rx) * u, (cy - ry) * u, (cx + rx) * u, (cy + ry) * u], fill=col)
    E(100, 100, 100, 100, CARD2 + (255,))
    if st["long"]: d.rounded_rectangle([46 * u, 50 * u, 154 * u, 175 * u], radius=50 * u, fill=st["hair"])
    E(100, 210, 78, 62, st["shirt"])                                   # shoulders
    d.rectangle([86 * u, 128 * u, 114 * u, 160 * u], fill=st["skin"])   # neck
    E(100, 98, 46, 54, st["skin"])                                      # face
    if st["beard"]: d.chord([56 * u, 70 * u, 144 * u, 156 * u], 10, 170, fill=st["hair"]); E(100, 112, 30, 22, st["skin"])
    d.chord([52 * u, 36 * u, 148 * u, 112 * u], 180, 360, fill=st["hair"])  # hair top
    blink = (T * 0.31 + (0.5 if who == "B" else 0)) % 1.0 < 0.04
    for ex in (82, 118):
        if blink: d.line([(ex - 6) * u, 98 * u, (ex + 6) * u, 98 * u], fill=(30, 22, 20), width=max(1, int(3 * u)))
        else: E(ex, 98, 5, 6.5, (30, 22, 20))
    mh = 3 + 15 * level if talking else 2.5
    E(100, 126, 11 if talking else 9, mh, (110, 50, 46))
    m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).ellipse([0, 0, S - 1, S - 1], fill=int(255 * (0.45 if dim else 1.0)))
    c.im.paste(im.convert("RGB"), (c.s(x - r), c.s(y - r)), m)
    if talking: c.circle(x, y, r + 7, outline=GOLD if who == "A" else TEXT, width=4)

def caption(c, sc, t, ctx=None, T=0.0):
    cur = None
    for ln in sc["lines"]:
        if ln["start"] - 0.05 <= t <= ln["end"] + 0.25: cur = ln
    ctx = ctx or {}; spk = ctx.get("speakers") or {}
    env = ctx.get("_env") or []; fi = int(T * FPS); level = env[min(len(env) - 1, fi)] if env else 0.3
    duo = len(spk) >= 2
    if duo:  # both characters always on screen; the speaker is lit
        who_now = cur.get("who", "A") if cur else None
        for who, (x, y) in (("B", (130, 1500)), ("A", (950, 1500))):
            character(c, x, y, 78, who, who_now == who, level, T, who_now not in (None, who))
            c.text(x, y + 104, spk[who]["name"], 26, fade(GOLD if who == "A" else TEXT, 0.9), "SemiBold")
    if not cur: return
    a = ease((t - cur["start"] + 0.05) / 0.2); size = 40 if duo else 44; wsp = c.tw(" ", size) + 4
    maxw = 640 if duo else 900
    words = cur["cap"].split(); rows = [[]]
    for w in words:
        cand = rows[-1] + [w]
        if sum(c.tw(x, size) for x in cand) + wsp * (len(cand) - 1) > maxw and rows[-1]: rows.append([w])
        else: rows[-1] = cand
    lh = size + 16; widths = [sum(c.tw(x, size) for x in r) + wsp * (len(r) - 1) for r in rows]
    bw = max(widths) + 64; bh = (len(rows) - 1) * lh + 92
    who = cur.get("who", "A"); accent = GOLD if who == "A" else TEXT
    if duo:
        cy = 1500 + (1 - a) * 14
        bx0 = 238 if who == "B" else 842 - bw
        c.rrect(bx0, cy - bh / 2, bx0 + bw, cy + bh / 2, 26, fill=fade(CARD2, a), outline=fade(accent, 0.7 * a), width=2)
        tx = bx0 if who == "B" else bx0 + bw
        dirn = -1 if who == "B" else 1
        c.poly([(tx, cy - 16), (tx, cy + 16), (tx + dirn * 26, cy)], fade(accent, 0.7 * a))
        cx = bx0 + bw / 2; y0 = cy - (len(rows) - 1) * lh / 2
    else:
        y0 = 1500 - (len(rows) - 1) * lh / 2 + (1 - a) * 16; cx = W / 2
        c.rrect(cx - bw / 2, y0 - 50, cx + bw / 2, y0 + (len(rows) - 1) * lh + 50, 24, fill=fade(CARD, 0.95 * a))
    n = len(words); dur = max(0.3, cur["end"] - cur["start"]); idx = 0
    for i, r in enumerate(rows):
        x = cx - widths[i] / 2
        for w in r:
            ws = cur["start"] + dur * idx / n
            core = w.strip(".,:;!?'\"()")
            hi = len(core) > 1 and core.isupper() and core.replace("-", "").replace("'", "").isalpha()
            if t < ws: col = fade(MUTED, 0.7 * a)
            elif t < ws + dur / n: col = fade(GOLD, a)
            else: col = fade(GOLD if hi else TEXT, a)
            c.text(x, y0 + i * lh, w, size, col, anchor="lm"); x += c.tw(w, size) + wsp; idx += 1

# ---------- scene types ----------
def s_hook(c, t, sc, ctx):
    L = sc["lines"]; a = ease(t / 0.6)
    avatar(c, W / 2, 560, 220 * (0.88 + 0.12 * a), t, a)
    t1 = L[1]["start"] if len(L) > 1 else L[0]["start"] + 1.0
    chips = sc.get("chips", []); out = 1 - ease((t - t1) / 0.4)
    for i, ch in enumerate(chips):
        p = back((t - L[0]["start"] - i * 0.5) / 0.45)
        if p <= 0 or out <= 0: continue
        x = W / 2 + (i - (len(chips) - 1) / 2) * 330; pa = clamp(p) * out
        w = c.tw(ch, 40) + 56
        c.rrect(x - w / 2, 920, x + w / 2, 1000, 18, fill=fade(CARD2, pa), outline=fade(GOLD if i == len(chips) - 1 else LINE, pa), width=3)
        c.text(x, 960, ch, 40, fade(TEXT, pa))
    q = back((t - t1) / 0.6)
    if q > 0:
        qa = clamp(q); size = c.fit(sc["title"], 100, 940)
        c.text(W / 2, 1010, sc["title"], size * max(q, 0.3), fade(TEXT, qa))
        if sc.get("subtitle"): c.text(W / 2, 1105, sc["subtitle"], 36, fade(MUTED, ease((t - t1 - 0.4) / 0.5)), "Medium")

def s_flow(c, t, sc, ctx):
    nodes = sc["nodes"]; n = len(nodes); ts = reveal_times(nodes, sc)
    top, bot = 330, 1300; gap = (bot - top) / max(1, n); h = min(130, gap - 40)
    shown = [i for i in range(n) if t >= ts[i]]
    for i, nd in enumerate(nodes):
        p = ease((t - ts[i]) / 0.5)
        if p <= 0: continue
        y = top + gap * (i + 0.5)
        if i > 0: c.arrow(W / 2, y - gap + h / 2 + 6, W / 2, y - h / 2 - 8, fade(MUTED, p), 4)
        node(c, W / 2 + (1 - p) * 60, y, nd["t"], nd.get("s"), p, shown and i == shown[-1], w=760, h=h, size=42)

def s_cycle(c, t, sc, ctx):
    nodes = sc["nodes"]; n = len(nodes); ts = reveal_times(nodes, sc)
    cx, cy, R = W / 2, 790, 330
    if sc.get("center"):
        a = ease(t / 0.5); w = c.tw(sc["center"], 44) + 70
        c.rrect(cx - w / 2, cy - 55, cx + w / 2, cy + 55, 55, fill=fade(GOLD, a)); c.text(cx, cy, sc["center"], 44, fade(BG, a) if a > 0.05 else BG)
    angs = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    all_in = t >= ts[-1] + 0.4
    for i in range(n):
        p = ease((t - ts[i]) / 0.5)
        if p <= 0: continue
        a0, a1 = angs[i] + 0.38, angs[(i + 1) % n] - 0.38
        if a1 < a0: a1 += 2 * math.pi
        if t >= ts[(i + 1) % n] or (all_in and i == n - 1):
            pts = [(cx + R * math.cos(a0 + (a1 - a0) * k / 24), cy + R * math.sin(a0 + (a1 - a0) * k / 24)) for k in range(25)]
            c.line(pts, fade(LINE, 1), 4)
            (x1, y1), (x0, y0) = pts[-1], pts[-3]; c.arrow(x0, y0, x1, y1, fade(MUTED, 1), 4, 18)
    if all_in:
        ph = ((t - ts[-1]) * 0.35) % 1.0; ang = angs[0] + 2 * math.pi * ph
        c.circle(cx + R * math.cos(ang), cy + R * math.sin(ang), 12, fill=GOLD)
        active = int(ph * n + 0.5) % n
    else:
        active = max([i for i in range(n) if t >= ts[i]], default=-1)
    for i, nd in enumerate(nodes):
        p = back((t - ts[i]) / 0.5)
        if p <= 0: continue
        x, y = cx + R * math.cos(angs[i]), cy + R * math.sin(angs[i])
        node(c, x, y, nd["t"], nd.get("s"), clamp(p), i == active, size=40)

def s_hub(c, t, sc, ctx):
    nodes = sc["nodes"]; n = len(nodes); ts = reveal_times(nodes, sc)
    cx, cy, R = W / 2, 800, 390; a = ease(t / 0.5)
    angs = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    for i in range(n):
        p = ease((t - ts[i]) / 0.5)
        if p <= 0: continue
        x, y = cx + R * math.cos(angs[i]), cy + R * math.sin(angs[i])
        ex, ey = cx + (x - cx) * p, cy + (y - cy) * p
        c.line([(cx, cy), (ex, ey)], fade(LINE, 1), 4)
        if p >= 1:
            ph = ((t - ts[i]) * 0.6 + i * 0.3) % 1.0
            c.circle(cx + (x - cx) * ph, cy + (y - cy) * ph, 8, fill=GOLD)
    w = c.tw(sc["center"], 46) + 80
    c.rrect(cx - w / 2, cy - 62, cx + w / 2, cy + 62, 30, fill=fade(GOLD, a)); c.text(cx, cy, sc["center"], 46, fade(BG, a) if a > 0.05 else BG)
    last = max([i for i in range(n) if t >= ts[i]], default=-1)
    for i, nd in enumerate(nodes):
        p = back((t - ts[i]) / 0.5)
        if p <= 0: continue
        node(c, cx + R * math.cos(angs[i]), cy + R * math.sin(angs[i]), nd["t"], nd.get("s"), clamp(p), i == last, size=36)

def s_list(c, t, sc, ctx):
    items = sc["items"]; n = len(items); ts = reveal_times(items, sc)
    top, bot = 320, 1330; gap = min(150, (bot - top) / max(1, n)); y0 = top + ((bot - top) - gap * n) / 2
    last = max([i for i in range(n) if t >= ts[i]], default=-1)
    for i, it in enumerate(items):
        p = ease((t - ts[i]) / 0.45)
        if p <= 0: continue
        y = y0 + gap * (i + 0.5); x0 = 90 + (1 - p) * 60; hi = i == last
        c.rrect(x0, y - gap / 2 + 10, W - 90, y + gap / 2 - 10, 22, fill=fade(CARD2, p), outline=fade(GOLD if hi else LINE, p), width=3 if hi else 2)
        c.text(x0 + 60, y, f"{i + 1:02d}", 44, fade(GOLD, p))
        size = c.fit(it["t"], 44, W - 90 - x0 - 170)
        if it.get("s"):
            c.text(x0 + 120, y - 18, it["t"], size, fade(TEXT, p), anchor="lm"); c.text(x0 + 120, y + 26, it["s"], 30, fade(MUTED, p), "Medium", anchor="lm")
        else:
            c.text(x0 + 120, y, it["t"], size, fade(TEXT, p), anchor="lm")

def s_compare(c, t, sc, ctx):
    rows = sc["rows"]; n = len(rows); ts = reveal_times([{"at": r[2]} if len(r) > 2 else {} for r in rows], sc)
    a = ease(t / 0.5); xl, xr = 300, 780
    for x, lab, hi in ((xl, sc["left"], False), (xr, sc["right"], True)):
        w = 400; c.rrect(x - w / 2, 330, x + w / 2, 430, 24, fill=fade(GOLD if hi else CARD2, a), outline=fade(LINE, a), width=2)
        c.text(x, 380, lab, c.fit(lab, 44, w - 40), fade(BG if hi else TEXT, a) if a > 0.05 else BG)
    c.text(W / 2, 380, "vs", 36, fade(MUTED, a), "Medium")
    gap = min(150, 860 / max(1, n))
    for i, r in enumerate(rows):
        p = ease((t - ts[i]) / 0.45)
        if p <= 0: continue
        y = 500 + gap * (i + 0.5)
        c.line([(110, y - gap / 2), (W - 110, y - gap / 2)], fade(LINE, p), 2)
        c.text(xl, y, r[0], c.fit(r[0], 38, 400, "SemiBold"), fade(MUTED, p), "SemiBold")
        c.text(xr, y, r[1], c.fit(r[1], 38, 400), fade(TEXT, p))

def s_bars(c, t, sc, ctx):
    bars = sc["bars"]; n = len(bars); ts = reveal_times(bars, sc); a = ease(t / 0.5)
    if sc.get("title"): c.text(W / 2, 360, sc["title"], c.fit(sc["title"], 44, 940), fade(TEXT, a))
    mx = max(b["v"] for b in bars); gap = min(140, 860 / max(1, n))
    for i, b in enumerate(bars):
        p = ease((t - ts[i]) / 0.7)
        if p <= 0: continue
        y = 470 + gap * (i + 0.5); L = 560 * b["v"] / mx * p; best = b["v"] == mx
        c.text(270, y, b["t"], c.fit(b["t"], 38, 220), fade(TEXT, p), anchor="rm")
        c.rrect(300, y - 30, 300 + max(L, 10), y + 30, 14, fill=fade(GOLD if best else MUTED, p))
        c.text(320 + L, y, f'{b["v"]}{b.get("unit", "")}', 34, fade(TEXT, p), anchor="lm")

def s_outro(c, t, sc, ctx):
    L = sc["lines"]; a = ease(t / 0.5)
    avatar(c, W / 2, 440, 150, t, a)
    recap = sc.get("recap", []); d0 = (L[0]["end"] - L[0]["start"])
    for i, s in enumerate(recap):
        p = back((t - 0.3 - i * d0 * 0.8 / max(1, len(recap))) / 0.5)
        if p <= 0: continue
        pa = clamp(p); y = 690 + i * 105; w = 400 * p
        c.rrect(W / 2 - w, y - 40, W / 2 + w, y + 40, 40, fill=fade(CARD2, pa), outline=fade(GOLD, pa), width=2)
        c.text(W / 2, y, f"{i + 1}. {s}", c.fit(f"{i + 1}. {s}", 40, 760) * max(p, 0.2), fade(TEXT, pa))
    t1 = L[-1]["start"]; q = back((t - t1) / 0.6)
    if q > 0:
        qa = clamp(q); pulse = 1 + 0.03 * math.sin(t * 6)
        if ctx.get("next"): c.text(W / 2, 1210, f'NEXT: {ctx["next"].upper()}', 46, fade(GOLD, qa))
        w = 330 * q * pulse
        c.rrect(W / 2 - w, 1260, W / 2 + w, 1350, 45, fill=fade(GOLD, qa))
        c.text(W / 2, 1305, "FOLLOW @aiwithsufi", 42 * max(q, 0.2) * pulse, fade(BG, qa) if qa > 0.05 else BG)

_mono = {}
def mono(size):
    if size not in _mono: _mono[size] = ImageFont.truetype(fetch(MONO), int(size * SS))
    return _mono[size]

def s_code(c, t, sc, ctx):
    """Typewriter code block. sc: {"title": "...", "code": "multi-line text", "at": line index to start typing, "note": "optional caption under"}"""
    L = sc["lines"]; a = ease(t / 0.5)
    if sc.get("title"): c.text(W / 2, 340, sc["title"], c.fit(sc["title"], 44, 940), fade(TEXT, a))
    code = sc["code"].split("\n"); st = L[min(int(sc.get("at", 0)), len(L) - 1)]["start"] + 0.2
    span = max(1.5, (L[-1]["end"] - st) * 0.6); total = sum(len(l) for l in code)
    shown = int(total * clamp((t - st) / span)); fs = 34 if max(len(l) for l in code) <= 38 else 28
    lh = fs * 1.55; h = len(code) * lh + 90; y0 = 420
    c.rrect(80, y0, W - 80, y0 + h, 24, fill=fade(CARD, a), outline=fade(LINE, a), width=2)
    for k, col in enumerate((GOLD, MUTED, LINE)): c.circle(120 + k * 30, y0 + 32, 8, fill=fade(col, a))
    y = y0 + 80; n = 0
    for ln in code:
        vis = ln[:max(0, min(len(ln), shown - n))]; n += len(ln)
        if vis:
            col = GOLD if vis.strip().startswith(('"tool"', '"name"', "tool", "#")) else TEXT
            c.d.text((c.s(120), c.s(y)), vis, font=mono(fs), fill=fade(col, a), anchor="lm")
        if 0 <= shown - (n - len(ln)) <= len(ln) and int(t * 2) % 2 == 0 and shown < total:
            cx = 120 + c.d.textlength(vis, font=mono(fs)) / SS + 4
            c.rrect(cx, y - fs * 0.6, cx + fs * 0.55, y + fs * 0.6, 2, fill=GOLD)
        y += lh
    if sc.get("note"): c.text(W / 2, y0 + h + 70, sc["note"], c.fit(sc["note"], 34, 920, "SemiBold"), fade(MUTED, ease((t - st - span) / 0.6)), "SemiBold")

def s_quiz(c, t, sc, ctx):
    """Interactive 'Pause & guess' moment. sc: {"question", "options": [3-4], "answer": index, "reveal": line index}"""
    L = sc["lines"]; a = ease(t / 0.5); rv = L[min(int(sc.get("reveal", len(L) - 1)), len(L) - 1)]["start"]
    c.rrect(W / 2 - 170, 300, W / 2 + 170, 356, 28, fill=fade(GOLD, a)); c.text(W / 2, 328, "PAUSE & GUESS", 30, fade(BG, a) if a > 0.05 else BG)
    q = sc["question"]; size = c.fit(q, 50, 900)
    words = q.split(); rows = [""]
    for w in words:
        tst = (rows[-1] + " " + w).strip()
        if c.tw(tst, 46) > 900 and rows[-1]: rows.append(w)
        else: rows[-1] = tst
    for i, r in enumerate(rows): c.text(W / 2, 430 + i * 60, r, 46, fade(TEXT, a))
    y = 430 + len(rows) * 60 + 40; opts = sc["options"]; revealed = t >= rv
    for i, o in enumerate(opts):
        p = back((t - 0.4 - i * 0.25) / 0.5)
        if p <= 0: continue
        pa = clamp(p); right = i == sc["answer"]; yy = y + i * 130
        if revealed:
            fill = GOLD if right else CARD; txt = BG if right else MUTED; out = GOLD if right else LINE
        else:
            fill = CARD2; txt = TEXT; out = LINE
        c.rrect(140, yy, W - 140, yy + 104, 52, fill=fade(fill, pa), outline=fade(out, pa), width=3)
        c.circle(200, yy + 52, 30, fill=fade(BG if (revealed and right) else CARD, pa))
        c.text(200, yy + 52, "ABCD"[i], 30, fade(GOLD, pa))
        c.text(250, yy + 52, o, c.fit(o, 38, W - 140 - 270), fade(txt, pa) if pa > 0.05 else BG, anchor="lm")
    if not revealed:  # countdown ring for the last 3 seconds before the reveal
        left = rv - t
        if left <= 3.2:
            cx, cy, R = W / 2, y + len(opts) * 130 + 80, 46; frac = clamp(left / 3.0)
            c.circle(cx, cy, R, outline=LINE, width=6)
            c.d.arc([c.s(cx - R), c.s(cy - R), c.s(cx + R), c.s(cy + R)], -90, -90 + 360 * frac, fill=GOLD, width=c.s(6))
            c.text(cx, cy, str(max(1, math.ceil(left))), 44, GOLD)
    else:
        c.text(W / 2, y + len(opts) * 130 + 80, "Got it right? Comment below", 34, fade(MUTED, ease((t - rv - 0.5) / 0.5)), "SemiBold")

FN = {"quiz": s_quiz, "code": s_code, "hook": s_hook, "flow": s_flow, "cycle": s_cycle, "hub": s_hub, "list": s_list, "compare": s_compare, "bars": s_bars, "outro": s_outro}

# ---------- voice ----------
def voiceover(spec, work):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(fetch(os.path.join(CACHE, "kokoro-v1.0.onnx")), fetch(os.path.join(CACHE, "voices-v1.0.bin")))
    LEAD, GAP, TAIL = 0.35, 0.3, 0.5; parts = []; SR = 24000
    spk = spec.get("speakers") or {"A": {"name": "", "voice": VOICE}}
    for sc in spec["scenes"]:
        seg = [np.zeros(int(LEAD * SR), np.float32)]; t = LEAD
        for i, ln in enumerate(sc["lines"]):
            who = ln.get("who", "A"); ln["who"] = who
            s, sr = k.create(ln["vo"], voice=spk.get(who, spk["A"])["voice"], speed=spec.get("speed", SPEED), lang="en-us")
            idx = np.where(np.abs(s) > 0.01)[0]; s = s[max(0, idx[0] - 600): idx[-1] + 1200].astype(np.float32)
            d = len(s) / SR; ln["start"], ln["end"] = t, t + d; seg.append(s); t += d
            g = GAP if i < len(sc["lines"]) - 1 else TAIL; seg.append(np.zeros(int(g * SR), np.float32)); t += g
        a = np.concatenate(seg); sc["dur"] = len(a) / SR; parts.append(a)
    full = np.concatenate(parts)
    hop = SR // FPS; spec["_env"] = [float(np.sqrt(np.mean(full[i:i + hop] ** 2))) for i in range(0, len(full), hop)]
    mx = max(spec["_env"]) or 1.0; spec["_env"] = [min(1.0, v / mx * 1.6) for v in spec["_env"]]
    raw = os.path.join(work, "vo_raw.wav"); sf.write(raw, full, SR)
    vo = os.path.join(work, "vo.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    "highpass=f=70,equalizer=f=180:t=q:w=1:g=1.5,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120,loudnorm=I=-15:TP=-1.5",
                    "-ar", "44100", "-ac", "1", vo], check=True)
    v, sr = sf.read(vo); n = len(v); tt = np.arange(n) / sr; pad = np.zeros(n)
    chords = [[220, 261.63, 329.63], [174.61, 220, 261.63], [196, 246.94, 293.66], [164.81, 207.65, 246.94]]
    for i in range(int(n / sr / 4) + 1):
        s0 = int(i * 4 * sr); e0 = min(n, int((i + 1) * 4 * sr) + sr)
        if s0 >= n: break
        x = np.arange(e0 - s0) / sr; env = np.minimum(1, x) * np.minimum(1, (e0 - s0) / sr - x)
        for f in chords[i % 4]: pad[s0:e0] += env * np.sin(2 * np.pi * f * x) / 3
    pad *= 0.035 * np.minimum(1, tt / 1.5) * np.minimum(1, (tt[-1] - tt) / 1.5)
    m = v * 0.97 + pad; m /= max(1, np.abs(m).max() / 0.97)
    out = os.path.join(work, "mix.wav"); sf.write(out, m, sr); return out

# ---------- render ----------
def frame(spec, idx, f, TOTAL):
    sc = spec["scenes"][idx]; T0 = sum(s["dur"] for s in spec["scenes"][:idx]); t = f / FPS
    c = Canvas(); chrome(c, sc, t, T0 + t, TOTAL); FN[sc["type"]](c, t, sc, spec); caption(c, sc, t, spec, T0 + t)
    im = c.out(); fi = clamp(t / 0.3) if idx > 0 else 1.0; fo = clamp((sc["dur"] - t) / 0.25); k = min(fi, fo)
    if k < 1: im = Image.blend(Image.new("RGB", (W, H), BG), im, k)
    return im

def render_scene(spec, idx, path, TOTAL):
    n = round(spec["scenes"][idx]["dur"] * FPS); tmp = path[:-4] + "_tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(n): p.stdin.write(frame(spec, idx, f, TOTAL).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, path)

def main():
    src, out = sys.argv[1], sys.argv[2]; preview = "--preview" in sys.argv
    spec = json.load(open(src)); work = tempfile.mkdtemp(prefix="reel_")
    audio = voiceover(spec, work); TOTAL = sum(s["dur"] for s in spec["scenes"])
    json.dump(spec, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    print(f"voiceover {TOTAL:.1f}s, work dir {work}")
    if preview:
        ims = []
        for i, sc in enumerate(spec["scenes"]):
            ims.append(frame(spec, i, int((sc["lines"][-1]["end"] - 0.1) * FPS), TOTAL).resize((270, 480)))
        cols = 6; rows = (len(ims) + cols - 1) // cols; m = Image.new("RGB", (270 * cols, 480 * rows))
        for k, im in enumerate(ims): m.paste(im, ((k % cols) * 270, (k // cols) * 480))
        m.save(out.replace(".mp4", "_preview.jpg"), quality=88); print("preview", out.replace(".mp4", "_preview.jpg")); return
    from concurrent.futures import ProcessPoolExecutor
    paths = [os.path.join(work, f"s{i:02d}.mp4") for i in range(len(spec["scenes"]))]
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as ex:
        list(ex.map(render_scene, [spec] * len(paths), range(len(paths)), paths, [TOTAL] * len(paths)))
    lst = os.path.join(work, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in paths))
    vid = os.path.join(work, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"wrote {out} ({TOTAL:.1f}s)")

if __name__ == "__main__":
    main()
