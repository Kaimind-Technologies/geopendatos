"""P03 · Capas y contrastes con WSF-Evolution (la fuente que pasó las verificaciones).

1. Píxeles de asentamiento (~30 m) dentro de Venezuela → tabla con lat/lng, año de
   primera detección (1985-2015) y área real del píxel (data/wsf_evo/pixeles.parquet).
2. Capa del Time Slider: hexágonos H3 res 8 (~0,74 km²) con el AÑO REAL (anual,
   1985-2015) en que su área de asentamiento superó el 10% del hexágono.
   1985 significa "ya era asentamiento en 1985 o antes".
3. Tipología LEI 2000-2015 con WSF, sobre la misma grilla de 100 m del GHSL
   (cada celda toma el primer año en que alguno de sus píxeles WSF fue asentamiento),
   para compararla con la LEI 2000-2015 del GHSL.
4. Dónde cayó el crecimiento 2000-2015, con WSF y con GHSL:
   a. Concentración: qué % del territorio concentra el 50/70/90% del crecimiento, con hexágonos
      H3 res 6, 7 y 8 (~36, ~5 y ~0,74 km²). Es lo que se publica.
   b. Capa con las celdas res 7 que suman la mitad del crecimiento WSF, marcando si también
      están entre las que suman la mitad del crecimiento GHSL (contornos del video).
   c. Puntos calientes Gi* (H3 res 7, FDR) con p-valores por Monte Carlo y, para el registro,
      con la curva normal de la versión anterior. No resiste como hallazgo: ver PROCESO.md §3.6.

Salidas: output/hex_r8_urbanizacion_wsf.parquet, output/hex_r7_mitad_crecimiento.parquet,
         output/p03_contraste_lei_gistar.json

Uso:
    python -P wsf_layers.py
"""

import json
import math
from pathlib import Path

import duckdb
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import Resampling, reproject
from scipy import ndimage
from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parents[1]
WSF = ROOT / "data" / "wsf_evo"
VEN = ROOT / "data" / "ghsl" / "ven"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
OUT = Path(__file__).resolve().parent / "output"
PIX = WSF / "pixeles.parquet"
FIRST100 = WSF / "wsf_primer_anio_100m.tif"
R = 6_371_008.8
URBANO_GHSL = 1_500
N_SIMS, CHUNK, SEED = 5_000_000, 500_000, 2026  # Monte Carlo del Gi* (como P02)
CORTES = (0.5, 0.7, 0.9)                         # curva de concentración del crecimiento


def row_areas(src) -> np.ndarray:
    t = src.transform
    lat_top = t.f + np.arange(src.height) * t.e
    return R ** 2 * math.radians(abs(t.a)) * np.abs(np.sin(np.radians(lat_top)) - np.sin(np.radians(lat_top + t.e)))


