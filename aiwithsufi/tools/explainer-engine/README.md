# explainer-engine (vendored)

GSAP/SVG frame-exact video renderer from the `explainer-engine` skill (Safiullah-Rahu/claude-video-skills, MIT, see LICENSE).
Local changes for @aiwithsufi:
- `audio/tts_onnx.py`: Kokoro-ONNX voices (am_fenrir / af_heart) for Riya/Arjun discussion scripts (`scenes[].lines[]` with who/vo/cap); word times estimated.
- `audio/sound.py`: uses system ffmpeg (FFMPEG_PATH or PATH) instead of a Windows ffmpeg.exe.
- `fonts/fonts.css`: Montserrat + IBM Plex Mono from `aiwithsufi/tools/` (copy `Montserrat.ttf`, `PlexMono.ttf` into `fonts/`).

Build a reel (see `aiwithsufi/reels_src/2026-11-13-always-on-agents/` for the Glow Sketch example):
```
cd aiwithsufi/tools/explainer-engine && npm install && cp ../Montserrat.ttf ../PlexMono.ttf fonts/
python3 audio/tts_onnx.py <project>
EXPLAINER_BROWSER_PATH=<chromium> node render.mjs <project> --cues && python3 audio/sound.py <project>
EXPLAINER_BROWSER_PATH=<chromium> node render.mjs <project> --workers 2 --out out/render.mp4
```
Then re-encode for Instagram (H.264 yuv420p, tv range, bt709, AAC, +faststart) as in the reel-export skill.
