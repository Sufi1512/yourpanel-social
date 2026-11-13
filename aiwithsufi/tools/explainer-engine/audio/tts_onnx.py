"""Kokoro-ONNX voiceover for a discussion script (scenes[].lines[] with who/vo/cap) -> audio/vo.wav + data/vo.json.
Word times are estimated across each clip's voiced span (kokoro-onnx returns no timestamps)."""
import json, os, re, sys, urllib.request
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from tts import estimate_words  # noqa: E402  (pure function, no torch import at module level)

CACHE = Path.home() / ".cache" / "aiwithsufi"; CACHE.mkdir(parents=True, exist_ok=True)
URLS = {"kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"}
SR = 48000

def fetch(name):
    p = CACHE / name
    if not p.exists():
        urllib.request.urlretrieve(URLS[name], p)
    return str(p)

def main(project):
    root = Path(project).resolve()
    spec = json.loads((root / "script.json").read_text(encoding="utf-8"))
    from kokoro_onnx import Kokoro
    k = Kokoro(fetch("kokoro-v1.0.onnx"), fetch("voices-v1.0.bin"))
    spk = spec["speakers"]
    t = spec.get("lead", 0.5); clips = []; lines = []; first = True
    for sc in spec["scenes"]:
        for ln in sc["lines"]:
            if not first:
                t += ln.get("gap", spec.get("gap", 0.3))
            first = False
            a, sr = k.create(ln["vo"], voice=spk[ln["who"]]["voice"], speed=ln.get("speed", spec.get("speed", 1.0)), lang="en-us")
            a = np.asarray(a, dtype=np.float32)
            words = estimate_words(a if sr == 24000 else resample_poly(a, 24000, sr), ln["vo"])
            s0 = max(0.0, words[0]["start"] - 0.06); s1 = min(len(a) / sr, words[-1]["end"] + 0.15)
            seg = a[int(s0 * sr):int(s1 * sr)].copy(); f = int(0.01 * sr)
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
            seg = resample_poly(seg, SR, sr).astype(np.float32)
            ws = [{"w": w["w"], "start": round(t + w["start"] - s0, 3), "end": round(t + w["end"] - s0, 3)} for w in words]
            clips.append((t, seg))
            lines.append({"id": ln["id"], "scene": sc["id"], "who": ln["who"], "text": ln["vo"], "cap": ln.get("cap", ln["vo"]),
                          "start": ws[0]["start"], "end": ws[-1]["end"], "words": ws})
            t += len(seg) / SR
            print(f"{ln['id']:>4} {ws[0]['start']:6.2f}-{ws[-1]['end']:6.2f} {ln['vo'][:70]}")
    dur = t + spec.get("tail", 1.4)
    out = np.zeros(int(dur * SR) + SR, dtype=np.float32)
    for t_, seg in clips:
        i = int(round(t_ * SR)); out[i:i + len(seg)] += seg
    out = out[:int(dur * SR)]; out *= 0.89 / max(float(np.abs(out).max()), 1e-6)
    for d in ("audio", "data", "out"): (root / d).mkdir(exist_ok=True)
    sf.write(root / "audio" / "vo.wav", out, SR, subtype="FLOAT")
    nw = sum(len(l["words"]) for l in lines)
    vo = {"duration": round(dur, 3), "voice": "discussion", "words": nw, "wpm_overall": round(nw / dur * 60, 1), "lines": lines}
    (root / "data" / "vo.json").write_text(json.dumps(vo, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"duration {dur:.1f}s, {nw} words, {vo['wpm_overall']} wpm")

if __name__ == "__main__":
    main(sys.argv[1])
