"""P02: ¿cuánto depende la densidad de quién dibujó los techos?

Overture junta techos de tres fuentes que los dibujan distinto: los voluntarios de
OpenStreetMap los trazan casa por casa, y la IA (Google, Microsoft) puede unir techos pegados
o partirlos. En las zonas más densas eso cambia el conteo, así que el "lugar más denso" puede
reflejar la fuente tanto como el barrio.

1. Distrito Capital (local, con output/caracas_edificios.parquet de P01): en celdas H3 res 9
   (~0,1 km²) compactas (≥35% del suelo techado), techos por celda según la fuente dominante.
2. Las 10 celdas res 7 (~5 km²) con más construcciones del país: mezcla de fuentes y techo
   mediano, leyendo de Overture (S3) solo el recuadro de cada celda (unos minutos).
3. Prueba del titular: % del territorio que concentra la mitad de las construcciones si las
   celdas densas tuvieran 1,5 o 2 veces más techos de los reales.

Salida: output/p02_fuentes.json

Uso (después de layers.py):
    python -P fuentes.py
"""

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "output"
CARACAS = ROOT / "p01-edificios-overture" / "output" / "caracas_edificios.parquet"
RANKING = OUT / "hex_r7_ranking.parquet"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
SOURCE = "s3://overturemaps-us-west-2/release/2026-09-23.1/theme=buildings/type=building/*.parquet"
COMPACTA = 0.35        # fracción mínima de suelo techado para comparar celdas parecidas
TOP_R7 = 10
DENSA = 2000           # construcciones por celda res 7 (~400/km²) para la prueba del titular
FACTORES = (1.0, 1.5, 2.0)


def caracas(con) -> dict:
    con.execute(f"""
        CREATE TABLE dc AS
        SELECT fuente, ST_Area(ST_Transform(geometry, 'EPSG:6933')) AS area_m2,
               h3_latlng_to_cell(ST_Y(ST_Centroid(geometry)), ST_X(ST_Centroid(geometry)), 9) AS r9
        FROM read_parquet('{CARACAS.as_posix()}')
    """)
    con.execute("""
        CREATE TABLE dc9 AS
        SELECT r9, count(*) AS n, avg((fuente = 'OpenStreetMap')::INT) AS osm,
               sum(area_m2) / h3_cell_area(r9, 'm^2') AS cobertura, median(area_m2) AS techo_mediana
        FROM dc GROUP BY r9
    """)
    dominante = """CASE WHEN osm >= 0.8 THEN 'OpenStreetMap' WHEN osm <= 0.2 THEN 'IA (Google o Microsoft)'
                        ELSE 'mixta' END"""
    grupos = con.execute(f"""
        SELECT {dominante} AS fuente, count(*), round(avg(n)), round(100 * avg(cobertura), 1), round(median(techo_mediana))
        FROM dc9 WHERE cobertura >= {COMPACTA} GROUP BY 1 ORDER BY 1
    """).fetchall()
    pct_osm = lambda where: con.execute(f"SELECT round(100 * avg((osm >= 0.8)::INT), 1) FROM ({where})").fetchone()[0]
    top = con.execute("""
        SELECT h3_h3_to_string(r9), n, round(100 * osm, 1), round(h3_cell_to_lat(r9), 5), round(h3_cell_to_lng(r9), 5)
        FROM dc9 ORDER BY n DESC LIMIT 10
    """).fetchall()
    return {
        "fuentes": [{"fuente": f, "construcciones": n, "pct": p} for f, n, p in con.execute(
            "SELECT fuente, count(*), round(100 * count(*) / sum(count(*)) OVER (), 1) FROM dc GROUP BY 1 ORDER BY 2 DESC"
        ).fetchall()],
        "celdas_compactas_por_fuente_dominante": [
            {"fuente_dominante": f, "celdas": c, "techos_por_celda": n, "cobertura_pct": cob, "techo_mediana_m2": m}
            for f, c, n, cob, m in grupos],
        "pct_celdas_dominadas_por_osm": {
            "entre_las_compactas": pct_osm(f"SELECT * FROM dc9 WHERE cobertura >= {COMPACTA}"),
            "entre_las_50_con_mas_techos": pct_osm("SELECT * FROM dc9 ORDER BY n DESC LIMIT 50"),
        },
        "top10_r9": [{"h3": h, "construcciones": n, "pct_osm": o, "lat": la, "lng": lo} for h, n, o, la, lo in top],
    }


