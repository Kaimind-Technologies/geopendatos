"""P03 · Validación antes de publicar: ¿qué afirmaciones resisten pruebas que podrían tumbarlas?

Complementa las verificaciones de PROCESO.md §3 (dos fuentes de suelo, modelo vs censo,
matriz 2×2) con cuatro pruebas nacionales. La metodología y los resultados están en VALIDACION.md.

  T1. Artefactos de la serie anual WSF. WSF-Evolution fecha cada píxel con el primer año en que
      lo detecta; si en algunos años hubo pocas imágenes Landsat, lo construido en esos años se
      "acumula" en el siguiente año con buenas imágenes. La firma es un salto en casi todos los
      estados el mismo año. Se mide en qué años saltan los estados a la vez y cuánto tendría que
      estar mal fechado para que "los 90 crecieron más rápido que 2000-2015" deje de ser cierto.
  T2. ODS 11.3.1 nacional con la población de los censos del INE (1990, 2001, 2011), sin modelos
      de población, en las mismas ventanas que los censos.
  T3. Línea base de la concentración: "la mitad del crecimiento en <1% del territorio" se compara
      con la concentración de lo que ya existía en 2000 (si se parecen, el hallazgo es "se creció
      donde ya había ciudad", no una concentración nueva) y con hexágonos de ~250 km² (res 5).
  T4. Sensibilidad de la tipología LEI 2000-2015: anillo de 100, 200 y 300 m; tres reglas para
      llevar WSF a 100 m (cualquier píxel, ≥25% y ≥50% de la celda) y tres umbrales del GHSL
      (10, 15 y 20% construido). El índice se calcula mancha por mancha, sin aproximaciones.

Requiere las salidas intermedias de prepare.py, growth.py y wsf_layers.py (data/, fuera del repo).
Crea data/wsf_evo/wsf_frac_{2000,2015}_100m.tif (fracción de asentamiento WSF por celda de 100 m).

Salida: output/p03_validacion.json

Uso:
    python -P verify_claims.py
"""

import json
import math
from pathlib import Path

import duckdb
import numpy as np
import rasterio
import shapely
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import Window, from_bounds
from scipy import ndimage
from shapely.geometry import box, shape

ROOT = Path(__file__).resolve().parents[1]
WSF = ROOT / "data" / "wsf_evo"
VEN = ROOT / "data" / "ghsl" / "ven"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
ADM1 = ROOT / "data" / "boundaries" / "gb-VEN-ADM1.geojson"
OUT = Path(__file__).resolve().parent / "output"
PIX = WSF / "pixeles.parquet"
FIRST100 = WSF / "wsf_primer_anio_100m.tif"
YEARS = list(range(1985, 2016))

# INE, población empadronada (Demografía de Venezuela, INE 2014; 2001 y 2011 coinciden con el Cuadro 2.2
# de las publicaciones por estado del Censo 2011). Fechas censales: 21-oct-1990, 22-oct-2001, 30-oct-2011.
CENSOS = {1990: 18_105_265, 2001: 23_054_210, 2011: 27_227_930}
# INE, estimaciones a mitad de año con corrección de omisión censal (vía citypopulation.de, "E 2001-06-30" y
# "E 2011-06-30"). Se usan solo como sensibilidad: muestran cuánto mueve la omisión censal la tasa 2001-2011.
INE_ESTIMADA = {2001: 24_802_885, 2011: 28_944_070}

SALTO = 2.0            # T1: un año "salta" si suma al menos el doble del incremento mediano del estado
MIN_KM2_ESTADO = 20    # T1: estados con al menos esta superficie WSF en 2015
RES_CONC = (5, 6, 7, 8)
WSF_REGLAS = {"cualquier_pixel": None, "25pct_de_la_celda": 25, "50pct_de_la_celda": 50}
GHSL_UMBRALES = {"10pct": 1_000, "15pct": 1_500, "20pct": 2_000}
ANILLOS = (1, 2, 3)    # celdas de 100 m


def tasa(serie: dict, a: int, b: int) -> float:
    return 100 * math.log(serie[b] / serie[a]) / (b - a)


