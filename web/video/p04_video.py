"""Video del lanzamiento de la web (P04), 1080×1350, ~20 s, bilingüe.

Sigue lo que funcionó en P01 (ver el análisis de alcance): desde el primer cuadro, Venezuela
completa y reconocible sobre fondo claro, con una sola cifra gigante. Después, los tres hallazgos
de la serie, un recorrido por la web y el cierre con la dirección.

Las cifras salen de los JSON del repo (P01, P02 y la API v0), no se escriben a mano. El recorrido
se captura de la web construida (`npm run build` + `npx vite preview --port 4173`).

Uso (desde la raíz del repo, con la vista previa corriendo):
    python -P web/video/p04_video.py --url datos.kaimindconsulting.com
Salida: web/video/p04_web_bilingue.mp4 (no va al repo)
"""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
CUADROS = AQUI / "frames_p04"
SALIDA = AQUI / "p04_web_bilingue.mp4"
MAPA = RAIZ / "web" / "src" / "datos" / "hexmapa.json"
W, H, FPS = 1080, 1350, 30
B, R = "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"
FONDO, TINTA, SUAVE, VERDE, VERDE_K = (247, 249, 248), (11, 13, 12), (75, 83, 80), (42, 115, 80), (76, 174, 126)
COLORES = [(226, 232, 229), (244, 208, 247), (226, 148, 236), (196, 74, 214), (138, 36, 170), (74, 20, 140)]


def f(path, size):
    return ImageFont.truetype(path, size)


def centrado(d, y, texto, fuente, color):
    d.text(((W - fuente.getlength(texto)) / 2, y), texto, font=fuente, fill=color)


