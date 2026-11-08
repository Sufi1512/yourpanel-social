"""Explainer carousel (educational post) for @aiwithsufi.

Usage:  python3 explainer_carousel.py post.json OUT_DIR
post.json = {"title": "RAG", "slides": [ ...max 10... ]}  slide types:
  {"type": "cover",   "kicker": "AI CONCEPT", "title": "RAG", "subtitle": "How AI answers from your documents"}
  {"type": "point",   "title": "The problem", "body": "1-3 short sentences", "bullets": ["optional", "max 4"]}
  {"type": "steps",   "title": "How it works", "steps": [{"t": "Chunk", "s": "split documents"}, ...max 6]}
  {"type": "compare", "title": "Fine-tuning vs RAG", "left": "Fine-tuning", "right": "RAG", "rows": [["teaches style", "adds knowledge"], ...max 5]}
  {"type": "recap",   "title": "Remember", "points": ["...", "..."]}
  {"type": "cta",     "next": "Vector databases"}
Writes OUT_DIR/01.jpg ... (1080x1350). Style: Charcoal & Gold + Montserrat, same as the Reels.
"""
import json, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG = (20, 20, 22); CARD = (32, 32, 35); CARD2 = (38, 38, 42); LINE = (70, 70, 74)
TEXT = (240, 236, 226); MUTED = (160, 156, 148); GOLD = (196, 164, 104)
HERE = os.path.dirname(os.path.abspath(__file__)); FONT = os.path.join(HERE, "Montserrat.ttf")
_fc = {}

def font(size, weight="Bold"):
    if not os.path.exists(FONT):
        urllib.request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf", FONT)
    k = (size, weight)
    if k not in _fc:
        f = ImageFont.truetype(FONT, size); f.set_variation_by_name(weight); _fc[k] = f
    return _fc[k]

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    return lines

def fit(d, text, weight, maxw, max_lines, start, minimum):
    s = start
    while s >= minimum:
        f = font(s, weight); ls = wrap(d, text, f, maxw)
        if len(ls) <= max_lines: return f, ls
        s -= 2
    f = font(minimum, weight); return f, wrap(d, text, f, maxw)[:max_lines]

def para(d, x, y, text, weight, color, maxw, max_lines, start, minimum, lh=1.35):
    f, ls = fit(d, text, weight, maxw, max_lines, start, minimum)
    for l in ls: d.text((x, y), l, font=f, fill=color, anchor="ls"); y += int(f.size * lh)
    return y

def base(page, total, title):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.text((80, 90), "@aiwithsufi", font=font(30, "SemiBold"), fill=GOLD, anchor="lm")
    d.text((W - 80, 90), title.upper(), font=fit(d, title.upper(), "Medium", 520, 1, 26, 18)[0], fill=MUTED, anchor="rm")
    d.line([(80, 140), (W - 80, 140)], fill=LINE, width=2)
    x0 = W / 2 - (total - 1) * 14
    for i in range(total):
        r = 7 if i == page else 5
        d.ellipse([x0 + i * 28 - r, H - 80 - r, x0 + i * 28 + r, H - 80 + r], fill=GOLD if i == page else LINE)
    if 0 < page < total - 1:
        d.text((W - 80, H - 150), f"{page + 1}/{total}", font=font(26, "Medium"), fill=MUTED, anchor="rs")
    return im, d

def heading(d, title, n=None):
    y = 290
    if n is not None:
        d.text((80, 270), f"{n:02d}", font=font(90, "ExtraBold"), fill=GOLD, anchor="ls"); y = 390
    return para(d, 80, y, title, "ExtraBold", TEXT, W - 160, 3, 66, 44, 1.15) + 30

def s_cover(s, page, total, title):
    im, d = base(page, total, title)
    if s.get("kicker"):
        k = s["kicker"].upper(); tw = d.textlength(k, font=font(28, "Bold")) + 48
        d.rounded_rectangle([80, 330, 80 + tw, 386], radius=28, outline=GOLD, width=2)
        d.text((80 + tw / 2, 358), k, font=font(28, "Bold"), fill=GOLD, anchor="mm")
    y = para(d, 80, 560, s["title"], "ExtraBold", TEXT, W - 160, 3, 130, 70, 1.05)
    para(d, 84, y + 40, s.get("subtitle", ""), "Medium", GOLD, W - 160, 3, 48, 34, 1.3)
    d.text((W - 80, H - 150), "Swipe  →", font=font(36, "Bold"), fill=GOLD, anchor="rs")
    return im

def s_point(s, page, total, title, n):
    im, d = base(page, total, title); y = heading(d, s["title"], n)
    if s.get("body"): y = para(d, 80, y + 20, s["body"], "Medium", MUTED, W - 160, 7, 40, 30, 1.45) + 20
    for b in s.get("bullets", [])[:4]:
        f, ls = fit(d, b, "SemiBold", W - 260, 2, 36, 28); h = 50 + len(ls) * int(f.size * 1.35)
        d.rounded_rectangle([80, y, W - 80, y + h], radius=18, fill=CARD)
        d.ellipse([110, y + h / 2 - 8, 126, y + h / 2 + 8], fill=GOLD)
        yy = y + 25 + f.size
        for l in ls: d.text((150, yy), l, font=f, fill=TEXT, anchor="ls"); yy += int(f.size * 1.35)
        y += h + 18
    return im