# ---------------------------------------------------------------- T1 · artefactos de la serie anual
def serie_por_estado(px: dict) -> tuple[list[str], np.ndarray]:
    """km² WSF por estado (filas) y año de primera detección (columnas, 1985 = 1985 o antes)."""
    feats = json.loads(ADM1.read_text(encoding="utf-8"))["features"]
    names = ["(fuera de los estados simplificados)"] + [f["properties"]["shapeName"] for f in feats]
    est = np.zeros(len(px["lat"]), dtype=np.int64)
    for i, f in enumerate(feats, start=1):
        g = shape(f["geometry"])
        shapely.prepare(g)
        free = est == 0
        est[free] = np.where(shapely.contains_xy(g, px["lng"][free], px["lat"][free]), i, 0)
    idx = est * len(YEARS) + (px["anio"] - 1985)
    m = np.bincount(idx, weights=px["area_m2"] / 1e6, minlength=len(names) * len(YEARS))
    return names, m.reshape(len(names), len(YEARS))


def t1_artefactos(names: list[str], m: np.ndarray, ghsl: dict) -> dict:
    inc_nac = m.sum(axis=0)[1:]                    # km² nuevos por año, 1986-2015
    cum = dict(zip(YEARS, np.cumsum(m.sum(axis=0))))
    grandes = [i for i in range(1, len(names)) if m[i].sum() >= MIN_KM2_ESTADO]
    saltan = {}
    for k, y in enumerate(YEARS[1:]):
        saltan[y] = [names[i] for i in grandes if m[i, k + 1] >= SALTO * np.median(m[i, 1:])]
    base_nac = float(np.median(inc_nac))

    # Escenario pesimista: el exceso de 1991 sobre el ritmo típico de 1986-1999 (sin 1991 ni 1996) ya
    # existía antes de 1990 y quedó mal fechado.
    tipicos = [inc_nac[y - 1986] for y in range(1986, 2000) if y not in (1991, 1996)]
    exceso_1991 = float(inc_nac[1991 - 1986] - np.median(tipicos))
    exceso_1996 = float(inc_nac[1996 - 1986] - np.median(tipicos))
    nuevos_90 = cum[2000] - cum[1990]
    nuevos_00 = cum[2015] - cum[2000]
    ritmo_00 = nuevos_00 / 15

    def escenario(desplazado: float) -> dict:
        c90 = cum[1990] + desplazado
        return {"km2_por_anio_1990_2000": round((cum[2000] - c90) / 10, 1),
                "km2_por_anio_2000_2015": round(ritmo_00, 1),
                "pct_anual_1990_2000": round(100 * math.log(cum[2000] / c90) / 10, 2),
                "pct_anual_2000_2015": round(tasa(cum, 2000, 2015), 2)}

    # Cuántos km² fechados en 1991-2000 tendrían que ser anteriores a 1990 para que se empaten los ritmos.
    empate_km2 = nuevos_90 - 10 * ritmo_00
    # En %/año: c90 tal que ln(c2000/c90)/10 = tasa 2000-2015.
    empate_pct = cum[2000] / math.exp(tasa(cum, 2000, 2015) / 100 * 10) - cum[1990]
    return {
        "incremento_mediano_nacional_km2": round(base_nac, 1),
        "incremento_nacional_km2_por_anio": {y: round(float(v), 1) for y, v in zip(YEARS[1:], inc_nac)},
        "razon_vs_mediana_nacional": {y: round(float(v) / base_nac, 2) for y, v in zip(YEARS[1:], inc_nac)},
        "estados_evaluados": len(grandes),
        "estados_que_saltan_por_anio": {y: len(v) for y, v in saltan.items()},
        "estados_que_saltan_1991": saltan[1991], "estados_que_saltan_1996": saltan[1996],
        "exceso_1991_km2": round(exceso_1991, 1), "exceso_1996_km2": round(exceso_1996, 1),
        "contraste_90_vs_00": {"tal_cual": escenario(0.0), "exceso_1991_antes_de_1990": escenario(exceso_1991)},
        "km2_mal_fechados_para_empatar": {"en_km2_por_anio": round(empate_km2, 1), "en_pct_anual": round(empate_pct, 1)},
        "ghsl_pct_anual": {"1990_2000": round(tasa(ghsl, 1990, 2000), 2), "2000_2015": round(tasa(ghsl, 2000, 2015), 2)},
    }


