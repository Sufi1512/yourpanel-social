"""Download the engine's fonts from the google/fonts GitHub repository (OFL-1.1 / Apache-2.0) into this folder.

  python get_fonts.py            # all faces except the two 20 MB Chinese ones
  python get_fonts.py --cjk      # also Noto Serif SC + Noto Sans SC (needed for <html lang="zh"> projects)

fonts.css expects these exact file names; files that already exist are skipped.
"""
import os
import sys
import urllib.error
import urllib.request

BASE = "https://github.com/google/fonts/raw/main/"
FONTS = {  # local file name -> path in google/fonts
    "ArchivoBlack-Regular.ttf": "ofl/archivoblack/ArchivoBlack-Regular.ttf",
    "BarlowCondensed-Bold.ttf": "ofl/barlowcondensed/BarlowCondensed-Bold.ttf",
    "BarlowCondensed-Medium.ttf": "ofl/barlowcondensed/BarlowCondensed-Medium.ttf",
    "BarlowCondensed-SemiBold.ttf": "ofl/barlowcondensed/BarlowCondensed-SemiBold.ttf",
    "BebasNeue-Regular.ttf": "ofl/bebasneue/BebasNeue-Regular.ttf",
    "Caveat_wght_.ttf": "ofl/caveat/Caveat[wght].ttf",
    "DMSerifDisplay-Regular.ttf": "ofl/dmserifdisplay/DMSerifDisplay-Regular.ttf",
    "Fredoka_wdth-wght_.ttf": "ofl/fredoka/Fredoka[wdth,wght].ttf",
    "Inter_opsz-wght_.ttf": "ofl/inter/Inter[opsz,wght].ttf",
    "LibreBaskerville-Italic_wght_.ttf": "ofl/librebaskerville/LibreBaskerville-Italic[wght].ttf",
    "LibreBaskerville_wght_.ttf": "ofl/librebaskerville/LibreBaskerville[wght].ttf",
    "Lora_wght_.ttf": "ofl/lora/Lora[wght].ttf",
    "Montserrat_wght_.ttf": "ofl/montserrat/Montserrat[wght].ttf",
    "Nunito_wght_.ttf": "ofl/nunito/Nunito[wght].ttf",
    "Oswald_wght_.ttf": "ofl/oswald/Oswald[wght].ttf",
    "PatrickHand-Regular.ttf": "ofl/patrickhand/PatrickHand-Regular.ttf",
    "PermanentMarker-Regular.ttf": "apache/permanentmarker/PermanentMarker-Regular.ttf",
    "PlayfairDisplay_wght_.ttf": "ofl/playfairdisplay/PlayfairDisplay[wght].ttf",
    "Poppins-Bold.ttf": "ofl/poppins/Poppins-Bold.ttf",
    "Poppins-ExtraBold.ttf": "ofl/poppins/Poppins-ExtraBold.ttf",
    "Poppins-Medium.ttf": "ofl/poppins/Poppins-Medium.ttf",
    "Poppins-Regular.ttf": "ofl/poppins/Poppins-Regular.ttf",
    "Poppins-SemiBold.ttf": "ofl/poppins/Poppins-SemiBold.ttf",
    "RobotoMono_wght_.ttf": "apache/robotomono/RobotoMono[wght].ttf",
    "SpaceGrotesk_wght_.ttf": "ofl/spacegrotesk/SpaceGrotesk[wght].ttf",
}
CJK = {
    "NotoSansSC_wght_.ttf": "ofl/notosanssc/NotoSansSC[wght].ttf",
    "NotoSerifSC_wght_.ttf": "ofl/notoserifsc/NotoSerifSC[wght].ttf",
}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    want = dict(FONTS, **(CJK if "--cjk" in sys.argv else {}))
    for name, path in want.items():
        dst = os.path.join(here, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 10_000:
            continue
        data, url = None, ""
        other = path.replace("ofl/", "apache/", 1) if path.startswith("ofl/") else path.replace("apache/", "ofl/", 1)
        for p in (path, other):  # google/fonts moves a family between licence folders now and then
            url = BASE + p.replace("[", "%5B").replace("]", "%5D").replace(",", "%2C")
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    data = r.read()
                break
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
        if data is None:
            raise SystemExit(f"{name}: not found at {BASE}{path} (or {other})")
        if data[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):  # a font, not an HTML error page
            raise SystemExit(f"{name}: {url} did not return a font")
        open(dst, "wb").write(data)
        print(f"{name:36s} {len(data) // 1024:6d} KB")
    print("fonts ready in", here)


if __name__ == "__main__":
    main()
