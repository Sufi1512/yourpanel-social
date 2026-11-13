"""Voiceover with Kokoro-82M (local, Apache-2.0): speaks <project>/script.json line by line, trims each line,
places it on the timeline with the script's gaps, and writes
  audio/vo.wav      48 kHz mono float
  data/vo.json      {duration, wpm, lines:[{id, text, start, end, words:[{w, start, end}]}]}
  out/captions.srt  captions from the script text and Kokoro's word times

script.json:
  {"voice": "am_michael", "speed": 1.0, "lead": 0.8, "tail": 1.6,
   "lines": [{"id": "hook", "text": "…", "gap": 0.35, "voice": "bf_emma", "speed": 0.95, "at": 12.0}]}
  gap = silence before the line (default 0.35 s); at = absolute start time (overrides gap) for music-led cuts.
  Voices: a*/b* prefix = American/British (af_heart, af_bella, af_nicole, am_michael, am_adam, am_fenrir, am_puck,
  am_echo, bf_emma, bf_isabella, bm_george, bm_lewis, bm_daniel …). Speed 1.0 ≈ 186 wpm while speaking.

  ~/.generative-music-video/venv/Scripts/python.exe tts.py <project>
"""
import json
import os
import sys
from pathlib import Path

if (Path.home() / ".generative-music-video").exists():  # reuse that venv's model cache when it is there
    os.environ.setdefault("HF_HOME", str(Path.home() / ".generative-music-video" / "cache" / "hf"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
import warnings  # noqa: E402

warnings.filterwarnings("ignore")
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy.signal import resample_poly  # noqa: E402

SR_TTS, SR = 24000, 48000


def is_word(s):
    return any(ch.isalnum() for ch in s)


def speak(pipe, text, voice, speed):
    audio, toks, off = [], [], 0.0
    for r in pipe(text, voice=voice, speed=speed):
        a = r.audio.cpu().numpy() if hasattr(r.audio, "cpu") else np.asarray(r.audio)
        for tk in r.tokens or []:
            toks.append({"t": tk.text, "s": None if tk.start_ts is None else tk.start_ts + off,
                         "e": None if tk.end_ts is None else tk.end_ts + off})
        audio.append(a.astype(np.float32))
        off += len(a) / SR_TTS
    a = np.concatenate(audio)
    if not toks:  # Mandarin/Japanese pipelines return no timestamps: estimate them
        return a, estimate_words(a, text)
    words = []
    for tk in toks:  # punctuation joins the previous word
        if is_word(tk["t"]) or not words:
            words.append({"w": tk["t"], "start": tk["s"], "end": tk["e"]})
        else:
            words[-1]["w"] += tk["t"]
    for i, w in enumerate(words):  # fill missing times
        if w["start"] is None:
            w["start"] = words[i - 1]["end"] if i else 0.0
        if w["end"] is None:
            nxt = words[i + 1]["start"] if i + 1 < len(words) else None
            w["end"] = nxt if nxt is not None else w["start"] + 0.25
    return a, words


def estimate_words(a, text):
    """Word times when the pipeline gives none: find the voiced span by RMS, then spread units (each CJK character,
    each Latin or Devanagari word) across it in proportion to their length, with punctuation counted as a short pause."""
    import re
    hop = int(0.01 * SR_TTS)
    rms = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, mode="same"))
    voiced = np.where(rms > max(rms.max() * 0.05, 1e-4))[0]
    t0, t1 = (voiced[0] / SR_TTS, voiced[-1] / SR_TTS) if len(voiced) else (0.0, len(a) / SR_TTS)
    units = re.findall(r"[㐀-鿿぀-ヿ]|[ऀ-ॿ]+|[A-Za-z0-9%$'.\-]+|[，。、！？；：,.!?;:…—।]", text)
    weight = [2.5 if re.fullmatch(r"[，。、！？；：,.!?;:…—।]", u) else (1.0 if len(u) == 1 else 0.6 + 0.25 * len(u)) for u in units]
    total = sum(weight) or 1.0
    words, t = [], t0
    for u, w in zip(units, weight):
        d = (t1 - t0) * w / total
        if re.fullmatch(r"[，。、！？；：,.!?;:…—।]", u):
            if words:
                words[-1]["w"] += u
        else:
            words.append({"w": u, "start": t, "end": t + d})
        t += d
    if words:  # trailing punctuation is pause, not speech: the last syllable runs to the end of the voiced span
        words[-1]["end"] = t1
    return words or [{"w": text, "start": t0, "end": t1}]


