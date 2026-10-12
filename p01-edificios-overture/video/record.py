"""Graba el video de P01 dentro de GeoLibre, cuadro a cuadro (stop-motion).

La cámara se maneja como lo haría una persona (mouse: arrastre y rueda). En cada
cuadro se mueve un poco, se espera a que GeoLibre dibuje y se toma una captura;
así el video sale fluido a 30 fps aunque cada paso tarde. El zoom se controla en
lazo cerrado leyendo la barra de estado de GeoLibre.

Necesita Chrome con ventana (sin ventana no hay GPU y GeoLibre no dibuja las capas).
Los estilos se sirven desde este equipo mientras no estén en el repo.

Uso:
    python -P record.py            # graba video/raw.mp4
"""

import math
import re
import shutil
import subprocess
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import Page, sync_playwright

P01 = Path(__file__).resolve().parents[1]
VIDEO = P01 / "video"
RAW = "https://raw.githubusercontent.com/Kaimind-Technologies/venezuela-datos-abiertos/main/p01-edificios-overture"
PORT = 8765
LOCAL = f"http://localhost:{PORT}"
W, H = 1080, 1350
FPS = 30
CARACAS = (-66.9036, 10.4806)
CHROME_FLAGS = ["--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests"]
# Medido en GeoLibre: cada evento de rueda sube ~0.0019 niveles de zoom por unidad de deltaY.
ZOOM_PER_DELTA = 0.0019


class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def log_message(self, *args) -> None:
        pass


def app_url() -> str:
    q = lambda u: quote(u, safe="")
    return (
        "https://web.geolibre.app/?welcome=0&theme=dark&panels=collapsed"
        f"&data={q(RAW + '/output/ven_h3_r7.parquet')}&data={q(RAW + '/output/caracas_edificios.parquet')}"
        f"&style={q(LOCAL + '/styles/h3.style.json')}&style={q(LOCAL + '/styles/caracas.style.json')}"
    )


# ---------- barra de estado de GeoLibre ----------
NUM = r"(-?\d+(?:\.\d+)?)"


def status(page: Page) -> dict:
    text = page.evaluate("document.body.innerText")
    out = {}
    if m := re.search(rf"Coords:\s*{NUM},\s*{NUM}", text):
        out["lng"], out["lat"] = float(m.group(1)), float(m.group(2))
    for key in ("Zoom", "Pitch", "Bearing"):
        if m := re.search(rf"{key}:\s*{NUM}", text):
            out[key.lower()] = float(m.group(1))
    return out


def fresh_status(page: Page, at) -> dict:
    """La barra solo se refresca al mover el mouse: 1 px y vuelta."""
    page.mouse.move(at[0] + 1, at[1])
    page.mouse.move(*at)
    time.sleep(0.06)
    return status(page)


def merc_y(lat: float) -> float:
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def pixel_of(page: Page, box: dict, lng: float, lat: float) -> tuple[float, float]:
    """Con pitch 0: calibra pixel<->coordenada pasando el mouse por dos puntos."""
    samples = []
    for fx, fy in ((0.3, 0.3), (0.7, 0.7)):
        x, y = box["x"] + box["width"] * fx, box["y"] + box["height"] * fy
        s = fresh_status(page, (x, y))
        samples.append((x, y, s["lng"], merc_y(s["lat"])))
    (x1, y1, g1, m1), (x2, y2, g2, m2) = samples
    return x1 + (lng - g1) * (x2 - x1) / (g2 - g1), y1 + (merc_y(lat) - m1) * (y2 - y1) / (m2 - m1)


def ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * t)


