"""P03 · Lámina "Cómo verificamos" (1080×1350) para el post: fuentes, tests, qué se publica
y qué se descartó. El contenido sale de PROCESO.md §3-§4.1; si cambia una verificación,
actualizar aquí también.

Salida: output/como_verificamos.png

Uso:
    python -P lamina_proceso.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "output" / "como_verificamos.png"
W, H = 1080, 1350
BG, CARD = (11, 16, 32), (22, 29, 51)
WHITE, SOFT, MUTED = (243, 244, 246), (209, 213, 219), (148, 156, 175)
GREEN, RED, CYAN, YELLOW = (74, 222, 128), (248, 113, 113), (103, 232, 249), (253, 231, 37)
B, R = "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"
SYM = "C:/Windows/Fonts/seguisym.ttf"  # Segoe UI no trae ✓ ni ✗

SECCIONES = [
    ("1 · Fuentes abiertas", "Open data sources", CYAN, None, [
        "GHSL (JRC): m² construidos 1975-2020, 100 m",
        "WSF-Evolution (DLR): año de asentamiento 1985-2015, 30 m",
        "GHS-POP (JRC) y censos del INE 2001 y 2011",
    ]),
    ("2 · Tests a cada cifra", "Every number tested", YELLOW, None, [
        "Dos satélites, dos métodos: GHSL contra WSF",
        "Población modelada contra el censo (correlación 0,99)",
        "Por ciudad: 4 combinaciones de fuentes deben coincidir",
        "Significancia por simulación (Monte Carlo), no por la curva normal",
    ]),
    ("3 · Lo que publicamos", "What we publish", GREEN, "✓", [
        "La mitad del crecimiento 2000-2015 cayó en menos del 1% del territorio",
        "Más de la mitad del crecimiento fue en los bordes de las ciudades",
        "Maracaibo, Barquisimeto, Barcelona-PLC y Margarita se densificaron",
        "A largo plazo, el suelo urbano creció al ritmo de la población",
    ]),
    ("4 · Lo que descartamos", "What we discarded", RED, "✗", [
        "El \"boom\" de los 90 del GHSL: la otra fuente no lo confirma",
        "Multiplicadores por ciudad desde 1975 (Maturín ×4, Margarita ×6)",
        "\"Caracas se expandió\": depende de cómo se mida su población",
        "\"70% en el 1,36%\" (puntos calientes): no resistió Monte Carlo",
    ]),
]


def fit(path: str, size: int, text: str, max_w: int) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(path, size)
    while f.getlength(text) > max_w and size > 14:
        size -= 1
        f = ImageFont.truetype(path, size)
    return f


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((60, 52), "Cómo verificamos cada cifra", font=ImageFont.truetype(B, 58), fill=WHITE)
    d.text((60, 128), "How we verified every number · P03, crecimiento urbano de Venezuela", font=fit(R, 28, "x" * 70, 960), fill=MUTED)
    y = 186
    for titulo, sub, color, mark, items in SECCIONES:
        alto = 84 + 42 * len(items)
        d.rounded_rectangle([40, y, W - 40, y + alto], radius=22, fill=CARD)
        d.rectangle([40, y + 18, 48, y + alto - 18], fill=color)
        d.text((76, y + 18), titulo, font=ImageFont.truetype(B, 34), fill=color)
        tf = ImageFont.truetype(B, 34)
        d.text((76 + tf.getlength(titulo) + 16, y + 30), sub, font=ImageFont.truetype(R, 22), fill=MUTED)
        iy = y + 68
        for it in items:
            d.text((80, iy), mark or "•", font=ImageFont.truetype(SYM if mark else B, 28), fill=color)
            d.text((120, iy + 2), it, font=fit(R, 27, it, W - 180), fill=SOFT)
            iy += 42
        y += alto + 16
    foot = "Proceso completo: github.com/Kaimind-Technologies/venezuela-datos-abiertos"
    d.text((60, H - 82), foot, font=fit(R, 24, foot, 760), fill=MUTED)
    d.text((W - 60 - ImageFont.truetype(B, 30).getlength("Kaimind"), H - 86), "Kaimind", font=ImageFont.truetype(B, 30), fill=WHITE)
    img.save(OUT)
    print("lámina:", OUT, "· alto usado:", y)


if __name__ == "__main__":
    main()
