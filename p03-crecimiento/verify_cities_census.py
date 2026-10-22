"""P03 · ODS 11.3.1 por ciudad con la población censal de los MUNICIPIOS, no del estado.

La matriz 2×2 (robustness_matrix.py) usaba el crecimiento censal del estado como proxy de la
población de la ciudad. Es un proxy grueso: el estado incluye pueblos y zonas rurales que pueden
crecer a otro ritmo. Aquí cada ciudad toma los municipios que caen mayoritariamente dentro de su
mancha urbana: un municipio entra si al menos el 50% de su población (GHS-POP 2010) vive dentro de
la mancha. Así la elección de municipios no se hace a mano.

Combinaciones por ciudad (4 × 3 × 3 = 36):
  población (2001-2011 salvo GHS-POP): GHS-POP en la mancha (2000-2015) · censo del estado o estados
      de esos municipios · censo de los municipios (INE, Cuadro 2.2, población empadronada) ·
      estimación INE de los municipios con corrección de omisión censal
  suelo: GHSL 2000-2015 · WSF 2000-2015 · WSF 2001-2011 (misma ventana que los censos)
  mancha urbana de 2020: 10, 15 y 20% construido (cierre de 300 m, como cities.py)

Regla (la de robustness_matrix.py): "densificación robusta" si las 36 dan ODS < 0,9; "expansión
robusta" si las 36 dan > 1,1; si no, "no concluyente". Si falta el censo de algún municipio de la
ciudad en datos/censo_municipal_2001_2011.csv (columnas vacías), la ciudad queda "sin censo municipal"
y solo se informa el rango de las combinaciones disponibles.

Entradas: datos/censo_municipal_2001_2011.csv (fuentes en VALIDACION.md) y las salidas
intermedias de prepare.py y wsf_layers.py (data/, fuera del repo).

Salida: output/p03_validacion_ciudades.json

Uso:
    python -P verify_cities_census.py
"""

import csv
import json
import math
import unicodedata
import urllib.request
from pathlib import Path

import duckdb
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from scipy import ndimage
from shapely.geometry import mapping, shape
from shapely.ops import transform as shp_transform

ROOT = Path(__file__).resolve().parents[1]
VEN = ROOT / "data" / "ghsl" / "ven"
PIX = ROOT / "data" / "wsf_evo" / "pixeles.parquet"
ADM1 = ROOT / "data" / "boundaries" / "gb-VEN-ADM1.geojson"
ADM2 = ROOT / "data" / "boundaries" / "gb-VEN-ADM2.geojson"
ADM2_URL = ("https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/VEN/"
            "ADM2/geoBoundaries-VEN-ADM2_simplified.geojson")
P03 = Path(__file__).resolve().parent
OUT = P03 / "output"
CENSO_MUN = P03 / "datos" / "censo_municipal_2001_2011.csv"
UMBRALES = {"10pct": 1_000, "15pct": 1_500, "20pct": 2_000}
CIERRE = np.ones((7, 7), dtype=bool)   # 300 m, como cities.py
TOP = 10
CARACAS = (-66.9036, 10.4806)
MIN_PARTE = 0.5
YEARS = list(range(1985, 2016))
ALIAS = {"Bustamante": "Maracaibo", "Valencia": "Valencia", "Caracas, Parroquia Catedral": "Caracas (valle)",
         "La Morita": "Maracay-Turmero", "Barquisimeto": "Barquisimeto", "Ciudad Guayana": "Ciudad Guayana",
         "Baralt": "Costa Oriental del Lago", "Barcelona": "Barcelona-Puerto La Cruz", "Maturín": "Maturín",
         "El Valle": "Margarita"}