# ---------------------------------------------------------------- T2 · ODS nacional con censos
def t2_ods_censos(cum: dict, ghsl: dict, pop_ghs: dict) -> dict:
    filas = []
    for a, b, ga, gb in ((1990, 2001, 1990, 2000), (2001, 2011, 2000, 2010), (1990, 2011, 1990, 2010)):
        p = tasa(CENSOS, a, b)
        w, g = tasa(cum, a, b), tasa(ghsl, ga, gb)
        filas.append({"periodo_censal": f"{a}-{b}", "poblacion_censo_pct": round(p, 2),
                      "wsf_pct_mismo_periodo": round(w, 2), "ods_wsf_censo": round(w / p, 2),
                      "ghsl_periodo": f"{ga}-{gb}", "ghsl_pct": round(g, 2), "ods_ghsl_censo": round(g / p, 2)})
    p_est = tasa(INE_ESTIMADA, 2001, 2011)
    sens = {"poblacion_ine_estimada_pct_2001_2011": round(p_est, 2),
            "ods_wsf_2001_2011": round(tasa(cum, 2001, 2011) / p_est, 2),
            "ods_ghsl_2000_2010": round(tasa(ghsl, 2000, 2010) / p_est, 2)}
    referencia = {"ods_wsf_ghspop_1985_2015": round(tasa(cum, 1985, 2015) / tasa(pop_ghs, 1985, 2015), 2),
                  "ods_ghsl_ghspop_1985_2015": round(tasa(ghsl, 1985, 2015) / tasa(pop_ghs, 1985, 2015), 2)}
    return {"con_censos": filas, "sensibilidad_omision_censal": sens, "version_publicada_con_ghs_pop": referencia}


# ---------------------------------------------------------------- T3 · línea base de la concentración
def territory_cells_sql(res: int) -> str:
    return f"""WITH parts AS (SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}'))
               SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), {res})) AS cell FROM parts"""


def top_share(x: np.ndarray, km2: np.ndarray, km2_terr: float, share: float = 0.5) -> float:
    """% del territorio que ocupan las celdas de mayor valor que, juntas, suman `share` del total."""
    xp = np.maximum(x, 0)
    order = np.argsort(-xp, kind="stable")
    k = int(np.searchsorted(np.cumsum(xp[order]) / xp.sum(), share)) + 1
    return 100 * float(km2[order[:k]].sum()) / km2_terr


def t3_concentracion(con) -> dict:
    out = {}
    for res in RES_CONC:
        d = con.execute(f"""
            WITH t AS ({territory_cells_sql(res)}),
            w AS (SELECT h3_latlng_to_cell(lat, lng, {res}) AS cell,
                         sum(area_m2) FILTER (WHERE anio > 2000 AND anio <= 2015) AS w_nuevo,
                         sum(area_m2) FILTER (WHERE anio <= 2000) AS w_2000
                  FROM read_parquet('{PIX.as_posix()}') GROUP BY cell),
            g AS (SELECT h3_latlng_to_cell(lat, lng, {res}) AS cell, sum(b2015 - b2000) AS g_nuevo, sum(b2000) AS g_2000
                  FROM read_parquet('{(VEN / "celdas.parquet").as_posix()}') GROUP BY cell)
            SELECT coalesce(w_nuevo, 0) AS w_nuevo, coalesce(w_2000, 0) AS w_2000,
                   coalesce(g_nuevo, 0) AS g_nuevo, coalesce(g_2000, 0) AS g_2000, h3_cell_area(u.cell, 'km^2') AS km2
            FROM (SELECT cell FROM t UNION SELECT cell FROM w UNION SELECT cell FROM g) u
            LEFT JOIN w USING (cell) LEFT JOIN g USING (cell) ORDER BY u.cell
        """).fetchnumpy()
        d = {k: v.astype(float) for k, v in d.items()}
        km2_terr = con.execute(f"SELECT sum(h3_cell_area(cell, 'km^2')) FROM ({territory_cells_sql(res)})").fetchall()[0][0]
        fila = {"km2_celda_media": round(km2_terr / con.execute(f"SELECT count(*) FROM ({territory_cells_sql(res)})").fetchall()[0][0], 1)}
        for fuente, nuevo, stock in (("wsf", "w_nuevo", "w_2000"), ("ghsl", "g_nuevo", "g_2000")):
            c_n, c_s = top_share(d[nuevo], d["km2"], km2_terr), top_share(d[stock], d["km2"], km2_terr)
            con_base = d[stock] > 0
            fila[fuente] = {"pct_territorio_mitad_del_crecimiento": round(c_n, 2),
                            "pct_territorio_mitad_de_lo_existente_2000": round(c_s, 2),
                            "crecimiento_vs_existente": round(c_n / c_s, 2),
                            "pct_crecimiento_en_celdas_con_asentamiento_en_2000":
                                round(100 * float(np.maximum(d[nuevo], 0)[con_base].sum() / np.maximum(d[nuevo], 0).sum()), 1)}
        out[f"h3_res{res}"] = fila
    km2_2015 = con.execute(f"SELECT sum(area_m2) / 1e6 FROM read_parquet('{PIX.as_posix()}')").fetchall()[0][0]
    km2_terr7 = con.execute(f"SELECT sum(h3_cell_area(cell, 'km^2')) FROM ({territory_cells_sql(7)})").fetchall()[0][0]
    out["asentamiento_wsf_2015_pct_territorio"] = round(100 * km2_2015 / km2_terr7, 2)
    return out


