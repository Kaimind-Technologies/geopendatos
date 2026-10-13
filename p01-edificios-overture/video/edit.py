"""Edición final de P01: textos sobre video/raw.mp4 -> video/p01_geolibre.mp4.

Los textos se escriben a archivos UTF-8 (textfile) para no pelear con el escape
de acentos y signos en los filtros de ffmpeg.

Uso:
    python -P edit.py
"""

import argparse
import subprocess
from pathlib import Path

VIDEO = Path(__file__).resolve().parent
TXT = VIDEO / "_txt"
FONT_BOLD = "C\\:/Windows/Fonts/segoeuib.ttf"
FONT = "C\\:/Windows/Fonts/segoeui.ttf"
TOP = 96  # debajo de la barra de menús de GeoLibre

# (inicio, fin, texto, tamaño, y, negrita, color)
TEXTS = [
    (0.3, 5.5, "10.861.395", 118, TOP + 26, True, "white"),
    (0.6, 5.5, "construcciones detectadas en Venezuela", 42, TOP + 168, False, "#e5e7eb"),
    (5.8, 10.6, "Venezuela no tiene censo desde 2011", 44, TOP + 40, True, "white"),
    (6.1, 10.6, "Los mapas abiertos sí saben dónde está cada construcción", 34, TOP + 104, False, "#e5e7eb"),
    (12.0, 19.0, "El 92% las dibujó una IA", 56, TOP + 34, True, "white"),
    (19.4, 24.5, "Explóralo tú mismo en GeoLibre", 50, TOP + 34, True, "white"),
    (19.7, 24.5, "Datos y código abiertos · link en comentarios", 34, TOP + 108, False, "#e5e7eb"),
]
# Versión bilingüe: inglés arriba (negrita), español abajo, igual que el post.
TEXTS_BI = [
    (0.3, 5.5, "10.861.395", 112, TOP + 18, True, "white"),
    (0.6, 5.5, "rooftops detected in Venezuela", 38, TOP + 150, True, "#f3f4f6"),
    (0.6, 5.5, "construcciones detectadas en Venezuela", 34, TOP + 200, False, "#d1d5db"),
    (5.8, 10.6, "No census since 2011", 48, TOP + 28, True, "white"),
    (6.1, 10.6, "Venezuela no tiene censo desde 2011", 36, TOP + 92, False, "#d1d5db"),
    (12.0, 19.0, "92% traced by AI", 52, TOP + 22, True, "white"),
    (12.2, 19.0, "El 92% las trazó una IA", 36, TOP + 86, False, "#d1d5db"),
    (19.4, 24.5, "Explore it yourself in GeoLibre", 46, TOP + 22, True, "white"),
    (19.6, 24.5, "Explóralo tú mismo en GeoLibre", 36, TOP + 82, False, "#d1d5db"),
    (19.8, 24.5, "Link in comments · Link en comentarios", 30, TOP + 136, False, "#e5e7eb"),
]
# Leyenda de fuentes (colores iguales a styles/caracas.style.json)
LEGEND = [("Microsoft · 48%", "#3b82f6"), ("Google · 44%", "#f59e0b"), ("OpenStreetMap · 8%", "#22c55e")]
LEGEND_SPAN = (12.4, 19.0)
BOXES = [(0.3, 5.5, 250), (5.8, 10.6, 170), (12.0, 19.0, 250), (19.4, 24.5, 170)]
BOXES_BI = [(0.3, 5.5, 270), (5.8, 10.6, 160), (12.0, 19.0, 220), (19.4, 24.5, 190)]
LEGEND_Y = {"es": TOP + 120, "bi": TOP + 140}


def alpha(t0: float, t1: float, fade: float = 0.35) -> str:
    return (f"if(lt(t,{t0}),0,if(lt(t,{t0 + fade}),(t-{t0})/{fade},"
            f"if(lt(t,{t1 - fade}),1,if(lt(t,{t1}),({t1}-t)/{fade},0))))")


def textfile(i: int, text: str) -> str:
    TXT.mkdir(exist_ok=True)
    path = TXT / f"{i}.txt"
    path.write_text(text, encoding="utf-8")
    return path.as_posix().replace(":", "\\:")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(VIDEO / "raw.mp4"))
    parser.add_argument("--lang", choices=["es", "bi"], default="es")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.output is None:
        args.output = str(VIDEO / ("p01_geolibre.mp4" if args.lang == "es" else "p01_geolibre_bilingue.mp4"))
    texts, boxes = (TEXTS, BOXES) if args.lang == "es" else (TEXTS_BI, BOXES_BI)
    filters = []
    for t0, t1, h in boxes:
        filters.append(f"drawbox=x=0:y={TOP}:w=iw:h={h}:color=0x0b1020@0.62:t=fill:enable='between(t,{t0},{t1})'")
    for i, (t0, t1, text, size, y, bold, color) in enumerate(texts):
        font = FONT_BOLD if bold else FONT
        filters.append(
            f"drawtext=fontfile='{font}':textfile='{textfile(i, text)}':fontsize={size}:fontcolor={color}:expansion=none"
            f":x=(w-text_w)/2:y={y}:alpha='{alpha(t0, t1)}'"
        )
    t0, t1 = LEGEND_SPAN
    y = LEGEND_Y[args.lang]
    x0 = 120
    for j, (label, color) in enumerate(LEGEND):
        x = x0 + j * 290
        filters.append(f"drawbox=x={x}:y={y + 14}:w=26:h=26:color={color}:t=fill:enable='between(t,{t0},{t1})'")
        filters.append(
            f"drawtext=fontfile='{FONT}':textfile='{textfile(100 + j, label)}':fontsize=30:fontcolor=white:expansion=none"
            f":x={x + 38}:y={y + 8}:alpha='{alpha(t0, t1)}'"
        )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", args.input, "-vf", ",".join(filters),
         "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         args.output],
        check=True,
    )
    print("listo:", args.output)


if __name__ == "__main__":
    main()
