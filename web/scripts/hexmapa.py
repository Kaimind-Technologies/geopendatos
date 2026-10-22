"""Genera el mapa de hexágonos de la portada (web/src/datos/hexmapa.json).

Venezuela en celdas H3 de resolución 4 (~1.770 km²), con las construcciones de P01
sumadas por celda. Se incluyen las celdas sin ninguna construcción para que se vea
el país completo. El contorno de cada celda sale ya proyectado a coordenadas SVG,
así la página no calcula nada en el navegador.

Las celdas con construcciones se reparten en 5 clases por quintiles: con datos tan
concentrados, una escala lineal dejaría casi todo el país del mismo color.

Uso (desde la raíz del repo, después de common/boundaries.py y P01):
    python -P web/scripts/hexmapa.py
"""

import json
import math
import re
import statistics
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[2]
PAIS = RAIZ / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
H3_R7 = RAIZ / "p01-edificios-overture" / "output" / "ven_h3_r7.parquet"
# No "data/": el .gitignore raíz ignora todas las carpetas con ese nombre
SALIDA = RAIZ / "web" / "src" / "datos" / "hexmapa.json"

RES = 4
ANCHO = 1000  # ancho del viewBox del SVG
CLASES = 5


def celdas():
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    # Territorio: celdas con el centro dentro del país. Se les suman las que tienen
    # construcciones aunque su centro caiga en el mar (costa, islas).
    return con.execute(f"""
        WITH partes AS (
            SELECT unnest(ST_Dump(geom)).geom AS g FROM ST_Read('{PAIS}')
        ),
        territorio AS (
            SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(g), {RES})) AS celda FROM partes
        ),
        conteo AS (
            SELECT h3_cell_to_parent(h3_string_to_h3(h3), {RES}) AS celda, sum(edificios) AS n
            FROM '{H3_R7}' GROUP BY 1
        )
        SELECT coalesce(n, 0)::BIGINT AS n, h3_cell_area(celda, 'km^2') AS km2,
               h3_cell_to_boundary_wkt(celda) AS wkt
        FROM territorio FULL JOIN conteo USING (celda)
        ORDER BY celda  -- salida estable: re-correr sin cambios no ensucia el diff
    """).fetchall()


def anillo(wkt):
    """'POLYGON ((lng lat, ...))' -> [(lng, lat), ...] sin repetir el primer punto."""
    pares = re.findall(r"(-?\d+\.?\d*) (-?\d+\.?\d*)", wkt)
    puntos = [(float(x), float(y)) for x, y in pares]
    return puntos[:-1] if puntos[0] == puntos[-1] else puntos


def main():
    filas = celdas()
    anillos = [anillo(wkt) for _, _, wkt in filas]

    # Equirectangular corregida por la latitud media: a estas latitudes (1-12° N)
    # la deformación es mínima y los hexágonos se ven regulares.
    lngs = [x for a in anillos for x, _ in a]
    lats = [y for a in anillos for _, y in a]
    k = math.cos(math.radians((min(lats) + max(lats)) / 2))
    escala = ANCHO / ((max(lngs) - min(lngs)) * k)
    alto = round((max(lats) - min(lats)) * escala)

    def path(a):
        pts = [f"{(x - min(lngs)) * k * escala:.1f} {(max(lats) - y) * escala:.1f}" for x, y in a]
        return "M" + "L".join(pts) + "Z"

    con_datos = sorted(n for n, _, _ in filas if n > 0)
    cortes = [round(c) for c in statistics.quantiles(con_datos, n=CLASES)]

    def clase(n):
        return 0 if n == 0 else 1 + sum(n > c for c in cortes)

    total = sum(con_datos)
    salida = {
        "fuente": "Overture Maps (buildings, P01) · geoBoundaries gbOpen VEN ADM0 (sin Guayana Esequiba)",
        "resolucion_h3": RES,
        "km2_celda": round(statistics.mean(km2 for _, km2, _ in filas)),
        "viewBox": f"0 0 {ANCHO} {alto}",
        "cortes": cortes,
        "total_construcciones": total,
        "celdas": [[clase(n), n, path(a)] for (n, _, _), a in zip(filas, anillos)],
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(filas)} celdas ({len(filas) - len(con_datos)} vacías), {total:,} construcciones, "
          f"cortes {cortes} -> {SALIDA.relative_to(RAIZ)} ({SALIDA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