def srt_time(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"


def main(project):
    for s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252; the log prints en dashes
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    root = Path(project).resolve()
    spec = json.loads((root / "script.json").read_text(encoding="utf-8"))
    import torch
    from kokoro import KPipeline

    pipes = {}

    def pipe_for(voice):
        lang = voice[0] if voice[0] in "abefhijpz" else "a"
        if lang not in pipes:
            pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M", device="cuda" if torch.cuda.is_available() else "cpu")
        return pipes[lang]

    clips, lines = [], []
    t = spec.get("lead", 0.8)
    for i, ln in enumerate(spec["lines"]):
        if "at" in ln:
            t = max(t, float(ln["at"]))
        elif i:
            t += ln.get("gap", spec.get("gap", 0.35))
        voice = ln.get("voice", spec["voice"])
        a, words = speak(pipe_for(voice), ln["text"], voice, ln.get("speed", spec.get("speed", 1.0)))
        s0 = max(0.0, words[0]["start"] - 0.06)
        s1 = min(len(a) / SR_TTS, words[-1]["end"] + 0.15)
        seg = a[int(s0 * SR_TTS):int(s1 * SR_TTS)].copy()
        fade = int(0.01 * SR_TTS)
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        ws = [{"w": w["w"], "start": round(t + w["start"] - s0, 3), "end": round(t + w["end"] - s0, 3)} for w in words]
        clips.append((t, seg))
        lines.append({"id": ln.get("id", f"l{i}"), "i": i, "text": ln["text"], "start": ws[0]["start"], "end": ws[-1]["end"], "words": ws})
        t += len(seg) / SR_TTS
        print(f"{lines[-1]['id']:>10s} {ws[0]['start']:6.2f}–{ws[-1]['end']:6.2f}  {ln['text'][:90]}")
    dur = t + spec.get("tail", 1.6)
    out = np.zeros(int(dur * SR_TTS) + SR_TTS, dtype=np.float32)
    for t_, seg in clips:
        k = int(round(t_ * SR_TTS))
        out[k:k + len(seg)] += seg
    out = resample_poly(out[: int(dur * SR_TTS)], 2, 1).astype(np.float32)
    out *= 0.89 / max(float(np.abs(out).max()), 1e-6)
    for d in ("audio", "data", "out"):
        (root / d).mkdir(exist_ok=True)
    sf.write(root / "audio" / "vo.wav", out, SR, subtype="FLOAT")
    nw = sum(len(l["words"]) for l in lines)
    speech = sum(l["end"] - l["start"] for l in lines)
    vo = {"duration": round(dur, 3), "voice": spec["voice"], "words": nw, "wpm_overall": round(nw / dur * 60, 1),
          "wpm_speech": round(nw / max(speech, 1e-6) * 60, 1), "lines": lines}
    (root / "data" / "vo.json").write_text(json.dumps(vo, indent=1, ensure_ascii=False), encoding="utf-8")
    with open(root / "out" / "captions.srt", "w", encoding="utf-8") as f:
        k = 1
        for l in lines:  # split long lines into ≤ 9-word (≤ 16-character for CJK) captions on word times
            ws = l["words"]
            cjk = any("㐀" <= ch <= "鿿" for ch in l["text"])
            n, sep = (16, "") if cjk else (9, " ")
            for j in range(0, len(ws), n):
                chunk = ws[j:j + n]
                f.write(f"{k}\n{srt_time(chunk[0]['start'])} --> {srt_time(chunk[-1]['end'])}\n{sep.join(w['w'] for w in chunk)}\n\n")
                k += 1
    print(f"\nduration {dur:.2f} s · {nw} words · {vo['wpm_overall']} wpm overall · {vo['wpm_speech']} wpm while speaking")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
