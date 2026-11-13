"""Soundtrack for an explainer project, fully synthesized (no samples, no licences):
a preset music score that follows energy sections, sound effects on the animation's cue list, the narration on
top with the music ducked under it, two-pass loudnorm.

  <project>/sound.json (all keys optional):
    {"preset": "corporate-pluck", "bpm": 112, "key": 0, "bars_per_chord": 1, "progression": ["I","V","vi","IV"],
     "sections": [{"t": 0, "energy": 1}, {"t": 9.5, "energy": 2}, {"t": 41, "energy": 3}, {"t": 58, "energy": 0}],
     "end_hit": true, "music_under_voice_db": -18, "music_alone_db": -7, "sfx_db": -2, "lufs": -14, "reverb": 0.3}
    "music_file": "audio/bed.flac" (+ "music_offset", "music_trim" in s) replaces the synthesized score with an
    external track (e.g. MiniMax-Music3), ducked and levelled the same way.
  inputs:  data/vo.json (tts.py; optional), data/cues.json (render.mjs --cues: duration + sfx list), audio/vo.wav
  outputs: audio/music.wav, audio/sfx.wav, audio/final.wav (48 kHz, target LUFS), data/audio.json (levels report)

  presets: corporate-pluck · tech-glow · ambient-space · lofi-piano · doc-pulse · playful-bounce · curious-marimba ·
           hype-trap · none
  sfx types: pop click swoosh whoosh woosh_low type ding notif success error tick tock thud impact riser rise
             paper scribble shutter boing glitch coin sparkle chime bubble blip blip_up blip_down zoom_in zoom_out
             slide stamp drop heartbeat beep

  ~/.generative-music-video/venv/Scripts/python.exe sound.py <project>
"""
import json
import os, shutil
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
RNG = np.random.default_rng(7)


# ============================================================================ dsp primitives
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(max(1, int(dur * SR))) / SR


def noise(n):
    return RNG.standard_normal(n)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], btype="band", output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR / 2 - 100) / (SR / 2), btype="low", output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f / (SR / 2), btype="high", output="sos"), x)


def adsr(n, a=0.005, d=0.1, s=0.7, r=0.2):
    a_, d_, r_ = int(a * SR), int(d * SR), int(r * SR)
    env = np.ones(n) * s
    env[: min(n, a_)] = np.linspace(0, 1, min(n, a_))
    if a_ < n:
        k = min(n - a_, d_)
        env[a_:a_ + k] = np.linspace(1, s, k)
    if 0 < r_ < n:
        env[-r_:] *= np.linspace(1, 0, r_)
    return env


def sweep_sin(f0, f1, n, geo=True):
    f = np.geomspace(f0, f1, n) if geo else np.linspace(f0, f1, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def place(bus, x, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= len(bus) or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    x = x[: len(bus) - i]
    if x.ndim == 1:
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        bus[i:i + len(x), 0] += x * gain * l * 1.414
        bus[i:i + len(x), 1] += x * gain * r * 1.414
    else:
        bus[i:i + len(x)] += x * gain


def reverb(bus, rt60, wet, pre=0.02, damp=6000, seed=1):
    if wet <= 0:
        return bus
    n = int(rt60 * 1.2 * SR)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    env = np.exp(-6.9 * t / rt60)
    ir = np.stack([lp(rng.standard_normal(n), damp) * env, lp(rng.standard_normal(n), damp) * env], axis=1)
    ir[: int(pre * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True))
    out = np.stack([fftconvolve(bus[:, 0], ir[:, 0])[: len(bus)], fftconvolve(bus[:, 1], ir[:, 1])[: len(bus)]], axis=1)
    return bus * (1 - wet * 0.5) + out * wet


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12)


# ============================================================================ instruments
def kalimba(f, vel=1.0, dur=1.6):
    t = tt(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.85) + 0.32 * np.sin(2 * np.pi * f * 5.95 * t) * np.exp(-t / 0.07)
    x += bp(noise(len(t)), 2000, 5000) * np.exp(-t / 0.003) * 0.15
    return x * adsr(len(t), 0.002, 0.0, 1.0, 0.05) * vel * 0.5


def marimba(f, vel=1.0, dur=1.0):
    t = tt(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.38) + 0.25 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t / 0.1)
    x += bp(noise(len(t)), 800, 3000) * np.exp(-t / 0.004) * 0.12
    return x * adsr(len(t), 0.002, 0, 1, 0.05) * vel * 0.5


