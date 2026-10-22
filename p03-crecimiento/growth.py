"""P03: cómo crecieron las ciudades — tipología LEI, puntos calientes Gi* y capa del
Time Slider con años reales.

1. Landscape Expansion Index (Liu et al., 2010). Celda urbana = ≥15% de suelo
   construido (el mismo umbral de cities.py). Cada mancha nueva de un período se
   rodea con un anillo de 100 m y se mide qué parte del anillo ya era urbana:
   LEI ≥ 50 → relleno; 0 < LEI < 50 → expansión de borde; LEI = 0 → salto.
2. Getis-Ord Gi* sobre el cambio de m² construidos 1975→2020, en hexágonos H3 res 7
   de todo el territorio (incluidos los vacíos), celda + 6 vecinas, corrección FDR.
3. Capa H3 res 8 (~0,74 km²) con el año (1975-2020) en que cada hexágono superó el
   10% de suelo construido, para el Time Slider de GeoLibre (años reales).

Salidas en output/:
    p03_lei.json, hex_r7_crecimiento_gistar.parquet, hex_r8_urbanizacion.parquet,
    p03_crecimiento_stats.json
Ninguna de estas salidas se publica: solo usan el GHSL e incluyen épocas poco confiables
(1975-1990), y el Gi* de aquí usa la curva normal (ver PROCESO.md §3.6-3.7). Lo publicado
sale de wsf_layers.py, contrastado con WSF-Evolution.
Intermedio (fuera del repo): data/ghsl/ven/celdas.parquet

Uso:
    python -P growth.py
"""

import json
import math
from pathlib import Path

import duckdb
import numpy as np
import rasterio
from pyproj import Transformer
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
VEN = ROOT / "data" / "ghsl" / "ven"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
OUT = Path(__file__).resolve().parent / "output"
CELLS = VEN / "celdas.parquet"
EPOCHS = list(range(1975, 2021, 5))
PERIODOS = [(1975, 1990), (1990, 2000), (2000, 2015), (2015, 2020)]
URBANO = 1_500        # m² construidos por celda de 100 m (15%)
UMBRAL_HEX = 0.10     # fracción construida para considerar urbanizado un hexágono res 8


def read(name: str) -> np.ndarray:
    with rasterio.open(VEN / name) as src:
        return src.read(1)


def city_labels(built2020: np.ndarray, top: int = 10) -> tuple[np.ndarray, list[int]]:
    closed = ndimage.binary_closing(built2020 >= URBANO, structure=np.ones((7, 7), dtype=bool))
    lab, n = ndimage.label(closed)
    sizes = ndimage.sum(built2020, lab, index=np.arange(1, n + 1))
    return lab, list(np.argsort(sizes)[::-1][:top] + 1)