# ---------------------------------------------------------------- T4 · sensibilidad de la LEI
def wsf_fraction_grids() -> dict[int, Path]:
    """Fracción (0-100) de cada celda de 100 m del GHSL cubierta por asentamiento WSF en 2000 y 2015."""
    paths = {y: WSF / f"wsf_frac_{y}_100m.tif" for y in (2000, 2015)}
    if all(p.exists() for p in paths.values()):
        return paths
    ven = shape(json.loads(ADM0.read_text(encoding="utf-8"))["features"][0]["geometry"])
    with rasterio.open(VEN / "mask_estados.tif") as g:
        grid_t, grid_crs, gh, gw = g.transform, g.crs, g.height, g.width
        inside = g.read(1) > 0
    frac = {y: np.zeros((gh, gw), dtype="uint8") for y in paths}
    for f in sorted(WSF.glob("WSFevolution_v1_*.tif")):
        with rasterio.open(f) as src:
            if not ven.intersects(box(*src.bounds)):
                continue
            a = src.read(1)
            w = from_bounds(*transform_bounds(src.crs, grid_crs, *src.bounds), transform=grid_t)
            c0, r0 = max(int(math.floor(w.col_off)), 0), max(int(math.floor(w.row_off)), 0)
            c1, r1 = min(int(math.ceil(w.col_off + w.width)), gw), min(int(math.ceil(w.row_off + w.height)), gh)
            win = Window(c0, r0, c1 - c0, r1 - r0)
            for y in paths:
                dst = np.zeros((win.height, win.width), dtype="float32")
                reproject(((a >= 1985) & (a <= y)).astype("float32"), dst, src_transform=src.transform, src_crs=src.crs,
                          dst_transform=rasterio.windows.transform(win, grid_t), dst_crs=grid_crs,
                          resampling=Resampling.average, src_nodata=-1, dst_nodata=-1)
                sub = frac[y][r0:r1, c0:c1]
                np.maximum(sub, np.clip(np.round(dst * 100), 0, 100).astype("uint8"), out=sub)
        print("  fracción WSF:", f.name, flush=True)
    for y, p in paths.items():
        frac[y][~inside] = 0
        with rasterio.open(p, "w", driver="GTiff", width=gw, height=gh, count=1, dtype="uint8", crs=grid_crs,
                           transform=grid_t, nodata=0, compress="deflate", tiled=True) as dst:
            dst.write(frac[y], 1)
    return paths


def lei_exacta(old: np.ndarray, new: np.ndarray, anillos: tuple[int, ...]) -> dict[int, dict]:
    """LEI (Liu et al., 2010) mancha por mancha: % del anillo de r celdas alrededor de cada mancha nueva que
    ya era urbano. ≥50 relleno, 0-50 borde, 0 salto. El anillo no cuenta celdas de otras manchas nuevas."""
    lab, n = ndimage.label(new, structure=np.ones((3, 3), dtype=bool))
    area = np.bincount(lab.ravel(), minlength=n + 1)
    area[0] = 0
    objs = ndimage.find_objects(lab)
    h, w = lab.shape
    out = {}
    for r in anillos:
        st = np.ones((2 * r + 1, 2 * r + 1), dtype=bool)
        idx = np.zeros(n + 1)
        for i, sl in enumerate(objs, start=1):
            y0, y1 = max(sl[0].start - r, 0), min(sl[0].stop + r, h)
            x0, x1 = max(sl[1].start - r, 0), min(sl[1].stop + r, w)
            sub = lab[y0:y1, x0:x1]
            ring = ndimage.binary_dilation(sub == i, structure=st) & (sub == 0)
            nr = ring.sum()
            idx[i] = 100 * old[y0:y1, x0:x1][ring].sum() / nr if nr else 0
        tipo = np.where(idx >= 50, 0, np.where(idx > 0, 1, 2))
        tot = area.sum()
        out[r] = {"km2_nuevos": round(tot / 100, 1), "manchas": int(n),
                  "pct_relleno": round(100 * area[tipo == 0].sum() / tot, 1),
                  "pct_expansion_de_borde": round(100 * area[tipo == 1].sum() / tot, 1),
                  "pct_salto": round(100 * area[tipo == 2].sum() / tot, 1)}
    return out