def pizz(f, vel=1.0, dur=0.5):
    t = tt(dur)
    x = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t / (0.16 / h)) / h for h in (1, 2, 3, 4))
    return lp(x, 3500) * adsr(len(t), 0.003, 0, 1, 0.04) * vel * 0.45


def bell(f, vel=1.0, dur=2.0, ratio=3.5, index=2.5, tau=1.1):
    t = tt(dur)
    x = np.sin(2 * np.pi * f * t + index * np.exp(-t / 0.5) * np.sin(2 * np.pi * f * ratio * t)) * np.exp(-t / tau)
    return x * adsr(len(t), 0.002, 0, 1, 0.1) * vel * 0.35


def epiano(f, vel=1.0, dur=1.8):
    t = tt(dur)
    mod = (1.2 + 0.8 * vel) * np.exp(-t / 0.35) * np.sin(2 * np.pi * f * t)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 1.1) + 0.15 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / 0.4)
    return x * adsr(len(t), 0.004, 0, 1, 0.25) * vel * 0.32


def saw(f, t, detune=0.0, phase=0.0):
    ph = (f * (2 ** (detune / 1200)) * t + phase) % 1.0
    return 2 * ph - 1


def pad(notes, dur, vel=1.0, cutoff=1600, attack=0.8, release=1.4):
    t = tt(dur)
    L = np.zeros(len(t)); R = np.zeros(len(t))
    for k, m in enumerate(notes):
        f = mtof(m)
        L += saw(f, t, -7, 0.1 * k) + 0.6 * saw(f, t, 4, 0.37 * k)
        R += saw(f, t, 7, 0.23 * k) + 0.6 * saw(f, t, -4, 0.61 * k)
    env = adsr(len(t), attack, 0.0, 1.0, release)
    return np.stack([lp(L, cutoff) * env, lp(R, cutoff) * env], axis=1) * vel * 0.045 / max(1, len(notes) ** 0.5)


def bass(f, dur, vel=1.0):
    t = tt(dur)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return x * adsr(len(t), 0.02, 0.2, 0.8, 0.12) * vel * 0.28


def sub808(f, dur, vel=1.0):
    t = tt(dur)
    x = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f * (1 + 0.5 * np.exp(-t / 0.04))) / SR))
    return lp(x, 900) * adsr(len(t), 0.003, 0.3, 0.7, 0.1) * vel * 0.32


def kick(vel=1.0):
    t = tt(0.45)
    x = sweep_sin(150, 45, len(t)) * np.exp(-t / 0.14) + bp(noise(len(t)), 1500, 6000) * np.exp(-t / 0.004) * 0.3
    return np.tanh(x * 1.6) * vel * 0.6


def snare(vel=1.0):
    t = tt(0.3)
    x = bp(noise(len(t)), 1200, 8000) * np.exp(-t / 0.07) * 0.8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.5
    return x * vel * 0.4


def clap(vel=1.0):
    t = tt(0.25)
    e = sum(np.exp(-np.clip(t - d, 0, None) / 0.012) * (t >= d) for d in (0, 0.011, 0.023))
    return bp(noise(len(t)), 900, 5000) * (e + np.exp(-t / 0.09) * 0.5) * vel * 0.3


def hat(vel=1.0, open_=False):
    t = tt(0.35 if open_ else 0.08)
    return hp(noise(len(t)), 7000) * np.exp(-t / (0.12 if open_ else 0.018)) * vel * 0.22


def shaker(vel=1.0):
    t = tt(0.12)
    return bp(noise(len(t)), 4000, 11000) * np.sin(np.pi * np.clip(t / 0.12, 0, 1)) ** 2 * vel * 0.12


def timp(f, vel=1.0):
    t = tt(1.4)
    return (sweep_sin(f * 1.3, f, len(t)) * np.exp(-t / 0.5) + lp(noise(len(t)), 300) * np.exp(-t / 0.05) * 0.4) * vel * 0.5


