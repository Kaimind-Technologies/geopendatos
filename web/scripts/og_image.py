"""Imagen para redes del sitio (web/public/og.png, 1200×630): la vista previa al compartir el enlace.

Sigue lo que funcionó en P01: el país completo y reconocible, colores vivos sobre fondo claro y
una sola cifra grande. El mapa sale de src/datos/hexmapa.json (el mismo de la portada) y la cifra,
de p01_cifras.json, así que no se escribe a mano.

Usa las fuentes Segoe UI de Windows, como las láminas de las publicaciones.

Uso (desde la raíz del repo):
    python -P web/scripts/og_image.py
"""

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
MAPA = RAIZ / "web" / "src" / "datos" / "hexmapa.json"
P01 = RAIZ / "p01-edificios-overture" / "output" / "p01_cifras.json"
SALIDA = RAIZ / "web" / "public" / "og.png"
W, H = 1200, 630
B, R = "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"
FONDO, TINTA, SUAVE, VERDE = (247, 249, 248), (11, 13, 12), (75, 83, 80), (42, 115, 80)
# Clase 0 = sin construcciones; 1-5 = quintiles, de fucsia claro a violeta profundo (como el video de P01)
COLORES = [(226, 232, 229), (244, 208, 247), (226, 148, 236), (196, 74, 214), (138, 36, 170), (74, 20, 140)]


def poligonos(path: str) -> list[tuple[float, float]]:
    nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", path)))
    return list(zip(nums[0::2], nums[1::2]))


def main() -> None:
    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    total = json.loads(P01.read_text(encoding="utf-8"))["total_edificios"]
    img = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(img)

    # Mapa a la derecha, escalado al alto disponible
    _, _, vw, vh = map(float, mapa["viewBox"].split())
    k = 500 / vh
    ox, oy = W - vw * k - 24, (H - vh * k) / 2
    for clase, _, path in mapa["celdas"]:
        pts = [(ox + x * k, oy + y * k) for x, y in poligonos(path)]
        d.polygon(pts, fill=COLORES[clase], outline=FONDO)

    x = 64
    d.text((x, 70), "VENEZUELA EN DATOS ABIERTOS", font=ImageFont.truetype(B, 22), fill=VERDE)
    d.text((x - 4, 120), f"{total:,}".replace(",", "."), font=ImageFont.truetype(B, 92), fill=TINTA)
    cuerpo = ImageFont.truetype(R, 30)
    for i, linea in enumerate(["construcciones en Venezuela,", "contadas con imágenes satelitales", "y mapas abiertos"]):
        d.text((x, 262 + i * 40), linea, font=cuerpo, fill=SUAVE)
    d.text((x, 400), "structures in Venezuela, counted from satellite imagery", font=ImageFont.truetype(R, 20), fill=SUAVE)
    d.rounded_rectangle([x, 470, x + 330, 520], radius=12, fill=(76, 174, 126))
    d.text((x + 20, 478), "Datos verificables · API v0", font=ImageFont.truetype(B, 24), fill=(0, 0, 0))
    d.text((x, 560), "Kaimind", font=ImageFont.truetype(B, 28), fill=TINTA)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    img.save(SALIDA, optimize=True)
    print("imagen para redes:", SALIDA.relative_to(RAIZ), f"({SALIDA.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
