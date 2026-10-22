"""P03 · Capas del Time Slider con WSF-Evolution (años reales 1985-2015).

Desde la tabla de píxeles WSF (wsf_layers.py), para hexágonos H3 res 7 (~5 km², vista
nacional del video) y res 8 (~0,74 km², exploración por ciudad):
  - anio: primer año en que el asentamiento acumulado del hexágono superó el 10% de su área
          (1985 = ya lo superaba en 1985, el primer año del WSF);
  - asentamiento_2015_pct: % del hexágono que es asentamiento en 2015.
Además, la serie nacional anual (km² acumulados) que usa el contador del video.

Salidas: output/hex_r7_urbanizacion_wsf.parquet, output/hex_r8_urbanizacion_wsf.parquet,
         video/serie_anual.json

Uso:
    python -P layers_slider.py
"""

import json
from pathlib import Path

import duckdb

P03 = Path(__file__).resolve().parent
ROOT = P03.parent
PIX = ROOT / "data" / "wsf_evo" / "pixeles.parquet"
OUT = P03 / "output"
UMBRAL = 0.10


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    for res in (7, 8):
        out = OUT / f"hex_r{res}_urbanizacion_wsf.parquet"
        con.execute(f"""
            COPY (
                WITH h AS (
                    SELECT h3_latlng_to_cell(lat, lng, {res}) AS cell, anio, sum(area_m2) AS m2
                    FROM read_parquet('{PIX.as_posix()}') GROUP BY cell, anio
                ), c AS (
                    SELECT cell, anio, sum(m2) OVER (PARTITION BY cell ORDER BY anio) AS acum,
                           h3_cell_area(cell, 'm^2') AS celda_m2 FROM h
                )
                SELECT h3_h3_to_string(cell) AS h3,
                       min(anio) FILTER (WHERE acum / celda_m2 >= {UMBRAL})::INTEGER AS anio,
                       round(100 * max(acum) / any_value(celda_m2), 1) AS asentamiento_2015_pct,
                       ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell)), 'OGC:CRS84') AS geometry
                FROM c GROUP BY cell
                HAVING max(acum) / any_value(celda_m2) >= {UMBRAL}
            ) TO '{out.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
        """)
        n, nuevos = con.execute(f"SELECT count(*), count(*) FILTER (WHERE anio > 1985) FROM read_parquet('{out.as_posix()}')").fetchone()
        print(f"res {res}: {n:,} hexágonos ({nuevos:,} se urbanizaron después de 1985) · {out.stat().st_size / 1e6:.1f} MB")

    serie = con.execute(f"""
        SELECT anio, sum(sum(area_m2)) OVER (ORDER BY anio) / 1e6 AS km2
        FROM read_parquet('{PIX.as_posix()}') GROUP BY anio ORDER BY anio
    """).fetchall()
    data = {"fuente": "WSF-Evolution (DLR), recortado con el contorno de Venezuela (geoBoundaries ADM0)",
            "km2_acumulados": {int(a): round(k, 1) for a, k in serie}}
    (P03 / "video").mkdir(exist_ok=True)
    (P03 / "video" / "serie_anual.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("serie anual:", serie[0], "...", serie[-1])


if __name__ == "__main__":
    main()
