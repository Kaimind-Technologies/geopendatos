"""P02: cómo se distribuyen las construcciones de Venezuela.

Parte del GeoParquet de P01 (10.861.395 construcciones) y calcula, todo en local:
- área de cada techo (proyección de áreas iguales EPSG:6933),
- métricas por hexágono H3 (res 7, 8 y 9): construcciones, m² de techo,
  cobertura (% del suelo techado) y tamaño medio de techo,
- curva de concentración (qué % del territorio concentra qué % de construcciones),
- los hexágonos más densos por conteo y por cobertura.

Salidas en output/:
    p02_cifras.json   cifras del post
    hex_r8.parquet    capa GeoParquet para GeoLibre (res 8, ~0,74 km²)
    hex_r9_top.parquet hexágonos res 9 (~0,1 km²) más densos

Uso:
    python -P analyze.py
"""

import json
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
P01_BUILDINGS = ROOT / "p01-edificios-overture" / "output" / "ven_edificios.parquet"
DERIVED = ROOT / "data" / "derived" / "ven_construcciones_metricas.parquet"
OUT = Path(__file__).resolve().parent / "output"
VEN_KM2 = 916_445  # superficie oficial, sin la Guayana Esequiba


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    DERIVED.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")

    if not DERIVED.exists():
        con.execute(f"""
            COPY (
                SELECT id, estado, fuente,
                       ST_Area(ST_Transform(geometry, 'EPSG:6933')) AS area_m2,
                       ST_Y(ST_Centroid(geometry)) AS lat,
                       ST_X(ST_Centroid(geometry)) AS lng
                FROM read_parquet('{P01_BUILDINGS.as_posix()}')
            ) TO '{DERIVED.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
        """)
        print(f"áreas calculadas en {time.perf_counter() - t0:.0f} s")

    con.execute(f"""
        CREATE TABLE b AS
        SELECT *, h3_latlng_to_cell(lat, lng, 7) AS r7, h3_latlng_to_cell(lat, lng, 8) AS r8,
               h3_latlng_to_cell(lat, lng, 9) AS r9
        FROM read_parquet('{DERIVED.as_posix()}')
    """)

    def hex_table(res: int) -> None:
        con.execute(f"""
            CREATE TABLE h{res} AS
            SELECT r{res} AS cell, count(*) AS construcciones, sum(area_m2) AS techo_m2,
                   median(area_m2) AS techo_mediana_m2,
                   h3_cell_area(r{res}, 'm^2') AS celda_m2,
                   any_value(estado) AS estado
            FROM b GROUP BY r{res}
        """)
        con.execute(f"ALTER TABLE h{res} ADD COLUMN cobertura DOUBLE")
        con.execute(f"UPDATE h{res} SET cobertura = techo_m2 / celda_m2")

    for res in (7, 8, 9):
        hex_table(res)

    total, techo_total = con.execute("SELECT count(*), sum(area_m2) FROM b").fetchone()

    # Curva de concentración con hexágonos res 7 (los mismos de P01).
    con.execute("""
        CREATE TABLE curva AS
        SELECT construcciones, celda_m2,
               sum(construcciones) OVER w AS acum, sum(celda_m2) OVER w AS acum_m2
        FROM h7 WINDOW w AS (ORDER BY construcciones DESC ROWS UNBOUNDED PRECEDING)
    """)
    curva = []
    for p in (0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
        km2 = con.execute(f"SELECT min(acum_m2) / 1e6 FROM curva WHERE acum >= {p} * {total}").fetchone()[0]
        curva.append({"pct_construcciones": int(p * 100), "km2": round(km2), "pct_territorio": round(100 * km2 / VEN_KM2, 2)})

    def top(res: int, order: str, n: int = 10) -> list[dict]:
        rows = con.execute(f"""
            SELECT h3_h3_to_string(cell), construcciones, round(techo_m2), round(100 * cobertura, 1),
                   round(techo_mediana_m2), estado,
                   round(h3_cell_to_lat(cell), 5), round(h3_cell_to_lng(cell), 5)
            FROM h{res} ORDER BY {order} DESC LIMIT {n}
        """).fetchall()
        keys = ["h3", "construcciones", "techo_m2", "cobertura_pct", "techo_mediana_m2", "estado", "lat", "lng"]
        return [dict(zip(keys, r)) for r in rows]

    por_estado = con.execute("""
        SELECT estado, count(*) AS construcciones, round(median(area_m2)) AS techo_mediana_m2,
               round(sum(area_m2) / 1e6, 1) AS techo_km2
        FROM b GROUP BY estado ORDER BY construcciones DESC
    """).fetchall()

    cifras = {
        "total_construcciones": total,
        "techo_total_km2": round(techo_total / 1e6, 1),
        "techo_pct_territorio": round(100 * techo_total / 1e6 / VEN_KM2, 3),
        "techo_mediana_m2_nacional": con.execute("SELECT round(median(area_m2)) FROM b").fetchone()[0],
        "curva_concentracion_r7": curva,
        "top_r9_por_construcciones": top(9, "construcciones"),
        "top_r9_por_cobertura": top(9, "cobertura"),
        "top_r8_por_construcciones": top(8, "construcciones", 5),
        "por_estado": [{"estado": e, "construcciones": n, "techo_mediana_m2": m, "techo_km2": k} for e, n, m, k in por_estado],
    }
    (OUT / "p02_cifras.json").write_text(json.dumps(cifras, indent=2, ensure_ascii=False), encoding="utf-8")

    con.execute(f"""
        COPY (
            SELECT h3_h3_to_string(cell) AS h3, construcciones, round(techo_m2) AS techo_m2,
                   round(100 * cobertura, 2) AS cobertura_pct, round(techo_mediana_m2) AS techo_mediana_m2, estado,
                   ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell)), 'OGC:CRS84') AS geometry
            FROM h8
        ) TO '{(OUT / "hex_r8.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    con.execute(f"""
        COPY (
            SELECT h3_h3_to_string(cell) AS h3, construcciones, round(techo_m2) AS techo_m2,
                   round(100 * cobertura, 2) AS cobertura_pct, round(techo_mediana_m2) AS techo_mediana_m2, estado,
                   ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell)), 'OGC:CRS84') AS geometry
            FROM h9 WHERE construcciones >= 300
        ) TO '{(OUT / "hex_r9_top.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)

    resumen = {k: v for k, v in cifras.items() if k not in ("por_estado",)}
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    for f in ("hex_r8.parquet", "hex_r9_top.parquet"):
        print(f"{f}: {(OUT / f).stat().st_size / 1e6:.1f} MB")
    print(f"total: {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
