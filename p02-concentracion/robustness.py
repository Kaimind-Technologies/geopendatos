"""P02: tests de robustez de los dos datos del titular.

  A. "La mitad de las construcciones está en el 0,5% del territorio"
  B. "El 54% del territorio no tiene ninguna construcción"

Se recalculan por superficie real (h3_cell_area), con:
  1. tres resoluciones H3 (6 ≈ 36 km², 7 ≈ 5 km², 8 ≈ 0,74 km²),
  2. un filtro de calidad (sin techos < 20 m², posibles anexos o falsos positivos de la IA),
  3. el área oficial (916.445 km²) como contraste del denominador.

Salida: output/p02_robustez.json

Uso:
    python -P robustness.py
"""

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "ven_construcciones_metricas.parquet"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
OUT = Path(__file__).resolve().parent / "output" / "p02_robustez.json"
VEN_KM2 = 916_445


def run(con, res: int, min_area: float) -> dict:
    con.execute(f"""
        CREATE OR REPLACE TABLE t AS
        WITH parts AS (SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}')),
        terr AS (SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), {res})) AS cell FROM parts),
        counts AS (
            SELECT h3_latlng_to_cell(lat, lng, {res}) AS cell, count(*) AS n
            FROM read_parquet('{DERIVED.as_posix()}') WHERE area_m2 >= {min_area} GROUP BY cell
        )
        SELECT c.cell, coalesce(n, 0) AS n, h3_cell_area(c.cell, 'km^2') AS km2
        FROM (SELECT cell FROM terr UNION SELECT cell FROM counts) c LEFT JOIN counts USING (cell)
    """)
    total, terr_km2 = con.execute("SELECT sum(n), sum(km2) FROM t").fetchone()
    vacio_km2 = con.execute("SELECT sum(km2) FROM t WHERE n = 0").fetchone()[0]
    con.execute("""
        CREATE OR REPLACE TABLE c AS
        SELECT n, km2, sum(n) OVER w AS acum, sum(km2) OVER w AS acum_km2
        FROM t WHERE n > 0 WINDOW w AS (ORDER BY n DESC ROWS UNBOUNDED PRECEDING)
    """)

    def km2_for(p: float) -> float:
        return con.execute(f"SELECT min(acum_km2) FROM c WHERE acum >= {p} * {total}").fetchone()[0]

    k50, k90 = km2_for(0.5), km2_for(0.9)
    return {
        "resolucion_h3": res,
        "filtro_area_min_m2": min_area,
        "construcciones": int(total),
        "km2_territorio_celdas": round(terr_km2),
        "A_mitad_en_km2": round(k50),
        "A_mitad_pct_territorio": round(100 * k50 / terr_km2, 2),
        "A_mitad_pct_area_oficial": round(100 * k50 / VEN_KM2, 2),
        "90pct_en_pct_territorio": round(100 * k90 / terr_km2, 2),
        "B_vacio_pct_territorio": round(100 * vacio_km2 / terr_km2, 1),
    }


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    results = [run(con, res, 0) for res in (6, 7, 8)] + [run(con, 7, 20)]
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{'escenario':28}{'mitad en % terr.':>18}{'(% área oficial)':>18}{'90% en % terr.':>16}{'vacío % terr.':>15}")
    for r in results:
        name = f"H3 res {r['resolucion_h3']}" + (f", sin techos <{r['filtro_area_min_m2']:.0f} m²" if r["filtro_area_min_m2"] else "")
        print(f"{name:28}{r['A_mitad_pct_territorio']:>18}{r['A_mitad_pct_area_oficial']:>18}"
              f"{r['90pct_en_pct_territorio']:>16}{r['B_vacio_pct_territorio']:>15}")
    print("construcciones con filtro <20 m²:", results[-1]["construcciones"])


if __name__ == "__main__":
    main()
