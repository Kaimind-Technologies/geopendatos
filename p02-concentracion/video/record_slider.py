"""Graba el video de P02 dentro de GeoLibre: el Time Slider acumulativo enciende
Venezuela de lo más denso a lo más vacío, paso a paso (stop-motion).

- Sirve el repo en local con lectura por rangos (common/serve_range.py) y abre el
  proyecto geolibre/p02_concentracion.geolibre.json (generado con --base local).
- Oculta la barra de años del Time Slider (los "años" codifican el %) y avanza el
  slider con su propio botón ⏭, un paso por porcentaje.
- Guarda un cuadro por paso y un cronograma (video/frames_slider/schedule.json) que
  usa edit_slider.py para los textos y el contador.

Necesita Chrome con ventana (sin ventana no hay GPU y GeoLibre no dibuja las capas).

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
P02 = VIDEO.parent
REPO = P02.parent
sys.path.insert(0, str(REPO / "common"))
from serve_range import serve  # noqa: E402

PORT = 8766
W, H = 1080, 1350
FRAMES = VIDEO / "frames_slider"
CHROME_FLAGS = ["--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests"]
PROJECT_URL = f"http://localhost:{PORT}/p02-concentracion/geolibre/p02_concentracion.geolibre.json"

# Cuántos cuadros (30 fps) dura cada paso k del slider.
def hold_frames(k: int) -> int:
    if k == 1:
        return 60      # intro: país casi apagado
    if k < 50:
        return 4
    if k == 50:
        return 105     # la mitad: pausa larga
    if k < 100:
        return 3
    return 150         # 100%: país completo + cierre

HIDE_DOCK = """() => {
  const btn = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === '⏭');
  if (!btn) return 'sin botón';
  let el = btn;
  while (el.parentElement && el.parentElement.getBoundingClientRect().width < window.innerWidth * 0.6) el = el.parentElement;
  const dock = el.parentElement || el;
  dock.setAttribute('data-kaimind-hidden', '1');
  dock.style.display = 'none';
  return dock.getBoundingClientRect().height;
}"""
NEXT = """() => { const b = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === '⏭'); b.click(); return true; }"""


def main() -> None:
    server = serve(str(REPO), PORT)
    shutil.rmtree(FRAMES, ignore_errors=True)
    FRAMES.mkdir(parents=True)
    schedule = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=False, args=CHROME_FLAGS)
            page = browser.new_page(viewport={"width": W, "height": H})
            url = f"https://web.geolibre.app/?welcome=0&theme=dark&panels=collapsed&url={quote(PROJECT_URL, safe='')}"
            page.goto(url, wait_until="load")
            try:
                page.wait_for_function(
                    "[...document.querySelectorAll('button')].some(b => b.innerText.trim() === '⏭')", timeout=120000)
            except Exception:
                page.screenshot(path=str(VIDEO / "_fallo_carga.png"))
                raise
            time.sleep(30)  # carga y extrusión de los 88.987 hexágonos
            page.add_style_tag(content="::-webkit-scrollbar{display:none!important} *{scrollbar-width:none!important}")
            print("barra del slider oculta:", page.evaluate(HIDE_DOCK))
            time.sleep(4)
            n = 0
            for k in range(1, 101):
                if k > 1:
                    page.evaluate(NEXT)
                time.sleep(0.9 if k < 100 else 2.5)  # deja que GeoLibre filtre y redibuje
                shot = FRAMES / f"step_{k:03d}.jpg"
                page.screenshot(path=str(shot), type="jpeg", quality=93)
                for _ in range(hold_frames(k)):
                    shutil.copyfile(shot, FRAMES / f"{n:06d}.jpg")
                    schedule.append(k)
                    n += 1
                if k % 10 == 0:
                    print(f"  paso {k}/100 · {n} cuadros ({n / 30:.1f} s)", flush=True)
            browser.close()
    finally:
        server.shutdown()
    (FRAMES / "schedule.json").write_text(json.dumps(schedule), encoding="utf-8")
    print(f"{len(schedule)} cuadros -> {FRAMES} ({len(schedule) / 30:.1f} s)")


if __name__ == "__main__":
    main()
