"""Optional AI media providers for the @aiwithsufi studio.

Every provider is switched on by an environment variable and is skipped (never fatal) when the key is missing
or the call fails, so the pipeline always finishes with the free/offline tools.

  BFL_API_KEY         Black Forest Labs Flux images         (BFL_MODEL, default flux-pro-1.1)
  GEMINI_API_KEY      Google Veo video via the Gemini API   (VEO_MODEL, default veo-3.0-fast-generate-001)
  ELEVENLABS_API_KEY  ElevenLabs voices (used inside tools/reel_engine.py; set "eleven_voice_id" per speaker)

Kling, Runway and HeyGen are not wired yet: add a function here with the same signature once a key exists.
Never commit keys: this repo is public. Put them in the cloud environment's settings instead.
"""
import json, os, time, urllib.request


class Skip(Exception):
    """Provider not configured or failed; caller should fall back."""


def status():
    return {
        "flux_image (Black Forest Labs)": bool(os.environ.get("BFL_API_KEY")),
        "veo_video (Google Gemini API)": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
        "elevenlabs_voice": bool(os.environ.get("ELEVENLABS_API_KEY")),
        "kokoro_voice (offline, free)": True,
        "kling / runway / heygen": False,
    }


def _json(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json", "Accept": "application/json", **(headers or {})})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def flux_image(prompt, out, width=1088, height=1920, timeout=180):
    """Text -> image with Flux. Width/height must be multiples of 32 (1088x1920 ~ 9:16)."""
    key = os.environ.get("BFL_API_KEY")
    if not key: raise Skip("BFL_API_KEY not set")
    model = os.environ.get("BFL_MODEL", "flux-pro-1.1")
    try:
        job = _json(f"https://api.bfl.ai/v1/{model}", {"prompt": prompt, "width": width, "height": height}, {"x-key": key})
        poll = job.get("polling_url") or f"https://api.bfl.ai/v1/get_result?id={job['id']}"
        t0 = time.time()
        while time.time() - t0 < timeout:
            time.sleep(2); r = _json(poll, headers={"x-key": key})
            if r.get("status") == "Ready":
                urllib.request.urlretrieve(r["result"]["sample"], out); return out
            if r.get("status") in ("Error", "Failed", "Content Moderated", "Request Moderated"):
                raise Skip(f"Flux returned {r.get('status')}")
        raise Skip("Flux timed out")
    except Skip: raise
    except Exception as e: raise Skip(f"Flux error: {e}")


def veo_video(prompt, out, aspect="9:16", timeout=600):
    """Text -> short video clip with Veo through the google-genai SDK (pip install google-genai)."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key: raise Skip("GEMINI_API_KEY not set")
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise Skip("google-genai not installed (pip install --break-system-packages google-genai)")
    try:
        client = genai.Client(api_key=key)
        op = client.models.generate_videos(model=os.environ.get("VEO_MODEL", "veo-3.0-fast-generate-001"), prompt=prompt,
                                           config=types.GenerateVideosConfig(aspect_ratio=aspect))
        t0 = time.time()
        while not op.done:
            if time.time() - t0 > timeout: raise Skip("Veo timed out")
            time.sleep(10); op = client.operations.get(op)
        vid = op.response.generated_videos[0]
        client.files.download(file=vid.video); vid.video.save(out); return out
    except Skip: raise
    except Exception as e: raise Skip(f"Veo error: {e}")