def mapa_img(alto: int, alpha: float = 1.0) -> Image.Image:
    m = json.loads(MAPA.read_text(encoding="utf-8"))
    _, _, vw, vh = map(float, m["viewBox"].split())
    k = alto / vh
    img = Image.new("RGBA", (int(vw * k) + 2, alto + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for clase, _, path in m["celdas"]:
        nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", path)))
        pts = [(x * k, y * k) for x, y in zip(nums[0::2], nums[1::2])]
        d.polygon(pts, fill=COLORES[clase] + (int(255 * alpha),), outline=FONDO + (int(255 * alpha),))
    return img


def cifras() -> dict:
    p01 = json.loads((RAIZ / "p01-edificios-overture/output/p01_cifras.json").read_text(encoding="utf-8"))
    rob = json.loads((RAIZ / "p02-concentracion/output/p02_robustez.json").read_text(encoding="utf-8"))
    ind = {i["id"]: i for i in json.loads((RAIZ / "web/public/api/v0/indicadores.json").read_text(encoding="utf-8"))}
    r7 = next(r for r in rob if r["resolucion_h3"] == 7 and r["filtro_area_min_m2"] == 0)
    return {"total": f"{p01['total_edificios']:,}".replace(",", "."),
            "mitad": f"{r7['A_mitad_pct_territorio']:.1f}".replace(".", ","),
            "pegado": ind["crecimiento_pegado_a_lo_urbano_pct"]["rango"],
            "n_ind": len(ind)}


def escena_portada(c, mapa, t: float) -> Image.Image:
    """0-3 s: la cifra gigante sobre el país completo (el cuadro 0 ya tiene que funcionar solo)."""
    img = Image.new("RGB", (W, H), FONDO)
    img.paste(mapa, ((W - mapa.width) // 2, 430), mapa)
    d = ImageDraw.Draw(img)
    centrado(d, 70, "VENEZUELA EN DATOS ABIERTOS", f(B, 30), VERDE)
    centrado(d, 120, c["total"], f(B, 150), TINTA)
    centrado(d, 300, "construcciones en Venezuela", f(R, 44), SUAVE)
    centrado(d, 358, "structures in Venezuela", f(R, 32), SUAVE)
    return img


def escena_hallazgo(c, mapa_tenue, codigo, es, en, nota) -> Image.Image:
    img = Image.new("RGB", (W, H), FONDO)
    img.paste(mapa_tenue, ((W - mapa_tenue.width) // 2, 470), mapa_tenue)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 120, W - 60, 560], radius=36, fill=(255, 255, 255), outline=(226, 232, 229), width=3)
    d.text((110, 160), codigo, font=f(B, 34), fill=VERDE)
    y = 220
    for linea in es:
        d.text((110, y), linea, font=f(B, 58), fill=TINTA)
        y += 72
    d.text((110, y + 14), en, font=f(R, 30), fill=SUAVE)
    d.text((110, y + 62), nota, font=f(R, 26), fill=SUAVE)
    return img


def capturar_web(base: str) -> Image.Image:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 880, "height": 1500}, color_scheme="light", device_scale_factor=1)
        pg.goto(base, wait_until="networkidle")
        pg.wait_for_timeout(800)
        img = pg.screenshot(full_page=True)
        b.close()
    from io import BytesIO
    return Image.open(BytesIO(img)).convert("RGB")


def escena_web(pagina: Image.Image, y_pag: int, url: str, titulo: tuple[str, str]) -> Image.Image:
    img = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(img)
    centrado(d, 60, titulo[0], f(B, 50), TINTA)
    centrado(d, 128, titulo[1], f(R, 32), SUAVE)
    # Ventana de navegador con la web adentro
    x0, y0, ancho, alto = 60, 210, W - 120, H - 270
    d.rounded_rectangle([x0, y0, x0 + ancho, y0 + alto], radius=28, fill=(255, 255, 255), outline=(210, 216, 213), width=3)
    d.rounded_rectangle([x0 + 24, y0 + 18, x0 + ancho - 24, y0 + 66], radius=24, fill=(240, 243, 241))
    d.text((x0 + 52, y0 + 27), url, font=f(B, 26), fill=VERDE)
    escala = (ancho - 6) / pagina.width
    alto_vista = int((alto - 90) / escala)
    recorte = pagina.crop((0, y_pag, pagina.width, min(pagina.height, y_pag + alto_vista)))
    recorte = recorte.resize((ancho - 6, int(recorte.height * escala)), Image.LANCZOS)
    img.paste(recorte, (x0 + 3, y0 + 84))
    return img


def escena_cierre(url: str, n_ind: int) -> Image.Image:
    img = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(img)
    centrado(d, 360, "Explóralo y úsalo", f(B, 72), TINTA)
    centrado(d, 455, "Explore it and use it", f(R, 40), SUAVE)
    d.rounded_rectangle([90, 580, W - 90, 700], radius=30, fill=VERDE_K)
    centrado(d, 607, url, f(B, 52), (0, 0, 0))
    for i, linea in enumerate([f"{n_ind} indicadores en una API abierta", "cada uno con su método, su fuente y su licencia",
                               "y lo que descartamos, también"]):
        centrado(d, 780 + i * 52, linea, f(R, 36), SUAVE)
    centrado(d, 1180, "Kaimind", f(B, 44), TINTA)
    return img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="datos.kaimindconsulting.com", help="dirección que se muestra en el video")
    ap.add_argument("--base", default="http://localhost:4173/", help="web construida para el recorrido")
    args = ap.parse_args()
    c = cifras()
    mapa, tenue = mapa_img(860), mapa_img(800, alpha=0.35)
    pagina = capturar_web(args.base)
    shutil.rmtree(CUADROS, ignore_errors=True)
    CUADROS.mkdir(parents=True)
    a, b = c["pegado"]
    hallazgos = [
        ("P01", ["10,9 millones de", "construcciones"], "10.9 million structures, counted from space", "Overture Maps · DuckDB · GeoLibre"),
        ("P02", ["La mitad, en el", f"{c['mitad']} % del territorio"], f"Half of them on {c['mitad'].replace(',', '.')}% of the land", "hexágonos de ~5 km² · menos del 1 % en toda escala"),
        ("P03", ["9 de cada 10 km² nuevos,", "pegados a lo ya urbano"], "9 in 10 new km² grew next to existing cities", f"2000-2015 · {a}-{b} % · dos productos satelitales"),
    ]
    escenas = [(lambda t: escena_portada(c, mapa, t), 3.0)]
    escenas += [(lambda t, h=h: escena_hallazgo(c, tenue, *h), 2.2) for h in hallazgos]
    # Recorrido por la web: de la portada a la API, con desplazamiento suave
    fin = max(0, pagina.height - 2200)
    paso_web = 7.0
    titulo = ("Ahora, todo en una web y una API abierta", "Now it's all in one website and an open API")
    escenas.append((lambda t: escena_web(pagina, int(fin * (t / paso_web) ** 1.1), args.url, titulo), paso_web))
    escenas.append((lambda t: escena_cierre(args.url, c["n_ind"]), 3.5))
    n = 0
    for dibujar, segundos in escenas:
        for i in range(int(segundos * FPS)):
            dibujar(i / FPS).save(CUADROS / f"{n:06d}.jpg", quality=92)
            n += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(CUADROS / "%06d.jpg"),
                    "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-movflags", "+faststart", str(SALIDA)], check=True)
    print(f"listo: {SALIDA} ({n / FPS:.1f} s, {n} cuadros)")


if __name__ == "__main__":
    main()
