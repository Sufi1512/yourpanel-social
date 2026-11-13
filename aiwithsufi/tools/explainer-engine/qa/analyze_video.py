"""Frame-level mechanics analysis for one explainer video.

usage: python -I analyze_video.py <media_dir | video.mp4> <out_dir>

Writes into <out_dir>:
  metrics.json    shot/cut stats, motion energy, holds, palette, flatness (animation vs live action), loudness, WPM
  opening.jpg     first 16 s at 2 fps (the hook)
  timeline.jpg    48 frames evenly over the whole video (rhythm / visual system)
  shots_N.jpg     one mid-frame per shot (up to 72 shots, evenly thinned)
  strips.jpg      8 fps filmstrips around 3 cuts + 2 high-motion moments (transition & easing mechanics)
  animated.jpg    only the flat-shaded (animated) seconds, for mixed live-action videos
  ending.jpg      last 12 s at 1 fps (CTA / outro)
  transcript.txt  de-duplicated captions with [mm:ss] stamps
"""
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

def find_ffmpeg():
    """FFMPEG_PATH, else the engine's own ffmpeg-static (npm install), else ffmpeg on PATH."""
    if os.environ.get("FFMPEG_PATH"):
        return os.environ["FFMPEG_PATH"]
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("ffmpeg.exe", "ffmpeg"):
        p = os.path.join(here, "node_modules", "ffmpeg-static", name)
        if os.path.exists(p):
            return p
    return shutil.which("ffmpeg") or "ffmpeg"


FF = find_ffmpeg()
CUT_THR = 0.33
FONT = ImageFont.truetype("arial.ttf", 13)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)


def probe(path):
    err = run([FF, "-hide_banner", "-i", path]).stderr.decode("utf-8", "ignore")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    v = re.search(r"Video: .*?, (\d{2,5})x(\d{2,5}).*?([\d.]+) fps", err)
    return dur, int(v[1]), int(v[2]), float(v[3])


def stream(path, vf, w, h, ch, extra_dir=None):
    """Yield frames from ffmpeg as uint8 arrays (h, w, ch)."""
    cmd = [FF, "-v", "error", "-i", path, "-an", "-vf", vf, "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=extra_dir, bufsize=10**7)
    n = w * h * ch
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, ch) if ch > 1 else np.frombuffer(buf, np.uint8).reshape(h, w)
    p.wait()


def motion_and_cuts(path, out):
    """One decode: per-frame scene scores (native fps) + 6 fps grey frames for motion energy."""
    vf = "select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file=scores.txt,fps=6,scale=160:90:flags=area,format=rgb24"
    diffs, hists, prev = [], [], None
    for f in stream(path, vf, 160, 90, 3, extra_dir=out):
        g = (f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114).astype(np.int16)
        diffs.append(0.0 if prev is None else float(np.abs(g - prev).mean()))
        prev = g
        q = (f >> 6).astype(np.int32)  # 4 levels per channel -> 64-bin colour histogram
        hists.append(np.bincount((q[..., 0] * 16 + q[..., 1] * 4 + q[..., 2]).ravel(), minlength=64) / q[..., 0].size)
    motion_and_cuts.hists = np.array(hists)
    cuts, last = [], -9.0
    t = None
    for line in open(os.path.join(out, "scores.txt"), encoding="utf-8", errors="ignore"):
        if line.startswith("frame:"):
            t = float(re.search(r"pts_time:([\d.]+)", line)[1])
        elif "scene_score" in line and t is not None:
            s = float(line.split("=")[1])
            if s > CUT_THR and t - last > 0.25 and t > 0.1:
                cuts.append(round(t, 3))
                last = t
    os.remove(os.path.join(out, "scores.txt"))
    return np.array(diffs), cuts