# Nombres de geoBoundaries que difieren de los del INE.
ADM2_ALIAS = {"DIEGO BAUTISTA URBANEJO": "DIEGO BAUTISTA URBANEJA", "SIR ARTHUR MAC GREGOR": "SIR ARTHUR MC GREGOR"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper().strip()
    return ADM2_ALIAS.get(s, s)


def tasa(a: float, b: float, anios: int) -> float | None:
    return 100 * math.log(b / a) / anios if a > 0 and b > 0 else None


def municipios_raster(transform, crs, shape_hw) -> tuple[np.ndarray, list[tuple[str, str]]]:
    """Raster de municipios (ADM2) en la grilla del GHSL y su (estado, municipio) normalizado."""
    if not ADM2.exists():
        urllib.request.urlretrieve(ADM2_URL, ADM2)
    to_moll = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform
    estados = [(f["properties"]["shapeName"], shape(f["geometry"]))
               for f in json.loads(ADM1.read_text(encoding="utf-8"))["features"]]
    feats = json.loads(ADM2.read_text(encoding="utf-8"))["features"]
    claves, geoms = [], []
    for f in feats:
        g = shape(f["geometry"])
        estado = max(estados, key=lambda e: e[1].intersection(g).area)[0]   # estado con mayor solape
        claves.append((norm(estado), norm(f["properties"]["shapeName"])))
        geoms.append((mapping(shp_transform(to_moll, g)), len(claves)))
    lab = rasterize(geoms, out_shape=shape_hw, transform=transform, dtype="uint16")
    return lab, claves


def manchas(built2020: np.ndarray, umbral: int) -> tuple[np.ndarray, np.ndarray, int]:
    closed = ndimage.binary_closing(built2020 >= umbral, structure=CIERRE)
    lab, n = ndimage.label(closed)
    sizes = ndimage.sum(built2020, lab, index=np.arange(1, n + 1))
    return lab, np.argsort(sizes)[::-1][:TOP] + 1, n


def caracas_metro(lab: np.ndarray, n: int, transform, crs) -> np.ndarray:
    cx, cy = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(*CARACAS)
    coms = ndimage.center_of_mass(lab > 0, lab, index=np.arange(1, n + 1))
    near = [i + 1 for i, (yy, xx) in enumerate(coms) if math.dist(transform * (xx + 0.5, yy + 0.5), (cx, cy)) < 35_000]
    return np.flatnonzero(np.isin(lab, near))


def main() -> None:
    with rasterio.open(VEN / "built_2020.tif") as src:
        built2020, transform, crs = src.read(1), src.transform, src.crs
    rd = lambda n: rasterio.open(VEN / n).read(1).ravel()
    b = {e: rd(f"built_{e}.tif") for e in (2000, 2015)}
    p = {e: rd(f"pop_{e}.tif") for e in (2000, 2010, 2015)}

    # Población por municipio: censo (Cuadro 2.2) y estimación INE.
    censo = {}
    with CENSO_MUN.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            censo[(norm(r["estado"]), r["municipio"])] = {k: int(r[k]) if r[k] else None for k in
                                                          ("censo_2001", "censo_2011", "ine_estimada_2001", "ine_estimada_2011")}
    estado_tot = {norm(r["estado"]): (r["censo_2001"], r["censo_2011"]) for r in
                  json.loads((OUT / "p03_verificacion_poblacion.json").read_text(encoding="utf-8"))["estados"]}
    # Control de la transcripción: los municipios de cada estado deben sumar el total estatal del censo.
    control = {}
    for est in sorted({e for e, _ in censo}):
        filas = [v for (e, _), v in censo.items() if e == est]
        if any(v["censo_2001"] is None for v in filas):
            control[est] = "sin censo municipal"
            continue
        suma = (sum(v["censo_2001"] for v in filas), sum(v["censo_2011"] for v in filas))
        control[est] = "cuadra" if suma == estado_tot[est] else f"NO CUADRA: {suma} vs {estado_tot[est]}"
    print("control del censo municipal:", control)
    if any(v.startswith("NO CUADRA") for v in control.values()):
        raise SystemExit("revisar la transcripción de datos/censo_municipal_2001_2011.csv")
    mlab, claves = municipios_raster(transform, crs, built2020.shape)
    mlab = mlab.ravel()
    pop_muni = np.bincount(mlab, weights=p[2010], minlength=len(claves) + 1)

    # Píxeles WSF → celda de 100 m del GHSL.
    con = duckdb.connect()
    px = con.execute(f"SELECT lat, lng, anio, area_m2 FROM read_parquet('{PIX.as_posix()}')").fetchnumpy()
    x, y = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(np.asarray(px["lng"]), np.asarray(px["lat"]))
    col = np.floor((x - transform.c) / transform.a).astype(np.int64)
    row = np.floor((y - transform.f) / transform.e).astype(np.int64)
    ok = (row >= 0) & (row < built2020.shape[0]) & (col >= 0) & (col < built2020.shape[1])
    celda = row[ok] * built2020.shape[1] + col[ok]          # índice plano de la celda de 100 m
    anio, area = np.asarray(px["anio"])[ok], np.asarray(px["area_m2"])[ok]

    nombres15 = [c["nombre"] for c in json.loads((OUT / "p03_ciudades.json").read_text(encoding="utf-8"))
                 ["umbral_15_cierre_300m"]["ciudades"]]
    alias15 = [next(v for k, v in ALIAS.items() if k in n) for n in nombres15]
    lab15, top15, n15 = manchas(built2020, UMBRALES["15pct"])
    ref = {a: np.flatnonzero(lab15 == c) for a, c in zip(alias15, top15)}   # celdas de cada mancha (índices planos)
    ref["Caracas metropolitana"] = caracas_metro(lab15, n15, transform, crs)
    del lab15

    res = {a: {"combinaciones": {}, "municipios": {}} for a in ref}
    for nu, umbral in UMBRALES.items():
        if nu == "15pct":
            masks = ref
        else:
            lab, _, n = manchas(built2020, umbral)
            masks = {}
            for a, m in ref.items():
                if a == "Caracas metropolitana":
                    masks[a] = caracas_metro(lab, n, transform, crs)
                else:                                   # la mancha de este umbral que más se solapa con la de 15%
                    cnt = np.bincount(lab.ravel()[m], minlength=n + 1)
                    cnt[0] = 0
                    masks[a] = np.flatnonzero(lab == int(cnt.argmax()))
            del lab
        for a, m in masks.items():
            # Municipios de la ciudad: ≥50% de su población dentro de la mancha.
            dentro = np.bincount(mlab[m], weights=p[2010][m], minlength=len(claves) + 1)
            incl = [i for i in range(1, len(claves) + 1) if pop_muni[i] > 0 and dentro[i] / pop_muni[i] >= MIN_PARTE]
            cobertura = float(dentro[incl].sum() / dentro[1:].sum())
            faltan = [claves[i - 1] for i in incl if censo.get(claves[i - 1], {}).get("censo_2001") is None]
            res[a]["municipios"][nu] = {"incluidos": [f"{claves[i - 1][1]} ({claves[i - 1][0]})" for i in incl],
                                        "pct_poblacion_de_la_mancha_en_esos_municipios": round(100 * cobertura, 1),
                                        "sin_dato_censal": [f"{k[1]} ({k[0]})" for k in faltan]}
            pop = {"ghs_pop_2000_2015": tasa(p[2000][m].sum(dtype="float64"), p[2015][m].sum(dtype="float64"), 15)}
            sts = sorted({claves[i - 1][0] for i in incl})
            if sts and all(s in estado_tot for s in sts):
                pop["censo_estado_2001_2011"] = tasa(sum(estado_tot[s][0] for s in sts), sum(estado_tot[s][1] for s in sts), 10)
            for k, nombre in (("censo", "censo_municipal_2001_2011"), ("ine_estimada", "ine_estimada_municipal_2001_2011")):
                vals = [censo.get(claves[i - 1], {}).get(f"{k}_{yr}") for i in incl for yr in (2001, 2011)]
                if incl and None not in vals:
                    pop[nombre] = tasa(sum(vals[0::2]), sum(vals[1::2]), 10)
            inm = np.isin(celda, m)
            w = np.cumsum(np.bincount(anio[inm] - 1985, weights=area[inm], minlength=len(YEARS)))
            suelo = {"ghsl_2000_2015": tasa(b[2000][m].sum(dtype="float64"), b[2015][m].sum(dtype="float64"), 15),
                     "wsf_2000_2015": tasa(w[2000 - 1985], w[2015 - 1985], 15),
                     "wsf_2001_2011": tasa(w[2001 - 1985], w[2011 - 1985], 10)}
            for ks, vs in suelo.items():
                for kp, vp in pop.items():
                    # Si la población no crece y el suelo sí, el cociente no se interpreta: cuenta como expansión.
                    ods = vs / vp if vp and vp > 0 else float("inf")
                    res[a]["combinaciones"][f"{nu} · {ks} · {kp}"] = round(ods, 2) if math.isfinite(ods) else "pob. no crece"
            res[a].setdefault("tasas_pct_anual", {})[nu] = {**{k: round(v, 2) for k, v in suelo.items()},
                                                          **{k: round(v, 2) for k, v in pop.items() if v is not None}}
        print(f"umbral {nu} listo", flush=True)

    previa = json.loads((OUT / "p03_matriz_robustez.json").read_text(encoding="utf-8"))
    print(f"\n{'ciudad':26}{'n':>4}{'mín':>7}{'máx':>7}   lectura (antes → ahora)")
    for a, r in res.items():
        v = [x if isinstance(x, float) else float("inf") for x in r["combinaciones"].values()]
        tiene_mun = any("censo_municipal" in k for k in r["combinaciones"])
        if all(x < 0.9 for x in v) and tiene_mun:
            lect = "densificación robusta"
        elif all(x > 1.1 for x in v) and tiene_mun:
            lect = "expansión robusta"
        elif not tiene_mun:
            lect = "sin censo municipal"
        else:
            lect = "no concluyente"
        solo_mun = [x for k, x in zip(r["combinaciones"], v) if "censo_municipal" in k]
        r.update({"n_combinaciones": len(v), "ods_min": round(min(v), 2), "ods_max": round(max(v), 2) if math.isfinite(max(v)) else "inf",
                  "ods_solo_censo_municipal": [round(min(solo_mun), 2), round(max(solo_mun), 2)] if solo_mun else None,
                  "lectura": lect, "lectura_matriz_2x2": previa.get(a, {}).get("lectura")})
        print(f"{a[:25]:26}{len(v):>4}{r['ods_min']:>7}{str(r['ods_max']):>7}   {r['lectura_matriz_2x2']} → {lect}")
    res["_control_censo_municipal"] = control
    (OUT / "p03_validacion_ciudades.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