# ---------- cuadro a cuadro ----------
class Film:
    def __init__(self, page: Page, frames_dir: Path):
        self.page = page
        self.dir = frames_dir
        self.n = 0
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)

    def snap(self, settle: float = 0.1) -> None:
        time.sleep(settle)
        self.page.screenshot(path=str(self.dir / f"{self.n:06d}.jpg"), type="jpeg", quality=93)
        self.n += 1
        if self.n % 60 == 0:
            print(f"  {self.n} cuadros ({self.n / FPS:.0f} s de video)", flush=True)

    def hold(self, seconds: float, settle: float = 0.1) -> None:
        for _ in range(int(seconds * FPS)):
            self.snap(settle)

    def drag(self, start, end, seconds: float, button: str = "left") -> None:
        page = self.page
        page.mouse.move(*start)
        page.mouse.down(button=button)
        n = max(2, int(seconds * FPS))
        for i in range(1, n + 1):
            k = ease(i / n)
            page.mouse.move(start[0] + (end[0] - start[0]) * k, start[1] + (end[1] - start[1]) * k)
            self.snap()
        page.mouse.up(button=button)

    def zoom(self, at, target: float, seconds: float) -> None:
        """Zoom con aceleración y frenado; en cada cuadro corrige contra el zoom real."""
        page = self.page
        z0 = fresh_status(page, at)["zoom"]
        n = max(2, int(seconds * FPS))
        for i in range(1, n + 1):
            desired = z0 + (target - z0) * ease(i / n)
            current = fresh_status(page, at).get("zoom", desired)
            if desired > current:
                page.mouse.wheel(0, -(desired - current) / ZOOM_PER_DELTA)
            self.snap(settle=0.18)

    def encode(self, out: Path) -> None:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(self.dir / "%06d.jpg"),
             "-vf", f"scale={W}:{H}:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "17",
             "-preset", "medium", "-movflags", "+faststart", str(out)],
            check=True,
        )


def tour(page: Page, film: Film) -> None:
    box = page.locator("canvas").first.bounding_box()
    center = (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    caracas = pixel_of(page, box, *CARACAS)
    print("inicio:", fresh_status(page, center), "| Caracas en pixel", caracas)

    film.hold(1.5)                                                         # país completo, vista cenital
    film.drag(caracas, center, 2.0)                                        # Caracas al centro
    s = fresh_status(page, center)
    if abs(s.get("lng", 0) - CARACAS[0]) > 0.3 or abs(s.get("lat", 0) - CARACAS[1]) > 0.3:
        raise RuntimeError(f"El desplazamiento no llegó a Caracas: {s}")
    film.drag(center, (center[0] + 40, center[1] - 110), 3.5, button="right")  # inclinar + girar
    print("tras inclinar:", fresh_status(page, center))
    film.zoom(center, 9.5, 4.0)                                            # acercarse en 3D
    film.zoom(center, 14.8, 6.0)                                           # fundido a edificios de Caracas
    film.hold(1.0, settle=0.25)                                            # deja cargar el mapa base
    film.zoom(center, 15.7, 5.0)                                           # acercamiento lento final
    film.hold(1.0)
    print("final:", fresh_status(page, center))


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(CORSHandler, directory=str(P01)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=False, args=CHROME_FLAGS)
            for attempt in range(1, 4):
                page = browser.new_page(viewport={"width": W, "height": H})
                page.goto(app_url(), wait_until="load")
                # Al terminar de cargar las dos capas, GeoLibre encuadra Venezuela (zoom ~5-5.6).
                page.wait_for_function(
                    "(() => { const m = document.body.innerText.match(/Zoom:\\s*([\\d.]+)/); return m && parseFloat(m[1]) > 4; })()",
                    timeout=180000,
                )
                time.sleep(20)  # GeoLibre sigue procesando las capas unos segundos después de encuadrar
                page.add_style_tag(content="::-webkit-scrollbar{display:none!important} *{scrollbar-width:none!important}")
                film = Film(page, VIDEO / "frames")
                try:
                    tour(page, film)
                except RuntimeError as err:
                    print(f"intento {attempt} fallido: {err}")
                    page.close()
                    continue
                film.encode(VIDEO / "raw.mp4")
                print(f"{film.n} cuadros -> {VIDEO / 'raw.mp4'} ({film.n / FPS:.1f} s)")
                break
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
