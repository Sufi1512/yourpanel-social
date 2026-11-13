# @aiwithsufi Content Studio

One pipeline that turns a **topic** or a **reference Reel** into an Instagram-ready package:
`reel.mp4` (1080x1920) + `cover.jpg` + `caption.txt` + `qc.json`.

It runs without any paid service. With no keys it uses the offline Kokoro voices, Montserrat motion graphics and FFmpeg.
Each API key you add switches on one extra stage. If a provider is missing or fails, the pipeline falls back and keeps going.

## Stages

| # | Stage | How |
|---|-------|-----|
| 1 | Research | Claude + web search; only confirmed sources (same rules as the AI News task) |
| 2 | Reference analysis | `studio.py analyze REF.mp4 OUT/ [--transcribe]` gives the shot list, cuts per 10 s, hook timing, motion, loudness, transcript (faster-whisper) and `contact_sheet.jpg` |
| 3 | Concept + script + storyboard | Claude writes `scripts/<date>-<slug>.json` (reel_engine format: one scene = one storyboard beat) |
| 4 | **Plan approval** | Sufi approves concept, script and style before anything is rendered |
| 5 | Graphics & animation | `tools/reel_engine.py` scene types: hook, flow, cycle, hub, list, compare, bars, code, quiz, media, outro |
| 6 | AI B-roll | `media` scenes with `"gen": {"kind": "image"\|"video", "prompt": ...}` use Flux (images) or Veo (video) |
| 7 | Voiceover + music bed | Kokoro (free, offline), or ElevenLabs per speaker via `"eleven_voice_id"` |
| 8 | Edit & export | reel_engine renders scenes in parallel; FFmpeg joins the scenes, mixes the audio and normalises loudness to -15 LUFS |
| 9 | Cover, caption, hashtags | `studio.py cover` (title kept inside the 1080x1350 grid-safe zone) + caption from `"caption"` / `"hashtags"` |
| 10 | Quality check | `studio.py qc` checks codec, 9:16 size, fps, AAC audio, duration, loudness, silent gaps and black frames |
| 11 | **Final approval** | Sufi approves the Reel, cover and caption |
| 12 | Post | Windsor Instagram connector, using commit-pinned raw.githubusercontent.com URLs |

## Commands

```bash
python3 aiwithsufi/studio/studio.py status                      # which providers/tools are available
python3 aiwithsufi/studio/studio.py analyze ref.mp4 work/ref/   # reference breakdown (structure only, never copy)
python3 aiwithsufi/studio/studio.py build aiwithsufi/scripts/X.json aiwithsufi/reels/X/ --preview   # one frame per scene
python3 aiwithsufi/studio/studio.py build aiwithsufi/scripts/X.json aiwithsufi/reels/X/             # full package
```

First-run setup in a fresh cloud session: `pip install --break-system-packages pillow soundfile kokoro-onnx`
(plus `faster-whisper` for transcripts, `google-genai` for Veo). The voice model downloads itself on first use.

## API keys (optional)

Set these as **environment variables in the cloud environment settings**. Never put them in this repo, because it is public.

| Variable | Turns on |
|----------|----------|
| `ELEVENLABS_API_KEY` | ElevenLabs voices (add `"eleven_voice_id"` to a speaker; `ELEVENLABS_MODEL` optional) |
| `BFL_API_KEY` | Flux images for `gen` scenes (`BFL_MODEL`, default `flux-pro-1.1`) |
| `GEMINI_API_KEY` | Veo video clips for `gen` scenes (`VEO_MODEL`, default `veo-3.0-fast-generate-001`) |

Kling, Runway and HeyGen are not wired yet. Each one is a single function in `providers.py` that can be added once a key exists.

## Rules

- Reference Reels give structure and pacing only. Never reuse their footage, script, music, branding or characters.
- AI-generated people must not depict real public figures.
- Nothing is rendered before plan approval, and nothing is posted before final approval.
- Commit only inside `aiwithsufi/`.
