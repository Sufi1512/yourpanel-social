#!/usr/bin/env bash
# Full build of an explainer project: voice -> sound cues -> soundtrack -> frames -> MP4 -> QA metrics.
#   ./make.sh <project> [--draft] [--skip-tts] [--fps 30] [--workers 4]
#   --draft renders 960x540 at 15 fps into out/draft.mp4 (fast check); otherwise out/<project-name>.mp4
set -e
ENGINE="$(cd "$(dirname "$0")" && pwd)"
P="$(cd "$1" && pwd)"; shift
# Python with kokoro + soundfile + scipy: $EXPLAINER_PY, else this PC's venv, else python3/python on PATH
PY="${EXPLAINER_PY:-$HOME/.generative-music-video/venv/Scripts/python.exe}"
[ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
DRAFT=0; SKIP_TTS=0; FPS=30; WORKERS=4
while [ $# -gt 0 ]; do case "$1" in
  --draft) DRAFT=1;; --skip-tts) SKIP_TTS=1;; --fps) FPS="$2"; shift;; --workers) WORKERS="$2"; shift;; esac; shift; done
if [ -f "$P/script.json" ] && [ $SKIP_TTS = 0 ]; then echo "== voice"; "$PY" "$ENGINE/audio/tts.py" "$P"; fi
echo "== cues"; node "$ENGINE/render.mjs" "$P" --cues
echo "== sound"; "$PY" "$ENGINE/audio/sound.py" "$P"
NAME="$(basename "$P")"
if [ $DRAFT = 1 ]; then
  echo "== draft render"; node "$ENGINE/render.mjs" "$P" --scale 0.5 --fps 15 --workers "$WORKERS" --out out/draft.mp4
else
  echo "== render"; node "$ENGINE/render.mjs" "$P" --fps "$FPS" --workers "$WORKERS" --out "out/$NAME.mp4"
  echo "== QA"; python -I "$ENGINE/qa/analyze_video.py" "$P/out/$NAME.mp4" "$P/out/qa" || true
fi
