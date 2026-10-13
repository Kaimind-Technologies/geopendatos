"""P02: capa para el Time Slider de GeoLibre.

Cada hexágono H3 res 7 (~5 km²) lleva `pct_acumulado`: qué % de las construcciones
del país suman los hexágonos tan o más densos que él. Al filtrar con el Time Slider
por ese campo (0 → 100), Venezuela se "enciende" de lo más denso a lo más vacío: al
50% solo brilla el 0,5% del territorio.

Salida:
    output/hex_r7_ranking.parquet

Uso:
    python -P layers.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "ven_construcciones_metricas.parquet"
OUT = Path(__file__).resolve().parent / "output" / "hex_r7_ranking.parquet"


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    con.execute(f"""
        CREATE TABLE h AS
        SELECT h3_latlng_to_cell(lat, lng, 7) AS cell, count(*) AS construcciones
        FROM read_parquet('{DERIVED.as_posix()}') GROUP BY cell
    """)
    total = con.execute("SELECT sum(construcciones) FROM h").fetchone()[0]
    con.execute(f"""
        COPY (
            SELECT h3_h3_to_string(cell) AS h3, construcciones,
                   row_number() OVER w AS ranking,
                   round(100.0 * sum(construcciones) OVER (w ROWS UNBOUNDED PRECEDING) / {total}, 2) AS pct_acumulado,
                   -- El Time Slider de GeoLibre solo acepta fechas o años (1000-9999): el % se codifica
                   -- como año, 1900 + techo(%), para animarlo con la opción acumulativa.
                   (1900 + ceil(100.0 * sum(construcciones) OVER (w ROWS UNBOUNDED PRECEDING) / {total}))::INTEGER AS anio,
                   ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell)), 'OGC:CRS84') AS geometry
            FROM h
            WINDOW w AS (ORDER BY construcciones DESC, cell)
        ) TO '{OUT.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    check = con.execute(f"""
        SELECT count(*) FILTER (WHERE pct_acumulado <= 50), count(*), max(pct_acumulado)
        FROM read_parquet('{OUT.as_posix()}')
    """).fetchone()
    print(f"hexágonos que suman el 50%: {check[0]:,} de {check[1]:,} | máximo pct_acumulado: {check[2]}")
    print(f"{OUT.name}: {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
