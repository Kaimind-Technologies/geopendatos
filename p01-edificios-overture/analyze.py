"""Paso 2 de P01: asigna cada edificio extraído a un estado de Venezuela
(geoBoundaries ADM1, sin Esequibo) y calcula las cifras del post. Todo local, sin red.

Edificio = centro de su bbox de Overture. Los que no caen en ningún estado
quedan fuera de Venezuela (vecinos dentro del recuadro de extracción).

Salidas en output/:
    p01_cifras.json            total, por estado, por fuente, por tipo
    ven_edificios.parquet      GeoParquet de Venezuela (para GeoLibre)
    caracas_edificios.parquet  solo Distrito Capital (capa liviana para el video)

Uso:
    python -P analyze.py
"""

import json
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "2026-09-23.1"
RAW = ROOT / "data" / "overture" / f"ven_buildings_bbox_{RELEASE}.parquet"
ADM1 = ROOT / "data" / "boundaries" / "gb-VEN-ADM1.geojson"
OUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    t0 = time.perf_counter()
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; SET enable_progress_bar=false;")

    # GeoJSON de geoBoundaries ya está en lon/lat; solo se iguala la etiqueta de CRS con la de Overture.
    con.execute(
        f"CREATE TABLE adm1 AS SELECT shapeName AS estado, ST_SetCRS(geom, 'OGC:CRS84') AS geom "
        f"FROM ST_Read('{ADM1.as_posix()}')"
    )
    con.execute(f"""
        CREATE TABLE pts AS
        SELECT id,
               ST_SetCRS(ST_Point((bbox.xmin + bbox.xmax) / 2, (bbox.ymin + bbox.ymax) / 2), 'OGC:CRS84') AS p
        FROM read_parquet('{RAW.as_posix()}')
    """)
    # Un punto sobre un límite compartido puede tocar dos estados: se queda con uno solo.
    con.execute("""
        CREATE TABLE asignacion AS
        SELECT pts.id, min(adm1.estado) AS estado
        FROM pts JOIN adm1 ON ST_Intersects(adm1.geom, pts.p)
        GROUP BY pts.id
    """)
    con.execute(f"""
        CREATE TABLE ven AS
        SELECT r.*, a.estado
        FROM read_parquet('{RAW.as_posix()}') r JOIN asignacion a USING (id)
    """)
    t_join = time.perf_counter() - t0

    total = con.execute("SELECT count(*) FROM ven").fetchone()[0]
    fuera = con.execute("SELECT count(*) FROM pts").fetchone()[0] - total

    por_estado = con.execute(
        "SELECT estado, count(*) AS n FROM ven GROUP BY estado ORDER BY n DESC"
    ).fetchall()
    por_fuente = con.execute(
        "SELECT sources[1].dataset AS fuente, count(*) AS n FROM ven GROUP BY fuente ORDER BY n DESC"
    ).fetchall()
    por_tipo = con.execute(
        "SELECT coalesce(subtype, 'sin dato') AS tipo, count(*) AS n FROM ven GROUP BY tipo ORDER BY n DESC"
    ).fetchall()
    con_pisos = con.execute("SELECT count(*) FROM ven WHERE num_floors IS NOT NULL").fetchone()[0]

    cifras = {
        "release_overture": RELEASE,
        "poligono": "geoBoundaries gbOpen VEN ADM1 (OCHA Venezuela / INE), CC BY 3.0 IGO, sin Esequibo",
        "criterio": "edificio asignado por el centro de su bbox",
        "total_edificios": total,
        "descartados_fuera_de_venezuela": fuera,
        "suma_por_estados": sum(n for _, n in por_estado),
        "por_estado": [{"estado": e, "edificios": n} for e, n in por_estado],
        "por_fuente": [{"fuente": f, "edificios": n, "pct": round(100 * n / total, 1)} for f, n in por_fuente],
        "por_tipo": [{"tipo": t, "edificios": n, "pct": round(100 * n / total, 1)} for t, n in por_tipo],
        "con_dato_de_pisos": con_pisos,
        "segundos_asignacion": round(t_join, 1),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "p01_cifras.json").write_text(json.dumps(cifras, indent=2, ensure_ascii=False), encoding="utf-8")

    con.execute(f"""
        COPY (SELECT id, estado, sources[1].dataset AS fuente, subtype, class, num_floors, height, geometry FROM ven)
        TO '{(OUT_DIR / "ven_edificios.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    con.execute(f"""
        COPY (SELECT id, sources[1].dataset AS fuente, subtype, num_floors, height, geometry
              FROM ven WHERE estado = 'Distrito Capital')
        TO '{(OUT_DIR / "caracas_edificios.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)

    print(json.dumps({k: v for k, v in cifras.items() if k != "por_estado"}, indent=2, ensure_ascii=False))
    print("Top 5 estados:", json.dumps(cifras["por_estado"][:5], ensure_ascii=False))
    print("Segundos totales:", round(time.perf_counter() - t0, 1))


if __name__ == "__main__":
    main()