# ============================================================================ harmony
MAJOR = {"I": (0, 4, 7, 11), "ii": (2, 5, 9, 12), "iii": (4, 7, 11, 14), "IV": (5, 9, 12, 16), "V": (7, 11, 14, 17),
         "vi": (9, 12, 16, 19), "IVsus": (5, 7, 12, 14), "Vsus": (7, 12, 14, 19)}
MINOR = {"i": (0, 3, 7, 10), "iv": (5, 8, 12, 15), "v": (7, 10, 14, 17), "III": (3, 7, 10, 14), "VI": (8, 12, 15, 19),
         "VII": (10, 14, 17, 21), "ii0": (2, 5, 8, 12)}

PRESETS = {  # tempo, progression, root midi, layers by energy
    "corporate-pluck": dict(bpm=112, prog=["I", "V", "vi", "IV"], root=60, bpc=1, rev=0.25),
    "tech-glow": dict(bpm=100, prog=["vi", "IV", "I", "V"], root=57, bpc=1, rev=0.35),
    "ambient-space": dict(bpm=80, prog=["i", "VI", "III", "VII"], root=50, bpc=2, rev=0.55),
    "lofi-piano": dict(bpm=72, prog=["I", "vi", "IV", "V"], root=60, bpc=1, rev=0.35),
    "doc-pulse": dict(bpm=96, prog=["i", "VI", "iv", "v"], root=57, bpc=1, rev=0.3),
    "playful-bounce": dict(bpm=118, prog=["I", "vi", "ii", "V"], root=62, bpc=1, rev=0.2),
    "curious-marimba": dict(bpm=104, prog=["I", "iii", "IV", "V"], root=62, bpc=1, rev=0.3),
    "hype-trap": dict(bpm=140, prog=["i", "VI", "III", "VII"], root=45, bpc=1, rev=0.25),
}


def chord_notes(sym, root, minor):
    tab = MINOR if minor else MAJOR
    return [root + s for s in (tab.get(sym) or MAJOR.get(sym) or MINOR.get(sym))]