def top_r7(con) -> list[dict]:
    con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2'; SET parquet_metadata_cache=true;")
    cells = con.execute(f"""
        SELECT h3, construcciones, ST_XMin(g), ST_YMin(g), ST_XMax(g), ST_YMax(g)
        FROM (SELECT h3, construcciones, ST_GeomFromText(h3_cell_to_boundary_wkt(h3_string_to_h3(h3))) AS g
              FROM read_parquet('{RANKING.as_posix()}') WHERE ranking <= {TOP_R7}) ORDER BY construcciones DESC
    """).fetchall()
    result = []
    for h3, n, xmin, ymin, xmax, ymax in cells:
        rows = con.execute(f"""
            WITH b AS (
                SELECT sources[1].dataset AS fuente, ST_Area(ST_Transform(geometry, 'EPSG:6933')) AS area_m2,
                       h3_latlng_to_cell(ST_Y(ST_Centroid(geometry)), ST_X(ST_Centroid(geometry)), 7) AS r7
                FROM read_parquet('{SOURCE}')
                WHERE bbox.xmin <= {xmax} AND bbox.xmax >= {xmin} AND bbox.ymin <= {ymax} AND bbox.ymax >= {ymin}
            )
            SELECT fuente, count(*), round(median(area_m2)) FROM b WHERE h3_h3_to_string(r7) = '{h3}' GROUP BY 1 ORDER BY 2 DESC
        """).fetchall()
        total = sum(c for _, c, _ in rows)
        lat, lng = con.execute(f"SELECT h3_cell_to_lat(h3_string_to_h3('{h3}')), h3_cell_to_lng(h3_string_to_h3('{h3}'))").fetchone()
        result.append({"h3": h3, "construcciones": n, "coincide_con_p02": total == n,
                       "lat": round(lat, 4), "lng": round(lng, 4),
                       "fuentes": [{"fuente": f, "pct": round(100 * c / total, 1), "techo_mediana_m2": m} for f, c, m in rows]})
        print(f"  {h3} {n:>6,}: " + " · ".join(f"{f} {round(100 * c / total)}% ({m:.0f} m²)" for f, c, m in rows))
    return result


def sobreconteo(con) -> list[dict]:
    terr_km2 = con.execute(f"""
        WITH parts AS (SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}')),
        terr AS (SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), 7)) AS cell FROM parts),
        occ AS (SELECT h3_string_to_h3(h3) AS cell FROM read_parquet('{RANKING.as_posix()}'))
        SELECT sum(h3_cell_area(cell, 'km^2')) FROM (SELECT cell FROM terr UNION SELECT cell FROM occ)
    """).fetchone()[0]
    result = []
    for f in FACTORES:
        km2 = con.execute(f"""
            WITH h AS (SELECT CASE WHEN construcciones >= {DENSA} THEN construcciones / {f} ELSE construcciones END AS n,
                              h3_cell_area(h3_string_to_h3(h3), 'km^2') AS km2
                       FROM read_parquet('{RANKING.as_posix()}')),
            c AS (SELECT sum(n) OVER w AS acum, sum(km2) OVER w AS acum_km2, sum(n) OVER () AS total
                  FROM h WINDOW w AS (ORDER BY n DESC ROWS UNBOUNDED PRECEDING))
            SELECT min(acum_km2) FROM c WHERE acum >= 0.5 * total
        """).fetchone()[0]
        result.append({"factor_sobreconteo": f, "mitad_en_pct_territorio": round(100 * km2 / terr_km2, 2)})
    return result


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    result = {"caracas": caracas(con)}
    print(json.dumps(result["caracas"]["celdas_compactas_por_fuente_dominante"], ensure_ascii=False))
    print(result["caracas"]["pct_celdas_dominadas_por_osm"])
    result["sobreconteo_celdas_densas"] = sobreconteo(con)
    print(result["sobreconteo_celdas_densas"])
    print(f"top {TOP_R7} celdas res 7 (Overture S3):")
    result["top_r7"] = top_r7(con)
    (OUT / "p02_fuentes.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