def lei(old: np.ndarray, new_urban: np.ndarray, city_lab: np.ndarray, cities: list[int]) -> dict:
    lab, n = ndimage.label(new_urban, structure=np.ones((3, 3), dtype=bool))
    if n == 0:
        return {}
    dil = ndimage.grey_dilation(lab, size=(3, 3))
    ring = (dil > 0) & (lab == 0)
    ring_lab = dil[ring]
    ring_n = np.bincount(ring_lab, minlength=n + 1)
    ring_old = np.bincount(ring_lab, weights=old[ring], minlength=n + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        idx = np.where(ring_n > 0, 100 * ring_old / ring_n, 0)
    tipo = np.where(idx >= 50, 0, np.where(idx > 0, 1, 2))  # 0 relleno, 1 borde, 2 salto
    area = np.bincount(lab.ravel(), minlength=n + 1)        # celdas de 1 ha
    names = ["relleno", "expansion_de_borde", "salto"]

    def resume(sel: np.ndarray) -> dict:
        tot = area[sel].sum()
        return {"km2_nuevos": round(tot / 100, 1), "manchas": int(sel.sum()),
                **{f"pct_{names[k]}": round(100 * area[sel & (tipo == k)].sum() / tot, 1) if tot else 0 for k in range(3)}}

    sel_all = np.arange(n + 1) > 0
    out = {"nacional": resume(sel_all)}
    # Ciudad de cada mancha = ciudad (de 2020) que contiene su primera celda.
    first = ndimage.find_objects(lab)
    patch_city = np.zeros(n + 1, dtype=np.int64)
    for i, sl in enumerate(first, start=1):
        if sl is None:
            continue
        sub = lab[sl] == i
        patch_city[i] = city_lab[sl][sub][0]
    for c in cities:
        out[f"ciudad_{c}"] = resume(sel_all & (patch_city == c))
    return out


def build_cell_table(transform, crs) -> None:
    """Celdas de 100 m con algo construido en alguna época → parquet con lat/lng y m² por época."""
    any_built = None
    for e in EPOCHS:
        b = read(f"built_{e}.tif") > 0
        any_built = b if any_built is None else (any_built | b)
    rows, cols = np.nonzero(any_built)
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    lng, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(np.array(xs), np.array(ys))
    data = {"lat": lat, "lng": lng}
    for e in EPOCHS:
        data[f"b{e}"] = read(f"built_{e}.tif")[rows, cols].astype("int32")
        data[f"p{e}"] = read(f"pop_{e}.tif")[rows, cols].astype("float32")
    con = duckdb.connect()
    con.register("celdas", data)
    con.execute(f"COPY celdas TO '{CELLS.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
    print(f"tabla de celdas: {len(rows):,} celdas con construcción en alguna época")


def gistar_and_hex(con) -> dict:
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    con.execute(f"CREATE TABLE c AS SELECT * FROM read_parquet('{CELLS.as_posix()}')")
    # --- Gi* del cambio 1975→2020 en H3 res 7, sobre todo el territorio ---
    con.execute(f"""
        CREATE TABLE terr AS
        WITH parts AS (SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}')),
        t AS (SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), 7)) AS cell FROM parts),
        ch AS (SELECT h3_latlng_to_cell(lat, lng, 7) AS cell, sum(b1975) AS b75, sum(b2020) AS b20,
                      sum(b2020 - b1975) AS delta FROM c GROUP BY cell)
        SELECT u.cell, coalesce(b75, 0) AS b75, coalesce(b20, 0) AS b20, coalesce(delta, 0) AS delta
        FROM (SELECT cell FROM t UNION SELECT cell FROM ch) u LEFT JOIN ch USING (cell)
    """)
    con.execute("""
        CREATE TABLE gi AS
        WITH nb AS (SELECT cell, unnest(h3_grid_disk(cell, 1)) AS nbr FROM terr)
        SELECT nb.cell, count(*) AS w, sum(t2.delta) AS lag FROM nb JOIN terr t2 ON t2.cell = nb.nbr GROUP BY nb.cell
    """)
    cells, delta, w, lag, b75, b20 = map(np.array, zip(*con.execute(
        "SELECT t.cell, t.delta, g.w, g.lag, t.b75, t.b20 FROM terr t JOIN gi g USING (cell)").fetchall()))
    x = delta.astype(float)
    N = len(x)
    xbar, s = x.mean(), x.std()
    w = w.astype(float)
    z = (lag - xbar * w) / (s * np.sqrt((N * w - w ** 2) / (N - 1)))
    p = np.vectorize(math.erfc)(np.abs(z) / math.sqrt(2))
    order, ranks = np.sort(p), np.arange(1, N + 1)
    cut = {a: (order[order <= ranks / N * a].max() if (order <= ranks / N * a).any() else 0.0) for a in (0.01, 0.05, 0.10)}
    clase = np.full(N, "No significativo", dtype=object)
    for a, conf in ((0.10, 90), (0.05, 95), (0.01, 99)):
        sig = p <= cut[a]
        clase[sig & (z > 0)] = f"Punto caliente {conf}%"
        clase[sig & (z < 0)] = f"Punto frío {conf}%"
    con.register("gi_np", {"cell": cells, "b1975_m2": b75, "b2020_m2": b20, "delta_m2": delta,
                           "z": np.round(z, 3), "p": p, "clase": clase.astype(str)})
    con.execute(f"""
        COPY (SELECT h3_h3_to_string(cell::UBIGINT) AS h3, b1975_m2, b2020_m2, delta_m2, z, p, clase,
                     ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell::UBIGINT)), 'OGC:CRS84') AS geometry
              FROM gi_np WHERE delta_m2 > 0 OR clase <> 'No significativo')
        TO '{(OUT / "hex_r7_crecimiento_gistar.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    area = np.array([a for (a,) in con.execute("SELECT h3_cell_area(cell::UBIGINT, 'km^2') FROM gi_np").fetchall()])
    hot99 = clase == "Punto caliente 99%"
    gi_res = {
        "celdas_territorio": N,
        "clases": {c: int((clase == c).sum()) for c in sorted(set(clase))},
        "pct_territorio_hot99": round(100 * float(area[hot99].sum() / area.sum()), 2),
        "pct_crecimiento_en_hot99": round(100 * float(x[hot99].sum() / x[x > 0].sum()), 1),
    }

    # --- Capa del Time Slider: año en que cada hexágono res 8 superó el 10% construido ---
    sums = ", ".join(f"sum(b{e}) AS b{e}" for e in EPOCHS)
    con.execute(f"CREATE TABLE h8 AS SELECT h3_latlng_to_cell(lat, lng, 8) AS cell, {sums} FROM c GROUP BY cell")
    first_year = " ".join(
        f"WHEN b{e} / (h3_cell_area(cell, 'm^2')) >= {UMBRAL_HEX} THEN {e}" for e in EPOCHS)
    con.execute(f"""
        COPY (
            SELECT h3_h3_to_string(cell) AS h3,
                   CASE {first_year} END AS anio,
                   round(b2020) AS construido_2020_m2,
                   round(100 * b2020 / h3_cell_area(cell, 'm^2'), 1) AS construido_2020_pct,
                   ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell)), 'OGC:CRS84') AS geometry
            FROM h8
            WHERE b2020 / h3_cell_area(cell, 'm^2') >= {UMBRAL_HEX}
        ) TO '{(OUT / "hex_r8_urbanizacion.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    years = dict(con.execute(f"""
        SELECT anio, count(*) FROM read_parquet('{(OUT / "hex_r8_urbanizacion.parquet").as_posix()}')
        GROUP BY anio ORDER BY anio
    """).fetchall())
    return {"gistar_cambio_1975_2020": gi_res, "hexagonos_r8_por_anio_de_urbanizacion": years}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(VEN / "built_2020.tif") as src:
        transform, crs = src.transform, src.crs
        built2020 = src.read(1)

    city_lab, cities = city_labels(built2020)
    # Mismo umbral, cierre y orden (por m² construidos en 2020) que cities.py: se asocian por orden.
    # (Por centroide fallaba en manchas irregulares, cuyo centroide cae fuera de la mancha.)
    ciudades = json.loads((OUT / "p03_ciudades.json").read_text(encoding="utf-8"))["umbral_15_cierre_300m"]["ciudades"]
    city_names = {int(lab_id): c["nombre"] for lab_id, c in zip(cities, ciudades)}
    del built2020

    lei_res = {}
    for a, b in PERIODOS:
        old = read(f"built_{a}.tif") >= URBANO
        new = (read(f"built_{b}.tif") >= URBANO) & ~old
        r = lei(old, new, city_lab, cities)
        lei_res[f"{a}-{b}"] = {("nacional" if k == "nacional" else city_names.get(int(k.split("_")[1]), k)): v
                               for k, v in r.items()}
        n = lei_res[f"{a}-{b}"]["nacional"]
        print(f"LEI {a}-{b}: {n['km2_nuevos']} km² nuevos · relleno {n['pct_relleno']}% · borde "
              f"{n['pct_expansion_de_borde']}% · salto {n['pct_salto']}%", flush=True)
        del old, new
    (OUT / "p03_lei.json").write_text(json.dumps(lei_res, indent=2, ensure_ascii=False), encoding="utf-8")

    if not CELLS.exists():
        build_cell_table(transform, crs)
    stats = gistar_and_hex(duckdb.connect())
    (OUT / "p03_crecimiento_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    for f in ("hex_r7_crecimiento_gistar.parquet", "hex_r8_urbanizacion.parquet"):
        print(f"{f}: {(OUT / f).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