def build_score(cfg, dur):
    name = cfg.get("preset", "corporate-pluck")
    N = int(dur * SR)
    mus = np.zeros((N, 2))
    if name == "none":
        return mus
    P = dict(PRESETS[name])
    bpm = cfg.get("bpm", P["bpm"])
    beat = 60 / bpm
    root = P["root"] + cfg.get("key", 0)
    prog = cfg.get("progression", P["prog"])
    minor = name in ("ambient-space", "doc-pulse", "hype-trap") or prog[0].islower() and prog[0] in MINOR
    bpc = cfg.get("bars_per_chord", P["bpc"])
    secs = sorted(cfg.get("sections", [{"t": 0, "energy": 2}]), key=lambda s: s["t"])

    def energy(t):
        e = secs[0]["energy"]
        for s in secs:
            if t >= s["t"]:
                e = s["energy"]
        return e

    bar = 4 * beat
    nbars = int(math.ceil(dur / bar)) + 1
    for b in range(nbars):
        t0 = b * bar
        if t0 >= dur:
            break
        e = energy(t0 + 0.01)
        sym = prog[(b // bpc) % len(prog)]
        ch = chord_notes(sym, root, minor)
        first_of_chord = b % bpc == 0
        if e <= 0:
            continue
        if name == "corporate-pluck":
            if first_of_chord:
                place(mus, pad([n + 12 for n in ch[:3]], bar * bpc + 0.6, 0.55 + 0.15 * e, 1400 + 400 * e, attack=0.3), t0)
            for k in range(8):
                arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24][k % 4]
                place(mus, kalimba(mtof(arp), 0.42 if k % 2 == 0 else 0.3), t0 + k * beat / 2, pan=0.3 * math.sin(k))
            if e >= 2:
                for k in range(4):
                    place(mus, bass(mtof(ch[0] - 12), beat * 0.9, 0.8), t0 + k * beat)
                for k in (1, 3):
                    place(mus, clap(0.8), t0 + k * beat)
                for k in range(8):
                    place(mus, shaker(0.8 if k % 2 else 0.5), t0 + k * beat / 2, pan=0.4)
            if e >= 3:
                for k in range(4):
                    place(mus, kick(0.9), t0 + k * beat)
                if b % 2 == 0:
                    for k, m in enumerate([ch[2] + 24, ch[1] + 24, ch[0] + 24]):
                        place(mus, bell(mtof(m), 0.25, 1.5), t0 + k * beat, pan=-0.3)
        elif name == "tech-glow":
            if first_of_chord:
                place(mus, pad([n + 12 for n in ch], bar * bpc + 1.0, 0.8, 900 + 500 * e, attack=0.6), t0)
            for k in range(16):
                m = [ch[0], ch[2], ch[1] + 12, ch[3]][k % 4] + 24
                tq = t0 + k * beat / 4
                x = lp(saw(mtof(m), tt(0.18)) * np.exp(-tt(0.18) / 0.06), 1500 + 900 * e) * 0.09
                place(mus, x, tq, pan=0.35 * math.sin(k * 0.7))
            if e >= 2:
                for k in range(4):
                    place(mus, sub808(mtof(ch[0] - 12), beat * 0.8, 0.8), t0 + k * beat)
                for k in range(8):
                    place(mus, hat(0.6 if k % 2 else 0.35), t0 + k * beat / 2, pan=0.3)
            if e >= 3:
                for k in (0, 2):
                    place(mus, kick(0.9), t0 + k * beat)
                place(mus, snare(0.7), t0 + 1 * beat); place(mus, snare(0.7), t0 + 3 * beat)
        elif name == "ambient-space":
            if first_of_chord:
                place(mus, pad([n + 12 for n in ch] + [ch[0] + 24], bar * bpc + 2.0, 0.9 + 0.2 * e, 700 + 450 * e, attack=1.4, release=2.0), t0)
                place(mus, bass(mtof(ch[0] - 12), bar * bpc, 0.5 + 0.15 * e), t0)
            for k in range(0, 8, 3 if e < 2 else 1):
                if RNG.random() < (0.35 if e < 2 else 0.55):
                    m = ch[k % 4] + 24 + (12 if RNG.random() < 0.3 else 0)
                    place(mus, bell(mtof(m), 0.22, 3.0, ratio=2.0, index=1.1, tau=1.6), t0 + k * beat / 2, pan=RNG.uniform(-0.6, 0.6))
            if e >= 2:
                for k in range(8):
                    place(mus, lp(pizz(mtof(ch[0]), 0.5), 900), t0 + k * beat / 2, pan=-0.2)
            if e >= 3 and first_of_chord:
                place(mus, timp(mtof(ch[0] - 24), 0.9), t0)
                place(mus, pad([n + 24 for n in ch[:3]], bar * bpc + 1.5, 0.7, 3200, attack=0.9), t0)
        elif name == "lofi-piano":
            vel = 0.55 + 0.1 * e
            for k, n in enumerate(ch):
                place(mus, epiano(mtof(n), vel * (0.9 if k else 1.0), bar * 1.2), t0 + k * 0.02)
            if e >= 1:
                place(mus, epiano(mtof(ch[2] + 12), vel * 0.6, 1.2), t0 + 2.5 * beat)
            if e >= 2:
                place(mus, bass(mtof(ch[0] - 12), bar * 0.95, 0.55), t0)
            if e >= 3:
                for k in range(8):
                    place(mus, hat(0.25 if k % 2 else 0.4), t0 + k * beat / 2 + (0.03 if k % 2 else 0), pan=0.3)
                place(mus, lp(kick(0.5), 2000), t0); place(mus, lp(snare(0.35), 3000), t0 + 2 * beat)
        elif name == "doc-pulse":
            if first_of_chord:
                place(mus, pad([ch[0], ch[0] + 7], bar * bpc + 0.8, 0.8, 500, attack=1.0), t0)
            for k in (0, 3, 6):
                place(mus, epiano(mtof(ch[k % 3] + 12), 0.4, 1.4), t0 + k * beat / 2)
            if e >= 2:
                for k in range(16):
                    place(mus, hp(noise(int(0.01 * SR)), 5000) * np.exp(-tt(0.01) / 0.003) * (0.25 if k % 4 else 0.45), t0 + k * beat / 4, pan=0.3)
                for k in range(4):
                    place(mus, bass(mtof(ch[0] - 12), beat * 0.5, 0.7), t0 + k * beat)
            if e >= 3:
                place(mus, kick(0.8), t0); place(mus, kick(0.6), t0 + 2.5 * beat); place(mus, snare(0.5), t0 + 2 * beat)
        elif name in ("playful-bounce", "curious-marimba"):
            inst = pizz if name == "playful-bounce" else marimba
            pat = [0, 2, 1, 2, 0, 2, 1, 3] if name == "playful-bounce" else [0, 1, 2, 3, 2, 1, 2, 0]
            for k in range(8):
                place(mus, inst(mtof(ch[pat[k]] + 12), 0.5 if k % 2 == 0 else 0.35), t0 + k * beat / 2, pan=0.25 * math.sin(k * 1.7))
            if e >= 2:
                for k in (0, 2):
                    place(mus, pizz(mtof(ch[0] - 12), 0.8, 0.4), t0 + k * beat)
                place(mus, pizz(mtof(ch[2] - 12), 0.6, 0.3), t0 + 3.5 * beat)
                for k in (1, 3):
                    place(mus, clap(0.55), t0 + k * beat)
            if e >= 3:
                for k in range(4):
                    place(mus, kick(0.7), t0 + k * beat)
                for k, m in enumerate([ch[2], ch[1], ch[3], ch[2]]):
                    place(mus, bell(mtof(m + 24), 0.2, 1.0, ratio=3.0, index=1.0, tau=0.5), t0 + k * beat + beat / 2, pan=-0.3)
        elif name == "hype-trap":
            if first_of_chord:
                place(mus, pad([n + 12 for n in ch[:3]], bar * bpc + 0.4, 0.7, 700 + 500 * e, attack=0.2), t0)
            if e >= 1:
                place(mus, sub808(mtof(ch[0]), bar * 0.48, 0.9), t0)
                place(mus, sub808(mtof(ch[0]), bar * 0.3, 0.8), t0 + 2.75 * beat)
            if e >= 2:
                for k in range(16):
                    roll = (k >= 12 and b % 2 == 1)
                    place(mus, hat(0.55 if k % 2 == 0 else 0.35), t0 + k * beat / 4, pan=0.25)
                    if roll:
                        place(mus, hat(0.3), t0 + k * beat / 4 + beat / 8, pan=0.25)
                place(mus, clap(0.9), t0 + 2 * beat)
            if e >= 3:
                for tq in (0, 0.75, 2.5):
                    place(mus, kick(1.0), t0 + tq * beat)
                place(mus, snare(0.8), t0 + 2 * beat)
    # section-change accents: a riser into rising energy, a hit on the new section
    for a, b2 in zip(secs, secs[1:]):
        if b2["energy"] > a["energy"] and b2["t"] > 1.5:
            place(mus, fx("riser", 1.4) * 0.5, b2["t"] - 1.4)
            if b2["energy"] >= 3:
                place(mus, fx("impact", 1.2) * 0.5, b2["t"])
    if cfg.get("end_hit", True):
        last = secs[-1]["t"] if secs[-1]["energy"] == 0 else dur - 2.5
        ch = chord_notes(prog[0], root, minor)
        place(mus, pad([n + 12 for n in ch] + [ch[0] + 24], dur - last + 0.5, 1.0, 2200, attack=0.05, release=2.0), last)
        place(mus, bell(mtof(ch[0] + 24), 0.5, 3.0, ratio=2.0, index=1.2, tau=1.5), last)
        place(mus, bass(mtof(ch[0] - 12), min(3.0, dur - last), 0.7), last)
    return reverb(mus, 2.0 if name in ("ambient-space", "lofi-piano") else 1.4, cfg.get("reverb", P["rev"]))


# ============================================================================ sound effects
def fx(kind, dur=0.35, pitch=1.0):
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    env_s = np.sin(np.pi * np.clip(t / dur, 0, 1))
    if kind == "pop":
        return sweep_sin(950 * pitch, 320 * pitch, n) * np.exp(-t / 0.03) * 0.5
    if kind == "click":
        return (bp(noise(n), 2500, 7000) * np.exp(-t / 0.004) + np.sin(2 * np.pi * 2200 * pitch * t) * np.exp(-t / 0.006) * 0.5) * 0.5
    if kind in ("swoosh", "whoosh", "woosh_low"):
        bands = {"swoosh": [(900, 3000), (2000, 6000)], "whoosh": [(300, 900), (700, 2200), (1500, 4500)], "woosh_low": [(120, 500), (300, 1100)]}[kind]
        x = np.zeros(n)
        for k, (lo, hi) in enumerate(bands):
            x += bp(noise(n), lo * pitch, hi * pitch) * np.clip(env_s * 1.6 - 0.3 * k, 0, 1)
        return x * 0.4
    if kind == "type":
        x = np.zeros(n); tq = 0.0
        while tq < dur - 0.02:
            i = int(tq * SR); k = int(0.02 * SR)
            x[i:i + k] += (bp(noise(k), 1800, 6500) * np.exp(-np.arange(k) / SR / 0.005))[: n - i]
            tq += 0.055 + 0.05 * RNG.random()
        return x * 0.45
    if kind in ("ding", "notif"):
        a = bell(1568 * pitch, 0.9, max(dur, 0.9), ratio=3.0, index=1.5, tau=0.5)
        if kind == "notif":
            b = bell(2093 * pitch, 0.8, max(dur, 0.9), ratio=3.0, index=1.5, tau=0.5)
            out = np.zeros(len(a) + int(0.09 * SR)); out[: len(a)] += a; out[int(0.09 * SR):] += b
            return out
        return a
    if kind == "success":
        out = np.zeros(int((max(dur, 0.9) + 0.3) * SR))
        for k, m in enumerate((72, 76, 79, 84)):
            b = marimba(mtof(m) * pitch, 0.7, 0.8); i = int(k * 0.07 * SR); out[i:i + len(b)] += b[: len(out) - i]
        return out
    if kind == "error":
        return np.sign(np.sin(2 * np.pi * 140 * t)) * adsr(n, 0.005, 0.05, 0.6, 0.05) * lp(np.ones(n), 2000) * 0.12
    if kind in ("tick", "tock"):
        f = 1450 if kind == "tick" else 900
        return (np.sin(2 * np.pi * f * pitch * t) * np.exp(-t / 0.012) + 0.4 * bp(noise(n), 2000, 6000) * np.exp(-t / 0.002)) * 0.45
    if kind == "thud":
        return (sweep_sin(110, 55, n) * np.exp(-t / 0.07) + 0.3 * lp(noise(n), 500) * np.exp(-t / 0.02)) * 0.6
    if kind == "impact":
        return np.tanh(2 * (sweep_sin(90, 32, n) * np.exp(-t / 0.35) + lp(noise(n), 1200) * np.exp(-t / 0.08) * 0.6)) * 0.55
    if kind in ("riser", "rise"):
        tone = sweep_sin(180 * pitch, 900 * pitch, n) * 0.12
        air = bp(noise(n), 400, 6000) * (t / dur) ** 2
        return (tone + air * 0.3) * (t / dur) ** 1.5
    if kind == "paper":
        x = bp(noise(n), 1500, 7000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 9 * t + RNG.random() * 6)))
        return x * env_s ** 0.6 * 0.3
    if kind == "scribble":
        am = np.abs(np.sin(2 * np.pi * 7 * t + RNG.random() * 6)) ** 0.6
        return bp(noise(n), 2500, 8000) * am * adsr(n, 0.02, 0, 1, 0.06) * 0.25
    if kind == "shutter":
        a = bp(noise(n), 1500, 8000) * np.exp(-t / 0.01)
        b = np.zeros(n); i = int(0.07 * SR)
        if i < n:
            b[i:] = (bp(noise(n - i), 1000, 6000) * np.exp(-np.arange(n - i) / SR / 0.015))
        return (a + b) * 0.45
    if kind == "boing":
        f = 220 * pitch * (1 + 0.6 * np.exp(-t / 0.12) * np.sin(2 * np.pi * 9 * t))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.25) * 0.35
    if kind == "glitch":
        x = np.zeros(n); k = int(0.02 * SR)
        for i in range(0, n, k):
            if RNG.random() < 0.6:
                x[i:i + k] = np.sign(np.sin(2 * np.pi * RNG.uniform(200, 2000) * t[: min(k, n - i)]))
        return lp(x, 6000) * 0.12
    if kind == "coin":
        a = np.sign(np.sin(2 * np.pi * 988 * t)) * (t < 0.08); b = np.sign(np.sin(2 * np.pi * 1319 * t)) * (t >= 0.08)
        return lp((a + b) * np.exp(-np.clip(t - 0.08, 0, None) / 0.15), 4000) * 0.12
    if kind in ("sparkle", "chime"):
        x = np.zeros(n)
        notes = [86, 88, 90, 93, 95, 98] if kind == "sparkle" else [86, 90, 93, 98]
        for k in range(int(14 * dur) if kind == "sparkle" else 4):
            m = notes[k % len(notes)] if kind == "chime" else RNG.choice(notes)
            b = bell(mtof(m) * pitch, 0.5, 0.8, ratio=2.0, index=1.0, tau=0.3)
            i = int((k * 0.12 if kind == "chime" else RNG.random() * dur * 0.8) * SR)
            x[i:i + len(b)] += b[: max(0, n - i)]
        return x * 0.7
    if kind == "bubble":
        return sweep_sin(320 * pitch, 760 * pitch, n) * np.exp(-t / 0.04) * 0.4
    if kind in ("blip", "blip_up", "blip_down", "beep"):
        f0, f1 = {"blip": (660, 660), "beep": (1000, 1000), "blip_up": (420, 980), "blip_down": (820, 360)}[kind]
        sq = np.sign(np.sin(2 * np.pi * np.cumsum(np.geomspace(f0 * pitch, f1 * pitch, n)) / SR))
        return lp(sq, 3500) * adsr(n, 0.003, 0.05, 0.7, 0.04) * 0.15
    if kind in ("zoom_in", "zoom_out"):
        f = (320, 55) if kind == "zoom_in" else (55, 320)
        return (sweep_sin(*f, n) * 0.35 + bp(noise(n), 500, 3500) * 0.22) * env_s
    if kind == "slide":
        return bp(noise(n), 300 * pitch, 1800 * pitch) * env_s ** 0.7 * 0.45
    if kind == "stamp":
        return (fx("thud", dur) + bp(noise(n), 800, 4000) * np.exp(-t / 0.015) * 0.5) * 0.8
    if kind == "drop":
        return sweep_sin(900 * pitch, 200 * pitch, n) * np.exp(-t / 0.08) * 0.4
    if kind == "heartbeat":
        x = np.zeros(n)
        for d in (0, 0.22):
            i = int(d * SR)
            if i < n:
                x[i:] += (sweep_sin(70, 40, n - i) * np.exp(-np.arange(n - i) / SR / 0.06))
        return x * 0.6
    raise ValueError(f"unknown sfx type: {kind}")


