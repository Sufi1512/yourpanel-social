"""Daily AI news carousel for @aiwithsufi.

Usage:  python3 news_carousel.py stories.json OUT_DIR
stories.json = {"date": "2026-11-08", "stories": [
    {"tag": "MODEL LAUNCH", "headline": "...", "body": "...", "why": "...", "source": "Reuters"}, ...]}
Writes OUT_DIR/01.jpg ... (1080x1350, Instagram 4:5): cover, one slide per story, closing slide.
Style: Charcoal & Gold, Montserrat (same as the explainer Reels).
"""
import json, os, sys, datetime, urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
# Palettes: TEXT = main text, MUTED = body text, GOLD = the single accent colour.
THEMES = {
    "charcoal_gold":  dict(BG=(20, 20, 22), CARD=(32, 32, 35), LINE=(70, 70, 74), IVORY=(240, 236, 226), MUTED=(160, 156, 148), GOLD=(196, 164, 104)),
    "ivory_maroon":   dict(BG=(246, 242, 233), CARD=(236, 230, 218), LINE=(205, 198, 184), IVORY=(28, 28, 30), MUTED=(96, 90, 82), GOLD=(128, 32, 40)),
    "newsroom_red":   dict(BG=(250, 250, 248), CARD=(238, 238, 236), LINE=(210, 210, 206), IVORY=(17, 17, 17), MUTED=(85, 85, 85), GOLD=(200, 30, 30)),
    "forest_cream":   dict(BG=(22, 44, 36), CARD=(31, 58, 48), LINE=(60, 90, 78), IVORY=(244, 238, 222), MUTED=(190, 196, 180), GOLD=(222, 184, 110)),
    "plum_blush":     dict(BG=(44, 24, 46), CARD=(60, 36, 62), LINE=(92, 64, 94), IVORY=(248, 238, 242), MUTED=(206, 188, 202), GOLD=(240, 164, 184)),
    "terracotta_sand":dict(BG=(176, 88, 58), CARD=(156, 74, 48), LINE=(206, 128, 98), IVORY=(255, 244, 228), MUTED=(250, 222, 200), GOLD=(255, 214, 160)),
    "graphite_tangerine": dict(BG=(40, 40, 40), CARD=(54, 54, 54), LINE=(84, 84, 84), IVORY=(246, 244, 240), MUTED=(176, 172, 166), GOLD=(244, 128, 52)),
    "blush_burgundy": dict(BG=(246, 228, 226), CARD=(238, 214, 212), LINE=(222, 192, 190), IVORY=(34, 20, 24), MUTED=(104, 80, 84), GOLD=(136, 28, 58)),
}
# One palette per weekday (Mon..Sun); NEWS_THEME overrides.
WEEKDAY_THEMES = ["charcoal_gold", "ivory_maroon", "newsroom_red", "forest_cream", "plum_blush", "terracotta_sand", "graphite_tangerine"]
THEME = os.environ.get("NEWS_THEME", "")

def set_theme(name):
    global THEME
    THEME = name
    globals().update(THEMES[name])

def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "Montserrat.ttf")
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
_fc = {}

def font(size, weight="Bold"):
    if not os.path.exists(FONT):
        urllib.request.urlretrieve(FONT_URL, FONT)
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

def fit_block(d, text, weight, maxw, max_lines, start, minimum):
    s = start
    while s >= minimum:
        f = font(s, weight); ls = wrap(d, text, f, maxw)
        if len(ls) <= max_lines: return f, ls
        s -= 2
    f = font(minimum, weight); return f, wrap(d, text, f, maxw)[:max_lines]

def chrome(d, page, total, date_label):
    d.text((80, 90), "@aiwithsufi", font=font(30, "SemiBold"), fill=GOLD, anchor="lm")
    d.text((W - 80, 90), date_label, font=font(28, "Medium"), fill=MUTED, anchor="rm")
    d.line([(80, 140), (W - 80, 140)], fill=LINE, width=2)
    x0 = W / 2 - (total - 1) * 14
    for i in range(total):
        r = 7 if i == page else 5
        d.ellipse([x0 + i * 28 - r, H - 80 - r, x0 + i * 28 + r, H - 80 + r], fill=GOLD if i == page else LINE)

