"""Shared day-wise palettes for @aiwithsufi. Every post on a given day (news carousel, Reel, explainer carousel)
uses that weekday's palette. Keys: BG, CARD, CARD2, LINE, TEXT (main text), MUTED, ACCENT."""
import datetime, os, re

PALETTES = {
    "sand_espresso":     dict(BG=(238, 226, 206), CARD=(228, 214, 190), CARD2=(246, 238, 224), LINE=(200, 184, 158), TEXT=(40, 28, 22),   MUTED=(108, 90, 74),  ACCENT=(168, 72, 38)),
    "ivory_maroon":      dict(BG=(246, 242, 233), CARD=(236, 230, 218), CARD2=(251, 249, 244), LINE=(205, 198, 184), TEXT=(28, 28, 30),   MUTED=(96, 90, 82),   ACCENT=(128, 32, 40)),
    "newsroom_red":      dict(BG=(250, 250, 248), CARD=(238, 238, 236), CARD2=(255, 255, 255), LINE=(210, 210, 206), TEXT=(17, 17, 17),   MUTED=(85, 85, 85),   ACCENT=(200, 30, 30)),
    "forest_cream":      dict(BG=(22, 44, 36),    CARD=(31, 58, 48),    CARD2=(36, 66, 55),    LINE=(60, 90, 78),    TEXT=(244, 238, 222), MUTED=(190, 196, 180), ACCENT=(222, 184, 110)),
    "plum_blush":        dict(BG=(44, 24, 46),    CARD=(60, 36, 62),    CARD2=(68, 42, 70),    LINE=(92, 64, 94),    TEXT=(248, 238, 242), MUTED=(206, 188, 202), ACCENT=(240, 164, 184)),
    "terracotta_sand":   dict(BG=(176, 88, 58),   CARD=(156, 74, 48),   CARD2=(166, 80, 52),   LINE=(206, 128, 98),  TEXT=(255, 244, 228), MUTED=(250, 222, 200), ACCENT=(255, 214, 160)),
    "graphite_tangerine":dict(BG=(40, 40, 40),    CARD=(54, 54, 54),    CARD2=(60, 60, 62),    LINE=(84, 84, 84),    TEXT=(246, 244, 240), MUTED=(176, 172, 166), ACCENT=(244, 128, 52)),
}
WEEKDAY = ["sand_espresso", "ivory_maroon", "newsroom_red", "forest_cream", "plum_blush", "terracotta_sand", "graphite_tangerine"]  # Mon..Sun

def for_date(d):
    if isinstance(d, str): d = datetime.date.fromisoformat(d)
    return WEEKDAY[d.weekday()]

def date_from_path(path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path or ""))
    return m.group(1) if m else None