# ============================================================================ mix
def load_music(path, n, offset=0.0, trim=0.0):
    """An external music bed (e.g. a MiniMax-Music3 render) instead of the synthesized score: resampled to 48 kHz
    stereo, `trim` seconds cut from its head, placed at `offset` on the timeline, cut to the film's length."""
    x, sr = sf.read(str(path), always_2d=True)
    if sr != SR:
        from scipy.signal import resample_poly
        g = math.gcd(int(sr), SR)
        x = resample_poly(x, SR // g, int(sr) // g, axis=0)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = x[int(trim * SR):, :2]
    out = np.zeros((n, 2))
    i = int(offset * SR)
    k = max(0, min(len(x), n - i))
    out[i:i + k] = x[:k]
    return out


def main(project):
    root = Path(project).resolve()
    cfg = json.loads((root / "sound.json").read_text(encoding="utf-8")) if (root / "sound.json").exists() else {}
    cues = json.loads((root / "data" / "cues.json").read_text(encoding="utf-8"))
    vo = json.loads((root / "data" / "vo.json").read_text(encoding="utf-8")) if (root / "data" / "vo.json").exists() else {"lines": []}
    dur = cues["duration"] + 0.3
    N = int(dur * SR)

    mus = load_music(root / cfg["music_file"], N, cfg.get("music_offset", 0.0), cfg.get("music_trim", 0.0)) \
        if cfg.get("music_file") else build_score(cfg, dur)
    sfx = np.zeros((N, 2))
    for c in cues["sfx"]:
        x = fx(c["type"], c.get("dur", 0.35), c.get("pitch", 1.0))
        place(sfx, x, c["t"], c.get("gain", 0.6), float(np.clip(c.get("pan", RNG.normal(0, 0.15)), -0.8, 0.8)))
    sfx = reverb(sfx, 0.7, 0.12, damp=7000)

    voc = np.zeros((N, 2))
    if (root / "audio" / "vo.wav").exists() and vo["lines"]:
        v, sr = sf.read(root / "audio" / "vo.wav", always_2d=False)
        assert sr == SR
        v = hp(v, 70)[:N]
        voc[: len(v), 0] = v; voc[: len(v), 1] = v
        voc = reverb(voc, 0.4, 0.05, pre=0.01, damp=5000)

    speech = np.zeros(N, bool)
    for l in vo["lines"]:
        speech[int(l["start"] * SR):int(l["end"] * SR)] = True
    if speech.any():
        gate = np.zeros(N)
        gate[speech] = 1.0
        a_att, a_rel = np.exp(-1 / (0.06 * SR)), np.exp(-1 / (0.5 * SR))
        act = np.maximum(lfilter([1 - a_rel], [1, -a_rel], gate), lfilter([1 - a_att], [1, -a_att], gate))
        duck_db = cfg.get("duck_db", 8)
        mus = mus * (1 - (1 - 10 ** (-duck_db / 20)) * np.clip(act, 0, 1))[:, None]
        vo_db = rms_db(voc[speech, 0])
        # measure the music only where it actually plays under speech (a bed under one line must not read as quiet)
        mm = mus.mean(axis=1)
        w50 = int(0.05 * SR)
        env = np.sqrt(np.convolve(mm ** 2, np.ones(w50) / w50, mode="same"))
        playing = speech & (env > env.max() * 0.03) if env.max() > 0 else speech
        ref = mm[playing] if playing.sum() > SR * 0.5 else mm[speech]
        g_mus = 10 ** ((vo_db + cfg.get("music_under_voice_db", -18) - rms_db(ref + 1e-9)) / 20) if np.abs(mus).max() > 0 else 0
        ref_db = vo_db
    else:  # music-led piece: music is the reference
        g_mus, ref_db = 10 ** (cfg.get("music_alone_db", -7) / 20) / max(10 ** (rms_db(mus.mean(axis=1)) / 20), 1e-9) * 0.25, -19
    w = int(0.1 * SR)
    sm = sfx.mean(axis=1)
    nw = len(sm) // w
    loud = np.percentile(np.sqrt((sm[: nw * w].reshape(nw, w) ** 2).mean(axis=1)), 99.5) if nw else 0
    g_sfx = 10 ** ((ref_db + cfg.get("sfx_db", -2) - 20 * np.log10(loud + 1e-12)) / 20) if loud > 0 else 0
    mix = voc + mus * g_mus + sfx * g_sfx
    fl = int(0.8 * SR)
    mix[-fl:] *= (np.linspace(1, 0, fl) ** 1.5)[:, None]
    peak = np.abs(mix).max() + 1e-9
    mix = mix / peak * 0.89
    out = root / "audio"
    out.mkdir(exist_ok=True)
    sf.write(out / "music.wav", (mus * g_mus / peak * 0.89).astype(np.float32), SR, subtype="FLOAT")
    sf.write(out / "sfx.wav", (sfx * g_sfx / peak * 0.89).astype(np.float32), SR, subtype="FLOAT")
    sf.write(out / "mix_raw.wav", mix.astype(np.float32), SR, subtype="FLOAT")

    ff = os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg") or str(Path(__file__).resolve().parent.parent / "node_modules" / "ffmpeg-static" / "ffmpeg")
    target = cfg.get("lufs", -14)
    r = subprocess.run([ff, "-hide_banner", "-i", str(out / "mix_raw.wav"), "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = json.loads(r.stderr[r.stderr.rindex("{"): r.stderr.rindex("}") + 1])
    af = (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([ff, "-y", "-hide_banner", "-v", "error", "-i", str(out / "mix_raw.wav"), "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", str(out / "final.wav")], check=True)
    rep = {"duration": round(dur, 2), "preset": cfg.get("preset", "corporate-pluck"), "sfx_cues": len(cues["sfx"]), "target_lufs": target,
           "music_gain_db": round(20 * np.log10(g_mus + 1e-12), 1), "sfx_gain_db": round(20 * np.log10(g_sfx + 1e-12), 1), "input_lufs": m["input_i"]}
    (root / "data" / "audio.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps(rep))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
