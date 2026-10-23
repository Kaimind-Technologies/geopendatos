"""Edición del video de P03: textos bilingües (inglés arriba, español abajo), contador
anual y leyenda de colores, dibujados cuadro a cuadro con Pillow.

Solo se muestran hallazgos que resistieron las verificaciones (PROCESO.md §4.1):
  - 2000-2015: 9 de cada 10 km² nuevos aparecieron pegados a zonas ya urbanas (relleno o
    bordes; 18 variantes del método, VALIDACION.md T4);
  - 2000-2015: el suelo urbano creció algo más lento que la población (ODS 0,88-0,95, T2).
Antes de 2000 se avisa que los saltos de 1991 y 1996 son artefactos de las imágenes (T1).

Lee video/frames_slider/ (record_slider.py) y video/serie_anual.json (layers_slider.py).
Salida: video/p03_geolibre_bilingue.mp4

Uso:
    python -P edit_slider.py
"""

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

VIDEO = Path(__file__).resolve().parent
FRAMES = VIDEO / "frames_slider"
OUT_FRAMES = VIDEO / "frames_edit"
OUT = VIDEO / "p03_geolibre_bilingue.mp4"
FONT_B = "C:/Windows/Fonts/segoeuib.ttf"
FONT_R = "C:/Windows/Fonts/segoeui.ttf"
W, H = 1080, 1350
TOP = 60
WHITE, SOFT, MUTED = (255, 255, 255), (209, 213, 219), (156, 163, 175)
YELLOW, CYAN = (253, 231, 37), (56, 189, 248)
BOX = (11, 16, 32, 180)
FADE = 8
# Mismos colores que geolibre_project.py (COLOR_ANIO)
RAMP = [(1986, (192, 38, 211)), (1995, (244, 63, 94)), (2005, (251, 146, 60)), (2015, (253, 224, 71))]
EXISTENTE = (63, 143, 135)
# Zona que muestra la cámara del video (aprox.), para el minimapa de ubicación
VISTA = (-68.7, 9.1, -66.4, 11.0)
CONTORNO = VIDEO.parent / "output" / "ven_contorno.parquet"