def build_pixels_and_grid() -> None:
    ven = shape(json.loads(ADM0.read_text(encoding="utf-8"))["features"][0]["geometry"])
    with rasterio.open(VEN / "mask_estados.tif") as g:
        grid_t, grid_crs, gh, gw = g.transform, g.crs, g.height, g.width
        inside_ven = g.read(1) > 0
    first = np.zeros((gh, gw), dtype="int16")
    con = duckdb.connect()
    con.execute("CREATE TABLE px (lat DOUBLE, lng DOUBLE, anio SMALLINT, area_m2 DOUBLE)")
    for f in sorted(WSF.glob("WSFevolution_v1_*.tif")):
        with rasterio.open(f) as src:
            if not ven.intersects(box(*src.bounds)):
                continue
            a = src.read(1)
            mask = rasterize([(mapping(ven), 1)], out_shape=a.shape, transform=src.transform, dtype="uint8") == 1
            sel = mask & (a >= 1985)
            rows, cols = np.nonzero(sel)
            if len(rows):
                xs, ys = rasterio.transform.xy(src.transform, rows, cols)
                df = {"lat": np.asarray(ys), "lng": np.asarray(xs), "anio": a[rows, cols].astype("int16"),
                      "area_m2": row_areas(src)[rows]}
                con.register("chunk", df)
                con.execute("INSERT INTO px SELECT lat, lng, anio, area_m2 FROM chunk")
                con.unregister("chunk")
            # Mismo año mínimo sobre la grilla de 100 m del GHSL (0 = sin asentamiento).
            yrs = np.where(sel, a, 32767).astype("int16")
            dst = np.full((gh, gw), 32767, dtype="int16")
            reproject(yrs, dst, src_transform=src.transform, src_crs=src.crs, dst_transform=grid_t,
                      dst_crs=grid_crs, resampling=Resampling.min, src_nodata=32767, dst_nodata=32767)
            upd = (dst != 32767) & ((first == 0) | (dst < first))
            first[upd] = dst[upd]
        print("  ", f.name, flush=True)
    first[~inside_ven] = 0
    with rasterio.open(FIRST100, "w", driver="GTiff", width=gw, height=gh, count=1, dtype="int16", crs=grid_crs,
                       transform=grid_t, nodata=0, compress="deflate", tiled=True) as dst:
        dst.write(first, 1)
    con.execute(f"COPY px TO '{PIX.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
    n, km2 = con.execute("SELECT count(*), sum(area_m2)/1e6 FROM px").fetchone()
    print(f"píxeles de asentamiento: {n:,} · {km2:,.1f} km² (debe coincidir con verify_wsf.py: 4.457,6)")


def lei(old: np.ndarray, new: np.ndarray) -> dict:
    lab, n = ndimage.label(new, structure=np.ones((3, 3), dtype=bool))
    dil = ndimage.grey_dilation(lab, size=(3, 3))
    ring = (dil > 0) & (lab == 0)
    rl = dil[ring]
    ring_n = np.bincount(rl, minlength=n + 1)
    ring_old = np.bincount(rl, weights=old[ring], minlength=n + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        idx = np.where(ring_n > 0, 100 * ring_old / ring_n, 0)
    tipo = np.where(idx >= 50, 0, np.where(idx > 0, 1, 2))
    area = np.bincount(lab.ravel(), minlength=n + 1)
    area[0] = 0
    tot = area.sum()
    return {"km2_nuevos": round(tot / 100, 1),
            "pct_relleno": round(100 * area[tipo == 0].sum() / tot, 1),
            "pct_expansion_de_borde": round(100 * area[tipo == 1].sum() / tot, 1),
            "pct_salto": round(100 * area[tipo == 2].sum() / tot, 1)}


def bh_cut(p: np.ndarray, alpha: float) -> float:
    """Benjamini-Hochberg: umbral de p que controla la tasa de falsos descubrimientos."""
    order, ranks = np.sort(p), np.arange(1, len(p) + 1)
    ok = order <= ranks / len(p) * alpha
    return float(order[ok].max()) if ok.any() else 0.0


def gistar(x: np.ndarray, w: np.ndarray, lag: np.ndarray, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Gi* con dos p-valores: el de la curva normal (versión anterior, descartada) y el de Monte Carlo.

    Mismo método que p02-concentracion/gistar.py: la hipótesis nula reparte los valores de las
    celdas al azar en el territorio (con reposición) y compara cada suma vecinal con N_SIMS
    sumas de w celdas tomadas al azar. Con 94% de celdas sin crecimiento, la normal exagera
    la significancia.
    """
    N = len(x)
    z = (lag - x.mean() * w) / (x.std() * np.sqrt((N * w - w ** 2) / (N - 1)))
    p_normal = np.vectorize(math.erfc)(np.abs(z) / math.sqrt(2))
    wi = w.astype(int)
    sums = np.empty((wi.max(), N_SIMS))
    for start in range(0, N_SIMS, CHUNK):
        m = min(CHUNK, N_SIMS - start)
        sums[:, start:start + m] = x[rng.integers(0, N, size=(m, wi.max()))].cumsum(axis=1).T
    sums.sort(axis=1)
    p_mc = np.ones(N)
    for wv in np.unique(wi):
        msk = wi == wv
        ge = N_SIMS - np.searchsorted(sums[wv - 1], lag[msk], side="left")
        le = np.searchsorted(sums[wv - 1], lag[msk], side="right")
        p_mc[msk] = np.minimum(1.0, 2 * (1 + np.minimum(ge, le)) / (N_SIMS + 1))
    return {"z": z, "p_normal": p_normal, "p_mc": p_mc}


def hot(g: dict[str, np.ndarray], p_key: str, alpha: float) -> np.ndarray:
    return (g[p_key] <= bh_cut(g[p_key], alpha)) & (g["z"] > 0)


def territory_cells_sql(res: int) -> str:
    return f"""WITH parts AS (SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}'))
               SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), {res})) AS cell FROM parts"""


def territory_km2(con, res: int) -> float:
    """Área real de las celdas H3 del territorio (denominador de todos los % del territorio)."""
    return con.execute(f"SELECT sum(h3_cell_area(cell, 'km^2')) FROM ({territory_cells_sql(res)})").fetchone()[0]


def count_cells(con, res: int) -> int:
    return con.execute(f"SELECT count(*) FROM ({territory_cells_sql(res)})").fetchone()[0]


def growth_cells(con, res: int) -> dict[str, np.ndarray]:
    """Crecimiento 2000-2015 por celda (m²): WSF (asentamiento nuevo) y GHSL (construido 2015 - 2000).

    Incluye todas las celdas del territorio (con 0) y las de borde que tienen crecimiento.
    Ordenado por celda para que el Monte Carlo sea reproducible con la misma semilla.
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE g{res} AS
        WITH t AS ({territory_cells_sql(res)}),
        w AS (SELECT h3_latlng_to_cell(lat, lng, {res}) AS cell, sum(area_m2) AS wsf
              FROM read_parquet('{PIX.as_posix()}') WHERE anio > 2000 AND anio <= 2015 GROUP BY cell),
        g AS (SELECT h3_latlng_to_cell(lat, lng, {res}) AS cell, sum(b2015 - b2000) AS ghsl
              FROM read_parquet('{(VEN / "celdas.parquet").as_posix()}') GROUP BY cell)
        SELECT u.cell, coalesce(w.wsf, 0) AS wsf, coalesce(g.ghsl, 0) AS ghsl, h3_cell_area(u.cell, 'km^2') AS km2
        FROM (SELECT cell FROM t UNION SELECT cell FROM w UNION SELECT cell FROM g) u
        LEFT JOIN w USING (cell) LEFT JOIN g USING (cell)
        ORDER BY u.cell
    """)
    d = con.execute(f"SELECT cell, wsf, ghsl, km2 FROM g{res} ORDER BY cell").fetchnumpy()
    return {k: (v if k == "cell" else v.astype(float)) for k, v in d.items()}


def top_cells(x: np.ndarray, share: float) -> np.ndarray:
    """Máscara de las celdas de mayor crecimiento que, juntas, suman `share` del crecimiento total."""
    xp = np.maximum(x, 0)
    order = np.argsort(-xp, kind="stable")
    k = int(np.searchsorted(np.cumsum(xp[order]) / xp.sum(), share)) + 1
    mask = np.zeros(len(x), dtype=bool)
    mask[order[:k]] = True
    return mask


def concentration(x: np.ndarray, km2: np.ndarray, km2_terr: float) -> dict:
    out = {}
    for share in CORTES:
        m = top_cells(x, share)
        out[f"{int(share * 100)}pct_del_crecimiento"] = {
            "celdas": int(m.sum()), "km2": round(float(km2[m].sum()), 1),
            "pct_territorio": round(100 * float(km2[m].sum()) / km2_terr, 2)}
    return out


def main() -> None:
    if not (PIX.exists() and FIRST100.exists()):
        build_pixels_and_grid()
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    total = con.execute(f"SELECT sum(area_m2)/1e6 FROM read_parquet('{PIX.as_posix()}')").fetchone()[0]
    print(f"verificación de la tabla de píxeles: {total:,.1f} km² (esperado 4.389,4 con el contorno ADM0)")

    # --- 2. Capa del Time Slider con años reales ---
    con.execute(f"""
        CREATE TABLE h8 AS
        SELECT h3_latlng_to_cell(lat, lng, 8) AS cell, anio, sum(area_m2) AS m2
        FROM read_parquet('{PIX.as_posix()}') GROUP BY cell, anio
    """)
    con.execute("""
        CREATE TABLE h8c AS
        SELECT cell, anio, sum(m2) OVER (PARTITION BY cell ORDER BY anio) AS acum,
               h3_cell_area(cell, 'm^2') AS celda_m2
        FROM h8
    """)
    con.execute(f"""
        COPY (
            SELECT h3_h3_to_string(cell) AS h3, min(anio) FILTER (WHERE acum / celda_m2 >= 0.10) AS anio,
                   round(100 * max(acum) / any_value(celda_m2), 1) AS asentamiento_2015_pct,
                   ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell)), 'OGC:CRS84') AS geometry
            FROM h8c GROUP BY cell
            HAVING max(acum) / any_value(celda_m2) >= 0.10
        ) TO '{(OUT / "hex_r8_urbanizacion_wsf.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    por_anio = dict(con.execute(f"""SELECT anio, count(*) FROM read_parquet('{(OUT / "hex_r8_urbanizacion_wsf.parquet").as_posix()}')
                                  GROUP BY anio ORDER BY anio""").fetchall())
    print("hexágonos res 8 por año de urbanización (WSF):", por_anio)

    # --- 3. LEI 2000-2015: WSF vs GHSL, en la misma grilla de 100 m ---
    with rasterio.open(FIRST100) as src:
        first = src.read(1)
    lei_wsf = {"1990-2000": lei((first > 0) & (first <= 1990), (first > 1990) & (first <= 2000)),
               "2000-2015": lei((first > 0) & (first <= 2000), (first > 2000) & (first <= 2015))}
    del first
    with rasterio.open(VEN / "built_2000.tif") as s0, rasterio.open(VEN / "built_2015.tif") as s1:
        o, n = s0.read(1) >= URBANO_GHSL, s1.read(1) >= URBANO_GHSL
    lei_ghsl = {"2000-2015": lei(o, n & ~o)}
    del o, n
    print("LEI 2000-2015 · WSF:", lei_wsf["2000-2015"], "· GHSL:", lei_ghsl["2000-2015"])

    # --- 4. Dónde cayó el crecimiento 2000-2015 ---
    # 4a. Concentración (publicable): qué % del territorio concentra el 50/70/90% del crecimiento,
    #     con las dos fuentes y tres escalas de hexágono. No depende de pruebas de significancia.
    conc, tablas = {}, {}
    for res in (6, 7, 8):
        tablas[res] = growth_cells(con, res)
        km2_terr = territory_km2(con, res)
        conc[f"h3_res{res}"] = {"km2_celda_media": round(km2_terr / count_cells(con, res), 2)}
        for name in ("wsf", "ghsl"):
            conc[f"h3_res{res}"][name] = concentration(tablas[res][name], tablas[res]["km2"], km2_terr)
    print("concentración del crecimiento 2000-2015:", json.dumps(conc, ensure_ascii=False))

    # 4b. Capa: las celdas de ~5 km² que suman la mitad del crecimiento WSF (la fuente del slider),
    #     marcando si también están entre las que suman la mitad del crecimiento GHSL.
    t7, km2_terr7 = tablas[7], territory_km2(con, 7)
    top_w, top_g = top_cells(t7["wsf"], 0.5), top_cells(t7["ghsl"], 0.5)
    both = top_w & top_g
    mitad = {
        "celdas_wsf": int(top_w.sum()), "celdas_ghsl": int(top_g.sum()),
        "coincidencia_jaccard": round(float(both.sum() / (top_w | top_g).sum()), 3),
        "celdas_en_ambas": int(both.sum()),
        "pct_territorio_en_ambas": round(100 * float(t7["km2"][both].sum()) / km2_terr7, 2),
        "pct_crecimiento_wsf_en_ambas": round(100 * float(t7["wsf"][both].sum() / t7["wsf"][t7["wsf"] > 0].sum()), 1),
    }
    con.register("mitad", {"cell": t7["cell"][top_w], "nuevo_wsf_m2": np.round(t7["wsf"][top_w]),
                           "nuevo_ghsl_m2": np.round(np.maximum(t7["ghsl"][top_w], 0)),
                           "tambien_en_ghsl": top_g[top_w]})
    con.execute(f"""
        COPY (SELECT h3_h3_to_string(cell::UBIGINT) AS h3, nuevo_wsf_m2, nuevo_ghsl_m2, tambien_en_ghsl,
                     ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell::UBIGINT)), 'OGC:CRS84') AS geometry
              FROM mitad ORDER BY nuevo_wsf_m2 DESC)
        TO '{(OUT / "hex_r7_mitad_crecimiento.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    print("mitad del crecimiento (res 7):", mitad)

    # 4c. Puntos calientes Gi* (DESCARTADOS como hallazgo): con la curva normal, las celdas calientes en las
    #     dos fuentes eran el 1,36% del territorio con el 70,4% del crecimiento; con Monte Carlo no resiste.
    con.execute("""
        CREATE TABLE lag AS
        WITH nb AS (SELECT cell, unnest(h3_grid_disk(cell, 1)) AS nbr FROM g7)
        SELECT nb.cell, count(*) AS w, sum(t.wsf) AS lag_wsf, sum(t.ghsl) AS lag_ghsl
        FROM nb JOIN g7 t ON t.cell = nb.nbr GROUP BY nb.cell
    """)
    lag = con.execute("SELECT l.w, l.lag_wsf, l.lag_ghsl FROM g7 JOIN lag l USING (cell) ORDER BY g7.cell").fetchnumpy()
    rng = np.random.default_rng(SEED)
    w = lag["w"].astype(float)
    g_w = gistar(t7["wsf"], w, lag["lag_wsf"].astype(float), rng)
    g_g = gistar(t7["ghsl"], w, lag["lag_ghsl"].astype(float), rng)

    def resumen(p_key: str, alpha: float) -> dict:
        hw, hg = hot(g_w, p_key, alpha), hot(g_g, p_key, alpha)
        b = hw & hg
        return {"celdas_calientes_wsf": int(hw.sum()), "celdas_calientes_ghsl": int(hg.sum()),
                "coincidencia_jaccard": round(float(b.sum() / (hw | hg).sum()), 3),
                "km2_calientes_de_ambas": round(float(t7["km2"][b].sum()), 1),
                "pct_territorio_calientes_de_ambas": round(100 * float(t7["km2"][b].sum()) / km2_terr7, 2),
                "pct_crecimiento_wsf_en_calientes_de_ambas":
                    round(100 * float(t7["wsf"][b].sum() / t7["wsf"][t7["wsf"] > 0].sum()), 1)}

    gi = {"simulaciones": N_SIMS, "semilla": SEED,
          "montecarlo": {"99": resumen("p_mc", 0.01), "95": resumen("p_mc", 0.05), "90": resumen("p_mc", 0.10)},
          "normal_version_descartada": {"99": resumen("p_normal", 0.01)}}
    print("Gi* 2000-2015 · Monte Carlo 99%:", gi["montecarlo"]["99"], "· normal 99%:", gi["normal_version_descartada"]["99"])
    res = {"lei_wsf": lei_wsf, "lei_ghsl": lei_ghsl, "concentracion_crecimiento_2000_2015": conc,
           "mitad_del_crecimiento_res7": mitad, "gistar_2000_2015_descartado": gi,
           "slider_hexagonos_por_anio": por_anio}
    (OUT / "p03_contraste_lei_gistar.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
