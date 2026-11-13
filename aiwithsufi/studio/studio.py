"""@aiwithsufi Content Studio: one pipeline from topic or reference Reel to an Instagram-ready package.

  python3 aiwithsufi/studio/studio.py status
  python3 aiwithsufi/studio/studio.py analyze REF.mp4 OUT_DIR [--transcribe]   reference Reel breakdown
  python3 aiwithsufi/studio/studio.py media   SCRIPT.json                       generate AI B-roll for "gen" scenes
  python3 aiwithsufi/studio/studio.py build   SCRIPT.json OUT_DIR [--preview]   media + Reel + cover + caption + QC
  python3 aiwithsufi/studio/studio.py cover   SCRIPT.json OUT.jpg
  python3 aiwithsufi/studio/studio.py qc      VIDEO.mp4

SCRIPT.json is the tools/reel_engine.py format plus optional keys:
  "cover":    {"kicker": "AI NEWS TODAY", "title": "...", "sub": "..."}
  "caption":  full caption text (else one is built from title + scene labels + "hashtags")
  "hashtags": ["#ai", ...]
  scenes of type "media" may carry "gen": {"kind": "image" | "video", "prompt": "..."} instead of a "media" path;
  `media`/`build` fill in the file under assets/ next to the script (skipped if no provider key -> card placeholder).
See aiwithsufi/studio/README.md for the full workflow.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS); sys.path.insert(0, HERE)
import providers  # noqa: E402

DEFAULT_TAGS = ["#ai", "#artificialintelligence", "#aiexplained", "#technews", "#genai", "#aiwithsufi"]


def sh(cmd, **kw): return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ffprobe(path):
    r = sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    if r.returncode: raise SystemExit(f"ffprobe failed on {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


# ---------------------------------------------------------------- status
def cmd_status(_):
    print("Providers (env keys):")
    for k, v in providers.status().items(): print(f"  [{'x' if v else ' '}] {k}")
    for tool in ("ffmpeg", "ffprobe", "node"):
        print(f"  [{'x' if sh(['which', tool]).returncode == 0 else ' '}] {tool}")
    for mod in ("cv2", "kokoro_onnx", "soundfile", "faster_whisper"):
        try: __import__(mod); ok = True
        except ImportError: ok = False
        print(f"  [{'x' if ok else ' '}] python: {mod}")


# ---------------------------------------------------------------- analyze
def cmd_analyze(a):
    import cv2
    from PIL import Image, ImageDraw
    ref, out = a[0], a[1]; os.makedirs(out, exist_ok=True); transcribe = "--transcribe" in a
    meta = ffprobe(ref); v = next(s for s in meta["streams"] if s["codec_type"] == "video")
    dur = float(meta["format"]["duration"]); num, den = map(int, v.get("avg_frame_rate", "30/1").split("/")); fps = num / (den or 1)

    # shot detection: HSV histogram distance between sampled frames (~6 per second)
    cap = cv2.VideoCapture(ref); step = max(1, int(round(fps / 6))); prev = None; cuts = [0.0]; diffs = []; i = 0; thumbs = {}
    motion = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i % step == 0:
            small = cv2.resize(fr, (160, 284)); hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            h = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256]); cv2.normalize(h, h)
            t = i / fps
            if prev is not None:
                d = cv2.compareHist(prev[0], h, cv2.HISTCMP_BHATTACHARYYA); diffs.append(d)
                mv = float(cv2.absdiff(prev[1], cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)).mean()); motion.append(mv)
                med = sorted(motion)[len(motion) // 2] if motion else 0
                # a cut = colour histogram jump, or a sudden pixel-change spike (catches fades on flat backgrounds)
                if (d > 0.45 or (mv > 6 and mv > 4 * max(med, 0.5))) and t - cuts[-1] > 0.6: cuts.append(round(t, 2))
            prev = (h, cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
            thumbs[round(t, 2)] = fr
        i += 1
    cap.release()
    shots = []
    for k, s in enumerate(cuts):
        e = cuts[k + 1] if k + 1 < len(cuts) else dur
        mid = min(thumbs, key=lambda x: abs(x - (s + e) / 2)) if thumbs else None
        shots.append({"n": k + 1, "start": s, "end": round(e, 2), "len": round(e - s, 2), "thumb_t": mid})

    # contact sheet (up to 24 shots) so Claude can look at the reference shot by shot
    sheet = os.path.join(out, "contact_sheet.jpg"); tw, th = 180, 320; cols = 6; pick = shots[:24]
    rows = (len(pick) + cols - 1) // cols or 1; im = Image.new("RGB", (tw * cols, (th + 28) * rows), (18, 18, 18)); d = ImageDraw.Draw(im)
    for k, s in enumerate(pick):
        fr = thumbs.get(s["thumb_t"])
        if fr is None: continue
        t = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((tw, th))
        x, y = (k % cols) * tw, (k // cols) * (th + 28); im.paste(t, (x, y)); d.text((x + 6, y + th + 6), f"#{s['n']} {s['start']:.1f}s ({s['len']:.1f}s)", fill=(230, 230, 230))
    im.save(sheet, quality=88)

    # audio: loudness + silences
    loud = None; r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", ref, "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr); loud = float(m[-1]) if m else None
    has_audio = any(s["codec_type"] == "audio" for s in meta["streams"])

    transcript = None
    if transcribe and has_audio:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
            segs, _ = model.transcribe(ref, vad_filter=True)
            transcript = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
        except ImportError:
            print("faster-whisper not installed: pip install --break-system-packages faster-whisper")

    lens = [s["len"] for s in shots]
    report = {
        "file": os.path.basename(ref), "duration": round(dur, 2), "size": f"{v['width']}x{v['height']}", "fps": round(fps, 2),
        "shots": len(shots), "avg_shot_len": round(sum(lens) / len(lens), 2) if lens else None,
        "cuts_per_10s": round(len(shots) / dur * 10, 2) if dur else None,
        "hook_first_cut_s": shots[1]["start"] if len(shots) > 1 else None,
        "avg_motion": round(sum(motion) / len(motion), 2) if motion else None,
        "audio": has_audio, "loudness_lufs": loud,
        "shot_list": shots, "transcript": transcript, "contact_sheet": os.path.basename(sheet),
        "note": "Use for structure and pacing only. Never copy the reference's footage, script, music, branding or characters.",
    }
    json.dump(report, open(os.path.join(out, "analysis.json"), "w"), indent=1)
    print(f"{len(shots)} shots, avg {report['avg_shot_len']}s, {report['cuts_per_10s']} cuts/10s, loudness {loud} LUFS")
    print("wrote", os.path.join(out, "analysis.json"), "and", sheet)


# ---------------------------------------------------------------- media
def cmd_media(a):
    src = a[0]; spec = json.load(open(src)); base = os.path.dirname(os.path.abspath(src))
    assets = os.path.join(base, "assets"); changed = False
    for i, sc in enumerate(spec["scenes"]):
        g = sc.get("gen")
        if sc.get("type") != "media" or not g: continue
        if sc.get("media") and os.path.exists(os.path.join(base, sc["media"])): continue
        os.makedirs(assets, exist_ok=True)
        stem = os.path.join(assets, f"{os.path.splitext(os.path.basename(src))[0]}_s{i:02d}")
        try:
            if g.get("kind") == "video":
                path = providers.veo_video(g["prompt"], stem + ".mp4")
            else:
                path = providers.flux_image(g["prompt"], stem + ".jpg")
            sc["media"] = os.path.relpath(path, base); changed = True; print(f"scene {i}: generated {sc['media']}")
        except providers.Skip as e:
            print(f"scene {i}: skipped ({e}); the Reel will show a placeholder card unless you add \"media\" by hand")
    if changed: json.dump(spec, open(src, "w"), indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- cover
def cmd_cover(a):
    from PIL import Image, ImageDraw, ImageFont
    from palettes import PALETTES, for_date, date_from_path
    src, out = a[0], a[1]; spec = json.load(open(src))
    day = spec.get("date") or date_from_path(src); p = PALETTES[spec.get("theme") or (for_date(day) if day else "sand_espresso")]
    cv = spec.get("cover") or {}; kicker = cv.get("kicker", "@aiwithsufi"); title = cv.get("title") or spec.get("title", ""); sub = cv.get("sub", "")
    W, H = 1080, 1920; im = Image.new("RGB", (W, H), p["BG"]); d = ImageDraw.Draw(im)
    def f(size, w="ExtraBold"):
        ft = ImageFont.truetype(os.path.join(TOOLS, "Montserrat.ttf"), size); ft.set_variation_by_name(w); return ft
    # everything important stays inside the centred 1080x1350 area (profile grid crop)
    top = (H - 1350) // 2
    av = os.path.join(TOOLS, "avatar.png")
    if os.path.exists(av):
        a_ = Image.open(av).convert("RGB"); s = min(a_.size); a_ = a_.crop(((a_.width - s) // 2, (a_.height - s) // 2, (a_.width + s) // 2, (a_.height + s) // 2)).resize((300, 300))
        m = Image.new("L", (300, 300), 0); ImageDraw.Draw(m).ellipse([0, 0, 299, 299], fill=255); im.paste(a_, (W // 2 - 150, top + 70), m)
        d.ellipse([W // 2 - 162, top + 58, W // 2 + 162, top + 382], outline=p["ACCENT"], width=6)
    kf = f(40, "Bold"); kw = d.textlength(kicker, font=kf) + 70
    d.rounded_rectangle([W // 2 - kw / 2, top + 440, W // 2 + kw / 2, top + 510], radius=35, outline=p["ACCENT"], width=3)
    d.text((W // 2, top + 475), kicker, font=kf, fill=p["ACCENT"], anchor="mm")
    # wrap title to <= 4 lines at the largest size that fits
    words = title.upper().split()
    for size in range(130, 50, -4):
        ft = f(size); lines = [""]
        for w in words:
            t = (lines[-1] + " " + w).strip()
            if d.textlength(t, font=ft) <= 940: lines[-1] = t
            else: lines.append(w)
        if len(lines) <= 4 and all(d.textlength(l, font=ft) <= 940 for l in lines): break
    y = top + 600
    for k, l in enumerate(lines):
        d.text((W // 2, y), l, font=ft, fill=p["ACCENT"] if k == len(lines) - 1 and len(lines) > 1 else p["TEXT"], anchor="mt"); y += int(size * 1.08)
    if sub: d.text((W // 2, y + 40), sub, font=f(40, "Medium"), fill=p["MUTED"], anchor="mt")
    im.save(out, quality=92); print("cover", out)


# ---------------------------------------------------------------- caption
def build_caption(spec):
    if spec.get("caption"): return spec["caption"]
    lines = [f"{spec.get('title', '')} 🎬", ""]
    labs = [re.sub(r"^\d+\s*·\s*", "", s["label"]).capitalize() for s in spec["scenes"] if s.get("label")]
    lines += [f"{i + 1}. {l}" for i, l in enumerate(labs)]
    if spec.get("next"): lines += ["", f"Next up: {spec['next']} 📌"]
    lines += ["", "Save this & follow @aiwithsufi for daily AI updates 📌", "", " ".join(spec.get("hashtags") or DEFAULT_TAGS)]
    return "\n".join(lines)


# ---------------------------------------------------------------- qc
def cmd_qc(a, quiet=False):
    path = a[0]; meta = ffprobe(path); checks = []
    v = next((s for s in meta["streams"] if s["codec_type"] == "video"), None); au = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)
    dur = float(meta["format"]["duration"]); size_mb = int(meta["format"]["size"]) / 1e6
    def add(name, ok, detail, level="fail"): checks.append({"check": name, "result": "pass" if ok else level, "detail": detail})
    add("video stream h264", v and v["codec_name"] == "h264", v and v["codec_name"])
    add("1080x1920 (9:16)", v and (v["width"], v["height"]) == (1080, 1920), v and f"{v['width']}x{v['height']}")
    n_, d_ = (v.get("avg_frame_rate", "0/1") if v else "0/1").split("/"); fr = int(n_) / (int(d_) or 1)
    add("frame rate 23-60", 23 <= fr <= 60, round(fr, 2))
    add("pixel format yuv420p", v and v.get("pix_fmt") == "yuv420p", v and v.get("pix_fmt"))
    add("audio stream aac", au and au["codec_name"] == "aac", au and au["codec_name"])
    add("duration 3s-3min", 3 <= dur <= 180, f"{dur:.1f}s")
    add("duration <= 90s (best reach)", dur <= 90, f"{dur:.1f}s", "warn")
    add("file size < 300 MB", size_mb < 300, f"{size_mb:.1f} MB")
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128,silencedetect=n=-45dB:d=1.5", "-vf", "blackdetect=d=0.5:pix_th=0.06", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr); lufs = float(m[-1]) if m else None
    add("loudness -18..-12 LUFS", lufs is not None and -18 <= lufs <= -12, lufs, "warn")
    sil = re.findall(r"silence_duration: ([\d.]+)", r.stderr); add("no silent gaps > 1.5s", not sil, f"{len(sil)} gaps", "warn")
    blk = re.findall(r"black_start:([\d.]+)", r.stderr); add("no black frames > 0.5s", not blk, f"{len(blk)} spans at {blk[:5]}", "warn")
    ok = all(c["result"] != "fail" for c in checks)
    if not quiet:
        for c in checks: print(f"  {c['result'].upper():4}  {c['check']}: {c['detail']}")
        print("QC", "PASSED" if ok else "FAILED")
    return {"passed": ok, "checks": checks}


# ---------------------------------------------------------------- build
def cmd_build(a):
    src, out = a[0], a[1]; preview = "--preview" in a; os.makedirs(out, exist_ok=True)
    cmd_media([src]); spec = json.load(open(src))
    reel = os.path.join(out, "reel.mp4")
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "reel_engine.py"), src, reel] + (["--preview"] if preview else []))
    if r.returncode: raise SystemExit("reel_engine failed")
    if preview: print("preview written; look at it, fix the script, then build without --preview"); return
    cmd_cover([src, os.path.join(out, "cover.jpg")])
    open(os.path.join(out, "caption.txt"), "w").write(build_caption(spec))
    qc = cmd_qc([reel]); json.dump(qc, open(os.path.join(out, "qc.json"), "w"), indent=1)
    print(f"package ready in {out}: reel.mp4, cover.jpg, caption.txt, qc.json")
    if not qc["passed"]: raise SystemExit(1)


CMDS = {"status": cmd_status, "analyze": cmd_analyze, "media": cmd_media, "build": cmd_build, "cover": cmd_cover, "qc": cmd_qc}
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS: print(__doc__); sys.exit(1)
    CMDS[sys.argv[1]](sys.argv[2:])