def font(path: str, size: int, text: str, max_w: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(path, size)
    while f.getlength(text) > max_w and size > 14:
        size -= 1
        f = ImageFont.truetype(path, size)
    return f


def top_block(d, lines, alpha: float) -> None:
    heights = [s + 14 for _, _, s, _ in lines]
    d.rectangle([0, TOP, W, TOP + sum(heights) + 44], fill=BOX[:3] + (int(BOX[3] * alpha),))
    y = TOP + 16
    for (text, path, size, color), lh in zip(lines, heights):
        f = font(path, size, text, W - 80)
        d.text(((W - f.getlength(text)) / 2, y), text, font=f, fill=color + (int(255 * alpha),))
        y += lh


def ramp_color(y: float) -> tuple:
    for (y0, c0), (y1, c1) in zip(RAMP, RAMP[1:]):
        if y <= y1:
            t = (y - y0) / (y1 - y0)
            return tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
    return RAMP[-1][1]


def counter(d, year: int, km2: float) -> None:
    x0, y0 = 40, H - 330
    d.rounded_rectangle([x0 - 16, y0 - 12, x0 + 600, y0 + 240], radius=18, fill=BOX)
    d.text((x0, y0 - 12), str(year), font=ImageFont.truetype(FONT_B, 96), fill=YELLOW + (255,))
    en = f"Venezuela: {km2:,.0f} km² of settlement"
    es = f"Venezuela: {km2:,.0f} km² de asentamiento".replace(",", ".")
    d.text((x0, y0 + 108), en, font=font(FONT_B, 28, en, 570), fill=WHITE + (255,))
    d.text((x0, y0 + 144), es, font=font(FONT_R, 26, es, 570), fill=SOFT + (255,))
    # Leyenda: gris = ya existía en 1985; rampa 1986 → 2015 = nuevo.
    ly = y0 + 192
    d.rectangle([x0, ly, x0 + 28, ly + 18], fill=EXISTENTE + (255,))
    d.text((x0 + 36, ly - 4), "1985", font=ImageFont.truetype(FONT_R, 20), fill=SOFT + (255,))
    gx = x0 + 110
    for i in range(220):
        d.line([gx + i, ly, gx + i, ly + 18], fill=ramp_color(1986 + 29 * i / 219) + (255,))
    d.text((gx + 228, ly - 4), "1986 → 2015", font=ImageFont.truetype(FONT_R, 20), fill=SOFT + (255,))
    d.rectangle([gx + 360, ly, gx + 388, ly + 18], outline=CYAN + (255,), width=2)
    d.text((gx + 396, ly - 4), "½ of growth", font=ImageFont.truetype(FONT_R, 20), fill=CYAN + (255,))


def locator() -> Image.Image:
    """Minimapa: Venezuela completa con un recuadro en la zona que muestra el video."""
    import duckdb
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    gj = json.loads(con.execute(f"SELECT ST_AsGeoJSON(geometry) FROM read_parquet('{CONTORNO.as_posix()}')").fetchone()[0])
    polys = gj["coordinates"] if gj["type"] == "MultiPolygon" else [gj["coordinates"]]
    pts = [p for poly in polys for p in poly[0]]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    mw, pad, top = 230, 14, 34
    k = mw / (x1 - x0)
    mh = int((y1 - y0) * k)
    img = Image.new("RGBA", (mw + 2 * pad, mh + top + pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=14, fill=BOX)
    xy = lambda lon, lat: (pad + (lon - x0) * k, top + (y1 - lat) * k)
    for poly in polys:
        d.polygon([xy(*p) for p in poly[0]], fill=(31, 42, 165, 255), outline=(229, 231, 235, 255))
    d.rectangle([xy(VISTA[0], VISTA[3]), xy(VISTA[2], VISTA[1])], outline=YELLOW + (255,), width=3)
    lab = "Venezuela · zona del video"
    f = font(FONT_R, 18, lab, img.width - 2 * pad)
    d.text(((img.width - f.getlength(lab)) / 2, 8), lab, font=f, fill=SOFT + (255,))
    return img


def credit(d) -> None:
    text = "WSF-Evolution (DLR) · GHSL (JRC) · H3 · GeoLibre · Kaimind"
    f = ImageFont.truetype(FONT_R, 18)
    # Por encima del botón de atribución del mapa (esquina inferior derecha).
    x = W - 24 - f.getlength(text)
    d.rounded_rectangle([x - 10, H - 94, W - 14, H - 64], radius=8, fill=BOX)
    d.text((x, H - 92), text, font=f, fill=MUTED + (230,))


def main() -> None:
    schedule = json.loads((FRAMES / "schedule.json").read_text(encoding="utf-8"))
    serie = {int(k): v for k, v in json.loads((VIDEO / "serie_anual.json").read_text(encoding="utf-8"))["km2_acumulados"].items()}
    shutil.rmtree(OUT_FRAMES, ignore_errors=True)
    OUT_FRAMES.mkdir(parents=True)
    first = {}
    for i, y in enumerate(schedule):
        first.setdefault(y, i)
    end0 = first[2015]
    mini = locator()

    for i, y in enumerate(schedule):
        img = Image.open(FRAMES / f"{i:06d}.jpg").convert("RGBA")
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        k = i - end0
        if y == 1985:
            a = min(1, (i + 1) / FADE)
            top_block(d, [("How Venezuela's central cities grew, 1985-2015", FONT_B, 42, WHITE),
                          ("Así crecieron las ciudades del centro de Venezuela, 1985-2015", FONT_R, 32, SOFT),
                          ("Valencia · Maracay · Caracas · Valles del Tuy", FONT_R, 26, MUTED)], a)
        elif y < 2000:
            top_block(d, [("Year by year, from satellite data", FONT_B, 40, WHITE),
                          ("Año a año, con datos satelitales", FONT_R, 32, SOFT),
                          ("Before 2000, read it by decade: the 1991 and 1996 jumps are imagery gaps", FONT_R, 22, MUTED),
                          ("Antes de 2000, léelo por décadas: los saltos de 1991 y 1996 son huecos en las imágenes", FONT_R, 22, MUTED)], 1)
        elif y < 2015 or k < 30:
            top_block(d, [("Year by year, from satellite data", FONT_B, 40, WHITE),
                          ("Año a año, con datos satelitales", FONT_R, 32, SOFT)], 1)
        elif k < 105:
            a = min(1, (k - 29) / FADE)
            top_block(d, [("9 in 10 km² of new settlement grew next to existing urban areas", FONT_B, 40, CYAN),
                          ("9 de cada 10 km² nuevos crecieron pegados a zonas ya urbanas", FONT_B, 32, WHITE),
                          ("(2000-2015 · infill or city edges · two satellite products agree)", FONT_R, 24, MUTED),
                          ("(2000-2015 · relleno o bordes · coinciden dos productos satelitales)", FONT_R, 24, MUTED)], a)
        elif k < 165:
            a = min(1, (k - 104) / FADE)
            top_block(d, [("2000-2015: urban land grew slightly slower than the population", FONT_B, 40, YELLOW),
                          ("2000-2015: el suelo urbano creció algo más lento que la población", FONT_B, 32, WHITE),
                          ("(UN SDG 11.3.1: 0.88-0.95 · satellites and censuses / satélites y censos)", FONT_R, 24, MUTED)], a)
        else:
            a = min(1, (k - 164) / FADE)
            top_block(d, [("Explore it yourself in GeoLibre", FONT_B, 48, WHITE),
                          ("Explóralo tú mismo en GeoLibre", FONT_R, 38, SOFT),
                          ("Link in comments · Link en comentarios", FONT_R, 30, MUTED)], a)
        if y > 1985 and k < 165:
            counter(d, y, serie[y])
        if k < 165:
            layer.alpha_composite(mini, (W - 52 - mini.width, 300))
        credit(d)
        Image.alpha_composite(img, layer).convert("RGB").save(OUT_FRAMES / f"{i:06d}.jpg", quality=94)

    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(OUT_FRAMES / "%06d.jpg"),
                    "-vf", f"scale={W}:{H}:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "17",
                    "-preset", "medium", "-movflags", "+faststart", str(OUT)], check=True)
    print(f"listo: {OUT} ({len(schedule) / 30:.1f} s)")


if __name__ == "__main__":
    main()