def cover(date_label, n, total, teaser):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); chrome(d, 0, total, date_label)
    d.text((80, 470), "AI NEWS", font=font(150, "ExtraBold"), fill=IVORY, anchor="ls")
    d.text((80, 640), "TODAY", font=font(150, "ExtraBold"), fill=GOLD, anchor="ls")
    d.text((84, 730), f"{n} stories you should know", font=font(44, "Medium"), fill=IVORY, anchor="ls")
    y = 840; step = 70 if len(teaser) <= 4 else int(320 / len(teaser)); fs = min(36, step - 8)
    for i, t in enumerate(teaser):
        f, ls = fit_block(d, t, "SemiBold", W - 240, 1, fs, 22)
        d.text((80, y), f"{i + 1:02d}", font=font(fs, "ExtraBold"), fill=GOLD, anchor="ls")
        d.text((160, y), ls[0], font=f, fill=MUTED, anchor="ls"); y += step
    d.text((W - 80, H - 150), "Swipe  →", font=font(36, "Bold"), fill=GOLD, anchor="rs")
    return im

def story(s, idx, page, total, date_label):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); chrome(d, page, total, date_label)
    d.text((80, 300), f"{idx:02d}", font=font(120, "ExtraBold"), fill=GOLD, anchor="ls")
    tag = s.get("tag", "AI NEWS").upper(); tw = d.textlength(tag, font=font(26, "Bold")) + 44
    d.rounded_rectangle([80, 340, 80 + tw, 392], radius=26, outline=GOLD, width=2)
    d.text((80 + tw / 2, 366), tag, font=font(26, "Bold"), fill=GOLD, anchor="mm")
    f, ls = fit_block(d, s["headline"], "ExtraBold", W - 160, 4, 66, 46)
    y = 470
    for l in ls: d.text((80, y), l, font=f, fill=IVORY, anchor="ls"); y += int(f.size * 1.18)
    y += 30
    fb, lb = fit_block(d, s["body"], "Medium", W - 160, 6, 38, 30)
    for l in lb: d.text((80, y), l, font=fb, fill=MUTED, anchor="ls"); y += int(fb.size * 1.45)
    if s.get("why"):
        y += 30
        fw, lw = fit_block(d, s["why"], "SemiBold", W - 220, 3, 34, 28)
        box_h = 70 + len(lw) * int(fw.size * 1.4)
        d.rounded_rectangle([80, y, W - 80, y + box_h], radius=20, fill=CARD)
        d.text((110, y + 50), "WHY IT MATTERS", font=font(26, "Bold"), fill=GOLD, anchor="ls")
        yy = y + 50 + int(fw.size * 1.45)
        for l in lw: d.text((110, yy), l, font=fw, fill=IVORY, anchor="ls"); yy += int(fw.size * 1.4)
    d.text((80, H - 150), f"Source: {s.get('source', '')}", font=font(26, "Medium"), fill=MUTED, anchor="ls")
    return im

def closing(page, total, date_label):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im); chrome(d, page, total, date_label)
    d.text((W / 2, 520), "That's AI today.", font=font(76, "ExtraBold"), fill=IVORY, anchor="ms")
    d.text((W / 2, 610), "New explainer Reel every evening.", font=font(40, "Medium"), fill=MUTED, anchor="ms")
    d.rounded_rectangle([W / 2 - 330, 700, W / 2 + 330, 800], radius=50, fill=GOLD)
    d.text((W / 2, 750), "FOLLOW @aiwithsufi", font=font(44, "ExtraBold"), fill=BG if lum(GOLD) > lum(BG) else (255, 255, 255), anchor="mm")
    d.text((W / 2, 900), "Save  ·  Share  ·  Comment your take", font=font(34, "SemiBold"), fill=GOLD, anchor="ms")
    return im

def main(src, out):
    data = json.load(open(src)); os.makedirs(out, exist_ok=True)
    dt = datetime.date.fromisoformat(data["date"])
    set_theme(THEME or WEEKDAY_THEMES[dt.weekday()])
    date_label = dt.strftime("%a · %d %b %Y").upper()
    st = data["stories"][:8]; total = len(st) + 2   # Instagram carousels allow at most 10 slides
    slides = [cover(date_label, len(st), total, [s.get("short", s["headline"]) for s in st])]
    slides += [story(s, i + 1, i + 1, total, date_label) for i, s in enumerate(st)]
    slides.append(closing(total - 1, total, date_label))
    for i, im in enumerate(slides):
        im.save(os.path.join(out, f"{i + 1:02d}.jpg"), quality=92, subsampling=0)
    print(f"wrote {len(slides)} slides to {out} (theme {THEME})")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