def scene_changes(hists, cuts, fps=6, thr=0.28, gap=1.5):
    """Scene changes including gradual ones (morphs, wipes, camera moves into a new set): peaks of the colour-histogram
    distance between frames 1 s apart, at least `gap` s apart. Hard cuts are counted here too."""
    if len(hists) <= fps:
        return []
    d = 0.5 * np.abs(hists[fps:] - hists[:-fps]).sum(axis=1)  # 0..1, frame i vs i+1 s
    ev, last = [], -9.0
    for i in range(1, len(d) - 1):
        t = (i + fps / 2) / fps
        if d[i] >= thr and d[i] >= d[i - 1] and d[i] >= d[i + 1] and t - last >= gap:
            ev.append(round(t, 2))
            last = t
    return ev


def look_stats(path, dur):
    """1 fps at 480x270: flatness (vector-animation detector), colourfulness, palette sample."""
    W, H = 480, 270
    flat, colorf, sat, val, pix = [], [], [], [], []
    rng = np.random.default_rng(0)
    for f in stream(path, f"fps=1,scale={W}:{H}:flags=area,format=rgb24", W, H, 3):
        a = f.astype(np.int16)
        dx = np.abs(np.diff(a, axis=1)).max(axis=2)[:-1, :]
        dy = np.abs(np.diff(a, axis=0)).max(axis=2)[:, :-1]
        flat.append(float(((dx <= 1) & (dy <= 1)).mean()))
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        rg, yb = r - g, 0.5 * (r + g) - b
        colorf.append(float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)))
        mx, mn = a.max(axis=2), a.min(axis=2)
        sat.append(float(((mx - mn) / np.maximum(mx, 1)).mean()))
        val.append(float(mx.mean() / 255))
        idx = rng.integers(0, W * H, 300)
        pix.append(f.reshape(-1, 3)[idx])
    return np.array(flat), np.array(colorf), np.array(sat), np.array(val), np.concatenate(pix)


