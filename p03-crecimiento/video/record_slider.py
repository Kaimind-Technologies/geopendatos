"""Graba el video de P03 dentro de GeoLibre: el Time Slider (años reales 1985-2015, WSF)
muestra cómo crecieron las ciudades del eje central, año a año (stop-motion).

Igual que el de P02: sirve el repo con lectura por rangos, abre geolibre/p03_video.geolibre.json
(generado con --base local), oculta la barra de años y avanza con ⏭, un año por paso.
Guarda un cuadro por paso y un cronograma (año de cada cuadro) para edit_slider.py.

Uso:
    python -P record_slider.py
"""

import json
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

VIDEO = Path(__file__).resolve().parent
REPO = VIDEO.parents[1]
sys.path.insert(0, str(REPO / "common"))
from serve_range import serve  # noqa: E402

PORT = 8766
W, H = 1080, 1350
FRAMES = VIDEO / "frames_slider"
CHROME_FLAGS = ["--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests"]
PROJECT_URL = f"http://localhost:{PORT}/p03-crecimiento/geolibre/p03_video.geolibre.json"
YEARS = list(range(1985, 2016))


def hold_frames(y: int) -> int:
    if y == 1985:
        return 75     # intro
    if y < 2015:
        return 10     # un año cada 1/3 de segundo
    return 210        # 2015: hallazgos y cierre


BTN = "[...document.querySelectorAll('button')].find(b => b.innerText.trim() === '⏭')"
HIDE_DOCK = f"""() => {{
  let el = {BTN};
  while (el.parentElement && el.parentElement.getBoundingClientRect().width < window.innerWidth * 0.6) el = el.parentElement;
  const dock = el.parentElement || el;
  dock.style.display = 'none';
  return true;
}}"""


def main() -> None:
    server = serve(str(REPO), PORT)
    shutil.rmtree(FRAMES, ignore_errors=True)
    FRAMES.mkdir(parents=True)
    schedule = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=False, args=CHROME_FLAGS)
            page = browser.new_page(viewport={"width": W, "height": H})
            page.goto(f"https://web.geolibre.app/?welcome=0&theme=dark&panels=collapsed&url={quote(PROJECT_URL, safe='')}",
                      wait_until="load")
            page.wait_for_function(f"!!({BTN})", timeout=120000)
            time.sleep(30)
            page.add_style_tag(content="::-webkit-scrollbar{display:none!important} *{scrollbar-width:none!important}")
            page.evaluate(HIDE_DOCK)
            time.sleep(4)
            diag = page.evaluate("(document.body.innerText.match(/Diagnostics:\\s*(\\d+)/) || [])[1]")
            print("diagnósticos de GeoLibre antes de grabar:", diag)
            n = 0
            for y in YEARS:
                if y > 1985:
                    page.evaluate(f"() => {BTN}.click()")
                time.sleep(0.9 if y < 2015 else 2.5)
                shot = FRAMES / f"year_{y}.jpg"
                page.screenshot(path=str(shot), type="jpeg", quality=93)
                for _ in range(hold_frames(y)):
                    shutil.copyfile(shot, FRAMES / f"{n:06d}.jpg")
                    schedule.append(y)
                    n += 1
            browser.close()
    finally:
        server.shutdown()
    (FRAMES / "schedule.json").write_text(json.dumps(schedule), encoding="utf-8")
    print(f"{len(schedule)} cuadros ({len(schedule) / 30:.1f} s) -> {FRAMES}")


if __name__ == "__main__":
    main()
