"""Tabla del contador del video de P02: para cada paso k del Time Slider (año 1900+k),
qué % real de las construcciones y qué % del territorio están encendidos.

El territorio es la suma de las áreas reales de las celdas H3 res 7 de Venezuela
(incluidas las vacías), el mismo denominador que robustness.py.

Salida: video/steps.json

Uso:
    python -P steps.py
"""

import json
from pathlib import Path

import duckdb

P02 = Path(__file__).resolve().parents[1]
ROOT = P02.parent
RANKING = P02 / "output" / "hex_r7_ranking.parquet"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
OUT = Path(__file__).resolve().parent / "steps.json"


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    terr_km2 = con.execute(f"""
        WITH parts AS (SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}')),
        terr AS (SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), 7)) AS cell FROM parts),
        occ AS (SELECT h3_string_to_h3(h3) AS cell FROM read_parquet('{RANKING.as_posix()}'))
        SELECT sum(h3_cell_area(cell, 'km^2')) FROM (SELECT cell FROM terr UNION SELECT cell FROM occ)
    """).fetchone()[0]
    total = con.execute(f"SELECT sum(construcciones) FROM read_parquet('{RANKING.as_posix()}')").fetchone()[0]
    rows = con.execute(f"""
        WITH r AS (SELECT anio, construcciones, h3_cell_area(h3_string_to_h3(h3), 'km^2') AS km2
                   FROM read_parquet('{RANKING.as_posix()}')),
        k AS (SELECT range AS k FROM range(1, 101))
        SELECT k.k, sum(r.construcciones) AS constr, sum(r.km2) AS km2
        FROM k LEFT JOIN r ON r.anio <= 1900 + k.k
        GROUP BY k.k ORDER BY k.k
    """).fetchall()
    steps = [{"k": k, "construcciones_pct": round(100 * (c or 0) / total, 2),
              "territorio_pct": round(100 * (a or 0) / terr_km2, 2)} for k, c, a in rows]
    OUT.write_text(json.dumps({"territorio_km2": round(terr_km2), "total": int(total), "steps": steps},
                              indent=2, ensure_ascii=False), encoding="utf-8")
    for s in steps:
        if s["k"] in (1, 10, 25, 50, 75, 90, 100):
            print(s)


if __name__ == "__main__":
    main()