def palette(px, k=8, iters=14):
    px = px.astype(np.float32)
    rng = np.random.default_rng(1)
    c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(iters):
        lab = ((px[:, None, :] - c[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            m = lab == j
            if m.any():
                c[j] = px[m].mean(0)
    share = np.bincount(lab, minlength=k) / len(px)
    order = np.argsort(-share)
    return [{"hex": "#%02x%02x%02x" % tuple(int(v) for v in c[j]), "share": round(float(share[j]), 3)} for j in order]


def loudness(path):
    err = run([FF, "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128,silencedetect=n=-45dB:d=0.6", "-f", "null", "-"]).stderr.decode("utf-8", "ignore")
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    sil = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", err))
    return (float(m[-1]) if m else None), sil


def grab(path, t, w=320):
    r = run([FF, "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", path, "-frames:v", "1", "-vf", f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"])
    from io import BytesIO
    try:
        return Image.open(BytesIO(r.stdout)).convert("RGB")
    except Exception:
        return None


def burst(path, t0, dur, fps, w):
    """Consecutive frames from one ffmpeg call (accurate seek)."""
    r = run([FF, "-v", "error", "-ss", f"{max(t0, 0):.3f}", "-i", path, "-t", f"{dur:.3f}", "-vf", f"fps={fps},scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"])
    from io import BytesIO
    data, ims, i = r.stdout, [], 0
    sig = b"\x89PNG\r\n\x1a\n"
    parts = data.split(sig)[1:]
    for p in parts:
        try:
            ims.append(Image.open(BytesIO(sig + p)).convert("RGB"))
        except Exception:
            pass
    return ims


def sheet(tiles, labels, cols, out, title):
    tiles = [t for t in tiles if t is not None]
    if not tiles:
        return
    tw, th = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    lab_h = 16
    img = Image.new("RGB", (cols * tw, 22 + rows * (th + lab_h)), (24, 24, 24))
    d = ImageDraw.Draw(img)
    d.text((6, 4), title, fill=(255, 220, 120), font=FONT)
    for i, (t, l) in enumerate(zip(tiles, labels)):
        x, y = (i % cols) * tw, 22 + (i // cols) * (th + lab_h)
        img.paste(t.resize((tw, th)), (x, y + lab_h))
        d.text((x + 3, y + 1), l, fill=(200, 200, 200), font=FONT)
    img.save(out, quality=88)


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def transcript(media_dir, out):
    vtts = sorted([f for f in os.listdir(media_dir) if f.endswith((".vtt", ".srt"))], key=lambda f: ("orig" in f, len(f)))
    if not vtts:
        return None, 0
    raw = open(os.path.join(media_dir, vtts[0]), encoding="utf-8", errors="ignore").read()
    lines, seen = [], set()
    for block in raw.split("\n\n"):
        m = re.search(r"(\d+):(\d+):([\d.,]+) -->", block.replace(",", "."))
        if not m:
            continue
        t = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
        for txt in block.split("\n")[1:]:
            txt = re.sub(r"<[^>]+>", "", txt).strip()
            if not txt or "-->" in txt or txt in seen:
                continue
            seen.add(txt)
            lines.append((t, txt))
    with open(out, "w", encoding="utf-8") as f:
        for t, txt in lines:
            f.write(f"[{mmss(t)}] {txt}\n")
    words = sum(len(t.split()) for _, t in lines)
    return vtts[0], words


def main(media_dir, out):
    media_dir, out = os.path.abspath(media_dir), os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    if os.path.isfile(media_dir):  # a rendered sample: analyze that file, captions beside it
        path, media_dir = media_dir, os.path.dirname(media_dir)
    else:
        mp4 = [f for f in os.listdir(media_dir) if f.endswith(".mp4")][0]
        path = os.path.join(media_dir, mp4)
    info_f = [f for f in os.listdir(media_dir) if f.endswith(".info.json")]
    info = json.load(open(os.path.join(media_dir, info_f[0]), encoding="utf-8")) if info_f else {}
    dur, w, h, fps = probe(path)

    diffs, cuts = motion_and_cuts(path, out)
    scs = scene_changes(motion_and_cuts.hists, cuts)
    flat, colorf, sat, val, px = look_stats(path, dur)
    lufs, silence = loudness(path)
    vtt, words = transcript(media_dir, os.path.join(out, "transcript.txt"))

    bounds = [0.0] + cuts + [dur]
    shots = np.diff(bounds)
    anim = flat > 0.42  # flat-fill frames: vector/2D animation or flat motion graphics
    m = {
        "id": info.get("id", os.path.basename(media_dir)), "title": info.get("title"), "channel": info.get("channel"),
        "upload_date": info.get("upload_date"), "views": info.get("view_count"),
        "duration_s": round(dur, 2), "src_res": f"{w}x{h}", "fps": fps,
        "cuts": len(cuts), "cuts_per_min": round(len(cuts) / dur * 60, 2),
        "shot_len_mean": round(float(shots.mean()), 2), "shot_len_median": round(float(np.median(shots)), 2),
        "shot_len_p10_p90": [round(float(np.percentile(shots, 10)), 2), round(float(np.percentile(shots, 90)), 2)],
        "first_cut_s": cuts[0] if cuts else None,
        "scene_changes_per_min": round(len(scs) / dur * 60, 2),
        "scene_len_median": round(float(np.median(np.diff([0.0] + scs + [dur]))), 2),
        "cuts_first_15s": sum(1 for c in cuts if c < 15),
        "motion_mean": round(float(diffs.mean()), 2), "motion_p90": round(float(np.percentile(diffs, 90)), 2),
        "hold_frac": round(float((diffs < 0.4).mean()), 3),
        "flat_mean": round(float(flat.mean()), 3), "animated_frac": round(float(anim.mean()), 3),
        "colourfulness": round(float(colorf.mean()), 1), "saturation": round(float(sat.mean()), 3),
        "brightness": round(float(val.mean()), 3), "dark_frame_frac": round(float((val < 0.3).mean()), 3),
        "palette": palette(px), "loudness_lufs": lufs, "silence_s": round(silence, 1),
        "caption_file": vtt, "caption_words": words, "wpm_overall": round(words / dur * 60, 1) if words else None,
        "chapters": [c.get("title") for c in (info.get("chapters") or [])],
    }
    # motion energy per 10 % of runtime (pacing curve)
    seg = np.array_split(diffs, 10)
    m["motion_curve_deciles"] = [round(float(s.mean()), 2) if len(s) else 0 for s in seg]
    json.dump(m, open(os.path.join(out, "metrics.json"), "w"), indent=1)

    # --- sheets -------------------------------------------------------------
    op = burst(path, 0, min(16, dur), 2, 384)
    sheet(op, [mmss(i / 2) for i in range(len(op))], 4, os.path.join(out, "opening.jpg"), f"OPENING 0-16s @2fps  {m['title']}")

    ts = np.linspace(0, dur - 0.5, 48)
    sheet([grab(path, t, 256) for t in ts], [mmss(t) for t in ts], 6, os.path.join(out, "timeline.jpg"), f"TIMELINE 48 evenly spaced  dur {mmss(dur)}  cuts/min {m['cuts_per_min']}")

    mids = [(bounds[i] + bounds[i + 1]) / 2 for i in range(len(bounds) - 1)]
    if len(mids) > 72:
        mids = [mids[int(i)] for i in np.linspace(0, len(mids) - 1, 72)]
    for k in range(0, len(mids), 36):
        chunk = mids[k:k + 36]
        sheet([grab(path, t, 256) for t in chunk], [mmss(t) for t in chunk], 6, os.path.join(out, f"shots_{k // 36 + 1}.jpg"), f"SHOT MID-FRAMES {k + 1}-{k + len(chunk)} of {len(mids)} sampled shots ({len(bounds) - 1} total)")

    rows, labels = [], []
    pick_cuts = [cuts[int(i)] for i in np.linspace(0, len(cuts) - 1, 3)] if len(cuts) >= 3 else cuts
    order = np.argsort(-diffs)
    peaks = []
    for i in order:
        t = i / 6
        if all(abs(t - c) > 1.0 for c in cuts) and all(abs(t - p) > 20 for p in peaks):
            peaks.append(t)
        if len(peaks) == 2:
            break
    for kind, t in [("cut", c) for c in pick_cuts] + [("motion", p) for p in peaks]:
        fr = burst(path, t - 0.5, 1.0, 8, 192)[:8]
        rows += fr + [None] * (8 - len(fr))
        labels += [f"{kind} {mmss(t - 0.5 + j / 8)}" for j in range(8)]
    keep = [(r, l) for r, l in zip(rows, labels) if r is not None]
    if keep:
        sheet([r for r, _ in keep], [l for _, l in keep], 8, os.path.join(out, "strips.jpg"), "FILMSTRIPS @8fps: each row = 1 s around a cut or a motion peak")

    if 0.04 < m["animated_frac"] < 0.9:
        secs = np.where(anim)[0]
        pick = secs[np.linspace(0, len(secs) - 1, min(36, len(secs))).astype(int)]
        sheet([grab(path, float(s) + 0.5, 256) for s in pick], [mmss(float(s)) for s in pick], 6, os.path.join(out, "animated.jpg"), f"ANIMATED/FLAT-SHADED SECONDS ONLY ({m['animated_frac'] * 100:.0f}% of runtime)")

    en = burst(path, max(0, dur - 12), 12, 1, 320)
    sheet(en, [mmss(max(0, dur - 12) + i) for i in range(len(en))], 4, os.path.join(out, "ending.jpg"), "ENDING last 12 s @1fps")
    print(json.dumps({k: m[k] for k in ("id", "duration_s", "cuts_per_min", "shot_len_median", "animated_frac", "wpm_overall")}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
