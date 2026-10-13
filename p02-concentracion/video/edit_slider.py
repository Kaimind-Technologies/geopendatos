"""Edición del video de P02: textos bilingües (inglés arriba, español abajo) y un
contador que sigue cada paso del Time Slider, dibujados cuadro a cuadro con Pillow.

Lee video/frames_slider/ (record_slider.py) y video/steps.json (steps.py), y genera
video/p02_geolibre_bilingue.mp4.

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
OUT = VIDEO / "p02_geolibre_bilingue.mp4"
FONT_B = "C:/Windows/Fonts/segoeuib.ttf"
FONT_R = "C:/Windows/Fonts/segoeui.ttf"
W, H = 1080, 1350
TOP = 60                 # debajo de la barra de menús de GeoLibre
ACCENT = (241, 96, 93)   # mismo coral de la paleta magma
WHITE, SOFT, MUTED = (255, 255, 255), (209, 213, 219), (156, 163, 175)
BOX = (11, 16, 32, 175)
FADE = 8


def font(path: str, size: int, text: str, max_w: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(path, size)
    while f.getlength(text) > max_w and size > 14:
        size -= 1
        f = ImageFont.truetype(path, size)
    return f


def es_num(x: float, dec: int) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def pct_terr(x: float) -> int:
    return 2 if x < 10 else 1


def top_block(d: ImageDraw.ImageDraw, lines: list[tuple[str, str, int, tuple]], alpha: float) -> None:
    """lines: (texto, fuente, tamaño, color). Caja translúcida a todo el ancho."""
    heights = [s + 14 for _, _, s, _ in lines]
    h = sum(heights) + 44
    d.rectangle([0, TOP, W, TOP + h], fill=BOX[:3] + (int(BOX[3] * alpha),))
    y = TOP + 16
    for (text, path, size, color), lh in zip(lines, heights):
        f = font(path, size, text, W - 80)
        d.text(((W - f.getlength(text)) / 2, y), text, font=f, fill=color + (int(255 * alpha),))
        y += lh


def counter(d: ImageDraw.ImageDraw, step: dict, alpha: float) -> None:
    c, t = step["construcciones_pct"], step["territorio_pct"]
    big = f"{round(c):d}%"
    en = f"of all structures, on {t:.{pct_terr(t)}f}% of the land"
    es = f"de las construcciones, en el {es_num(t, pct_terr(t))}% del territorio"
    x0, y0 = 40, H - 300
    d.rounded_rectangle([x0 - 16, y0 - 12, x0 + 760, y0 + 205], radius=18, fill=BOX[:3] + (int(BOX[3] * alpha),))
    fb = ImageFont.truetype(FONT_B, 96)
    d.text((x0, y0 - 10), big, font=fb, fill=ACCENT + (int(255 * alpha),))
    d.text((x0, y0 + 112), en, font=font(FONT_B, 30, en, 740), fill=WHITE + (int(255 * alpha),))
    d.text((x0, y0 + 152), es, font=font(FONT_R, 28, es, 740), fill=SOFT + (int(255 * alpha),))


def credit(d: ImageDraw.ImageDraw) -> None:
    text = "Overture Maps 2026-09-23.1 · H3 ~5 km² · GeoLibre · Kaimind"
    f = ImageFont.truetype(FONT_R, 18)
    d.text((W - 24 - f.getlength(text), H - 62), text, font=f, fill=MUTED + (220,))


def main() -> None:
    schedule = json.loads((FRAMES / "schedule.json").read_text(encoding="utf-8"))
    steps = {s["k"]: s for s in json.loads((VIDEO / "steps.json").read_text(encoding="utf-8"))["steps"]}
    shutil.rmtree(OUT_FRAMES, ignore_errors=True)
    OUT_FRAMES.mkdir(parents=True)
    first_frame = {}
    for i, k in enumerate(schedule):
        first_frame.setdefault(k, i)
    n_end = schedule.count(100)
    end_card_from = first_frame[100] + n_end // 2

    for i, k in enumerate(schedule):
        img = Image.open(FRAMES / f"{i:06d}.jpg").convert("RGBA")
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        if k == 1:
            a = min(1, (i + 1) / FADE)
            top_block(d, [("Where are Venezuela's 10.9 million structures?", FONT_B, 44, WHITE),
                          ("¿Dónde están las 10,9 millones de construcciones de Venezuela?", FONT_R, 34, SOFT)], a)
        elif k < 50 or 50 < k < 100:
            top_block(d, [("Lighting up from densest to emptiest", FONT_B, 42, WHITE),
                          ("Encendemos de lo más denso a lo más vacío", FONT_R, 34, SOFT)], 1)
        elif k == 50:
            a = min(1, (i - first_frame[50] + 1) / FADE)
            top_block(d, [("Half of all structures sit on 0.5% of the land", FONT_B, 46, ACCENT),
                          ("La mitad de las construcciones está en el 0,5% del territorio", FONT_B, 36, WHITE)], a)
        elif i < end_card_from:
            a = min(1, (i - first_frame[100] + 1) / FADE)
            top_block(d, [("In more than half of the country, not a single rooftop", FONT_B, 42, WHITE),
                          ("En más de la mitad del país no hay ni un techo", FONT_R, 36, SOFT),
                          ("(5 km² cells · celdas de 5 km²)", FONT_R, 26, MUTED)], a)
        else:
            a = min(1, (i - end_card_from + 1) / FADE)
            top_block(d, [("Explore it yourself in GeoLibre", FONT_B, 48, WHITE),
                          ("Explóralo tú mismo en GeoLibre", FONT_R, 38, SOFT),
                          ("Link in comments · Link en comentarios", FONT_R, 30, MUTED)], a)

        if k > 1 and i < end_card_from:
            counter(d, steps[k], 1)
        credit(d)
        Image.alpha_composite(img, layer).convert("RGB").save(OUT_FRAMES / f"{i:06d}.jpg", quality=94)

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(OUT_FRAMES / "%06d.jpg"),
         "-vf", f"scale={W}:{H}:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-movflags", "+faststart", str(OUT)],
        check=True,
    )
    print(f"listo: {OUT} ({len(schedule) / 30:.1f} s)")


if __name__ == "__main__":
    main()