def s_steps(s, page, total, title):
    im, d = base(page, total, title); y = heading(d, s["title"])
    steps = s["steps"][:6]; gap = min(150, (H - 220 - y) / max(1, len(steps)))
    for i, st in enumerate(steps):
        cy = y + gap * i + gap / 2
        if i > 0: d.line([(130, cy - gap + 45), (130, cy - 45)], fill=LINE, width=4)
        d.ellipse([90, cy - 40, 170, cy + 40], fill=GOLD)
        d.text((130, cy), str(i + 1), font=font(40, "ExtraBold"), fill=BG, anchor="mm")
        if st.get("s"):
            d.text((200, cy - 16), st["t"], font=fit(d, st["t"], "Bold", W - 290, 1, 42, 30)[0], fill=TEXT, anchor="lm")
            d.text((200, cy + 28), st["s"], font=fit(d, st["s"], "Medium", W - 290, 1, 32, 24)[0], fill=MUTED, anchor="lm")
        else:
            d.text((200, cy), st["t"], font=fit(d, st["t"], "Bold", W - 290, 1, 42, 30)[0], fill=TEXT, anchor="lm")
    return im

def s_compare(s, page, total, title):
    im, d = base(page, total, title); y = heading(d, s["title"])
    xl, xr, cw = 310, 770, 420
    for x, lab, hi in ((xl, s["left"], False), (xr, s["right"], True)):
        d.rounded_rectangle([x - cw / 2, y, x + cw / 2, y + 90], radius=22, fill=GOLD if hi else CARD2)
        d.text((x, y + 45), lab, font=fit(d, lab, "Bold", cw - 40, 1, 40, 26)[0], fill=BG if hi else TEXT, anchor="mm")
    y += 120; rows = s["rows"][:5]; gap = min(140, (H - 220 - y) / max(1, len(rows)))
    for i, r in enumerate(rows):
        cy = y + gap * i + gap / 2; d.line([(80, cy - gap / 2), (W - 80, cy - gap / 2)], fill=LINE, width=2)
        for x, txt, col, wt in ((xl, r[0], MUTED, "SemiBold"), (xr, r[1], TEXT, "Bold")):
            f, ls = fit(d, txt, wt, cw - 30, 2, 34, 24); yy = cy - (len(ls) - 1) * f.size * 0.65
            for l in ls: d.text((x, yy), l, font=f, fill=col, anchor="mm"); yy += int(f.size * 1.3)
    return im

def s_recap(s, page, total, title):
    im, d = base(page, total, title); y = heading(d, s.get("title", "Remember"))
    for i, p in enumerate(s["points"][:5]):
        f, ls = fit(d, p, "SemiBold", W - 300, 2, 38, 28); h = 60 + len(ls) * int(f.size * 1.35)
        d.rounded_rectangle([80, y, W - 80, y + h], radius=20, outline=GOLD, width=2)
        d.text((130, y + h / 2), f"{i + 1}", font=font(44, "ExtraBold"), fill=GOLD, anchor="mm")
        yy = y + 30 + f.size
        for l in ls: d.text((190, yy), l, font=f, fill=TEXT, anchor="ls"); yy += int(f.size * 1.35)
        y += h + 22
    return im

def s_cta(s, page, total, title):
    im, d = base(page, total, title)
    d.text((W / 2, 470), "Found this useful?", font=font(66, "ExtraBold"), fill=TEXT, anchor="ms")
    d.text((W / 2, 550), "Save it  ·  Share it  ·  Ask below", font=font(38, "Medium"), fill=MUTED, anchor="ms")
    if s.get("next"):
        d.text((W / 2, 690), "NEXT UP", font=font(30, "Bold"), fill=GOLD, anchor="ms")
        para_f, ls = fit(d, s["next"], "ExtraBold", W - 200, 2, 56, 40)
        y = 760
        for l in ls: d.text((W / 2, y), l, font=para_f, fill=TEXT, anchor="ms"); y += int(para_f.size * 1.2)
    d.rounded_rectangle([W / 2 - 330, 950, W / 2 + 330, 1050], radius=50, fill=GOLD)
    d.text((W / 2, 1000), "FOLLOW @aiwithsufi", font=font(44, "ExtraBold"), fill=BG, anchor="mm")
    return im

def apply_palette(name):
    from palettes import PALETTES
    v = PALETTES[name]; g = globals()
    g.update(BG=v["BG"], CARD=v["CARD"], CARD2=v["CARD2"], LINE=v["LINE"], TEXT=v["TEXT"], MUTED=v["MUTED"], GOLD=v["ACCENT"])

def main(src, out):
    post = json.load(open(src)); os.makedirs(out, exist_ok=True)
    sys.path.insert(0, HERE)
    from palettes import for_date, date_from_path
    day = post.get("date") or date_from_path(src)
    apply_palette(post.get("theme") or (for_date(day) if day else "sand_espresso"))
    slides = post["slides"][:10]; total = len(slides); title = post.get("title", ""); n = 0
    for i, s in enumerate(slides):
        t = s["type"]
        if t == "point": n += 1; im = s_point(s, i, total, title, n)
        else: im = {"cover": s_cover, "steps": s_steps, "compare": s_compare, "recap": s_recap, "cta": s_cta}[t](s, i, total, title)
        im.save(os.path.join(out, f"{i + 1:02d}.jpg"), quality=92, subsampling=0)
    print(f"wrote {total} slides to {out}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