def t4_lei() -> dict:
    corridas = {}
    with rasterio.open(FIRST100) as src:
        first = src.read(1)
    fr = {y: rasterio.open(p).read(1) for y, p in wsf_fraction_grids().items()}
    for regla, umbral in WSF_REGLAS.items():
        if umbral is None:
            old, new = (first > 0) & (first <= 2000), (first > 2000) & (first <= 2015)
        else:
            old = fr[2000] >= umbral
            new = (fr[2015] >= umbral) & ~old
        for r, v in lei_exacta(old, new, ANILLOS).items():
            corridas[f"wsf_{regla}_anillo_{r * 100}m"] = v
            print(f"  LEI WSF {regla}, anillo {r * 100} m:", v, flush=True)
        del old, new
    del first, fr
    with rasterio.open(VEN / "built_2000.tif") as s0, rasterio.open(VEN / "built_2015.tif") as s1:
        b0, b1 = s0.read(1), s1.read(1)
    for nombre, umbral in GHSL_UMBRALES.items():
        old = b0 >= umbral
        for r, v in lei_exacta(old, (b1 >= umbral) & ~old, ANILLOS).items():
            corridas[f"ghsl_{nombre}_anillo_{r * 100}m"] = v
            print(f"  LEI GHSL {nombre}, anillo {r * 100} m:", v, flush=True)
    vals = list(corridas.values())
    borde = [v["pct_expansion_de_borde"] for v in vals]
    pegado = [v["pct_relleno"] + v["pct_expansion_de_borde"] for v in vals]
    salto = [v["pct_salto"] for v in vals]
    relleno = [v["pct_relleno"] for v in vals]
    return {"corridas": corridas, "rango": {
        "pct_expansion_de_borde": [min(borde), max(borde)], "pct_relleno": [min(relleno), max(relleno)],
        "pct_salto": [min(salto), max(salto)], "pct_relleno_mas_borde": [round(min(pegado), 1), round(max(pegado), 1)],
        "borde_es_el_tipo_mas_comun_en_todas": all(v["pct_expansion_de_borde"] > max(v["pct_relleno"], v["pct_salto"]) for v in vals),
        "borde_mas_de_la_mitad_en_todas": all(b > 50 for b in borde)}}


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    px = con.execute(f"SELECT lat, lng, anio, area_m2 FROM read_parquet('{PIX.as_posix()}')").fetchnumpy()
    px = {k: np.asarray(v) for k, v in px.items()}
    nac = json.loads((OUT / "p03_nacional.json").read_text(encoding="utf-8"))["epocas"]
    ghsl = {e["anio"]: e["construido_km2"] for e in nac}
    pop_ghs = {e["anio"]: e["poblacion"] for e in nac}

    names, m = serie_por_estado(px)
    cum = dict(zip(YEARS, np.cumsum(m.sum(axis=0))))
    print(f"serie WSF (contorno ADM0): {cum[1985]:,.1f} → {cum[2015]:,.1f} km² (esperado 2.541,9 → 4.389,4)")
    res = {"t1_artefactos_serie_anual": t1_artefactos(names, m, ghsl)}
    t1 = res["t1_artefactos_serie_anual"]
    print("T1 · estados que saltan por año:", t1["estados_que_saltan_por_anio"])
    print("T1 · contraste 90 vs 2000-2015:", t1["contraste_90_vs_00"], "· km² mal fechados para empatar:",
          t1["km2_mal_fechados_para_empatar"])

    res["t2_ods_nacional_con_censos"] = t2_ods_censos(cum, ghsl, pop_ghs)
    print("T2 · ODS con censos:", json.dumps(res["t2_ods_nacional_con_censos"], ensure_ascii=False))

    res["t3_concentracion_vs_linea_base"] = t3_concentracion(con)
    print("T3 · concentración vs lo existente:", json.dumps(res["t3_concentracion_vs_linea_base"], ensure_ascii=False))

    res["t4_sensibilidad_lei_2000_2015"] = t4_lei()
    print("T4 · rangos LEI:", res["t4_sensibilidad_lei_2000_2015"]["rango"])
    (OUT / "p03_validacion.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
