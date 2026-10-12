"""Paso 3 de P01: capas de visualización a partir de output/ven_edificios.parquet.

Salidas en output/:
    ven_h3_r7.parquet   hexágonos H3 (resolución 7, ~5 km²) con conteo de edificios,
                        capa liviana para la vista nacional en GeoLibre
    mapa_p01.png        mapa estático 1080x1350 (portada / respaldo del video)

Uso:
    python -P layers.py
"""

import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm

OUT_DIR = Path(__file__).resolve().parent / "output"
BUILDINGS = OUT_DIR / "ven_edificios.parquet"
H3_OUT = OUT_DIR / "ven_h3_r7.parquet"
PNG_OUT = OUT_DIR / "mapa_p01.png"
CIFRAS = OUT_DIR / "p01_cifras.json"
RES = 7


def build_h3(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"""
        CREATE TABLE hex AS
        SELECT h3_latlng_to_cell(ST_Y(ST_Centroid(geometry)), ST_X(ST_Centroid(geometry)), {RES}) AS cell,
               count(*) AS edificios
        FROM read_parquet('{BUILDINGS.as_posix()}')
        GROUP BY cell
    """)
    con.execute(f"""
        COPY (
            SELECT h3_h3_to_string(cell) AS h3, edificios,
                   ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell)), 'OGC:CRS84') AS geometry
            FROM hex
        ) TO '{H3_OUT.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)


def render_png(con: duckdb.DuckDBPyConnection) -> None:
    rows = con.execute(
        "SELECT h3_cell_to_boundary_wkt(cell), edificios FROM hex ORDER BY edificios"
    ).fetchall()
    polys, values = [], []
    for wkt, n in rows:
        coords = wkt[wkt.index("((") + 2 : wkt.index("))")].split(",")
        polys.append([tuple(map(float, c.strip().split())) for c in coords])
        values.append(n)

    total = json.loads(CIFRAS.read_text(encoding="utf-8"))["total_edificios"]
    total_txt = f"{total:,}".replace(",", ".")

    fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor="#0b1020")
    ax = fig.add_axes([0.04, 0.12, 0.92, 0.72], facecolor="#0b1020")
    coll = PolyCollection(polys, array=np.array(values), cmap="magma",
                          norm=LogNorm(vmin=1, vmax=max(values)), linewidths=0)
    ax.add_collection(coll)
    ax.set_xlim(-73.5, -59.6)
    ax.set_ylim(0.5, 12.4)  # recorta Isla de Aves para que el país se vea grande
    ax.set_aspect("equal")
    ax.axis("off")

    fig.text(0.06, 0.93, total_txt, color="white", fontsize=64, fontweight="bold")
    fig.text(0.06, 0.885, "edificios detectados en Venezuela con mapas abiertos",
             color="#d6d9e6", fontsize=22)
    fig.text(0.06, 0.06, "Cada hexágono ≈ 5 km². Color = número de edificios (escala log).",
             color="#9aa0b5", fontsize=14)
    fig.text(0.06, 0.035, "Datos: Overture Maps Foundation (release 2026-09-23.1) · Límites: geoBoundaries / OCHA / INE",
             color="#9aa0b5", fontsize=12)
    fig.text(0.06, 0.012, "Kaimind", color="#d6d9e6", fontsize=13, fontweight="bold")
    fig.savefig(PNG_OUT, facecolor=fig.get_facecolor())


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    build_h3(con)
    render_png(con)
    stats = con.execute("SELECT count(*), sum(edificios), max(edificios) FROM hex").fetchone()
    print(f"hexágonos: {stats[0]:,} | edificios: {stats[1]:,} | máximo por hexágono: {stats[2]:,}")
    print(f"{H3_OUT.name}: {H3_OUT.stat().st_size / 1e6:.1f} MB")
    print(f"{PNG_OUT.name}: listo")


if __name__ == "__main__":
    main()
