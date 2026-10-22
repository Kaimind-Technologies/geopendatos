"""P03: crecimiento por ciudad 1975-2020 e indicador ODS 11.3.1 (LCRPGR).

Ciudad = mancha urbana continua de 2020 en el GHSL: celdas de 100 m con al menos
`umbral` de suelo construido, unidas por un cierre morfológico (`cierre_m`). Dentro
de esa extensión fija se mide, para cada época, lo construido (km²) y la población.

ODS 11.3.1 (ONU-Hábitat): LCRPGR = [ln(Urb_t2/Urb_t1)/años] / [ln(Pob_t2/Pob_t1)/años].
>1: el suelo construido crece más rápido que la población (expansión dispersa);
<1: densificación. Si la población cae, el cociente no se interpreta.

Se repite con varios umbrales para medir la sensibilidad. Caracas tiene además una
versión metropolitana (manchas a menos de 35 km del centro), porque las montañas la
parten en varios núcleos (ver P02).

Salida: output/p03_ciudades.json

Uso:
    python -P cities.py
"""

import json
import math
import time
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
VEN = ROOT / "data" / "ghsl" / "ven"
OUT = Path(__file__).resolve().parent / "output"
EPOCHS = list(range(1975, 2021, 5))
PERIODOS = [(1975, 1990), (1990, 2000), (2000, 2015), (2015, 2020), (1975, 2020)]
ESCENARIOS = [(0.15, 300), (0.10, 300), (0.20, 300)]  # (fracción construida mínima, cierre en metros)
TOP = 10
CARACAS = (-66.9036, 10.4806)


def ods(urb: dict, pob: dict, a: int, b: int) -> dict:
    y = b - a
    lcr = math.log(urb[b] / urb[a]) / y
    pgr = math.log(pob[b] / pob[a]) / y if pob[a] > 0 and pob[b] > 0 else float("nan")
    return {"suelo_pct_anual": round(100 * lcr, 2), "poblacion_pct_anual": round(100 * pgr, 2),
            "ods_11_3_1": round(lcr / pgr, 2) if pgr > 0 else None}


NAMES_CACHE = OUT / "_nombres_cache.json"


def nombre(lat: float, lng: float) -> str:
    """Nombre por geocodificación inversa (Nominatim/OSM), con caché en disco y reintentos."""
    cache = json.loads(NAMES_CACHE.read_text(encoding="utf-8")) if NAMES_CACHE.exists() else {}
    key = f"{lat:.2f},{lng:.2f}"
    if key in cache:
        return cache[key]
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lng}&zoom=10&accept-language=es",
        headers={"User-Agent": "Kaimind-venezuela-datos-abiertos/1.0 (research)"})
    for intento in range(3):
        try:
            a = json.load(urllib.request.urlopen(req, timeout=30)).get("address", {})
            break
        except OSError:
            time.sleep(5 * (intento + 1))
    else:
        return f"sin nombre ({key})"
    time.sleep(1.2)
    name = ", ".join(v for k, v in a.items() if k in ("city", "town", "municipality", "state"))
    cache[key] = name
    NAMES_CACHE.parent.mkdir(parents=True, exist_ok=True)
    NAMES_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return name


def main() -> None:
    with rasterio.open(VEN / "built_2020.tif") as src:
        built2020 = src.read(1)
        transform, crs = src.transform, src.crs
    builts = {e: rasterio.open(VEN / f"built_{e}.tif").read(1) for e in EPOCHS}
    pops = {e: rasterio.open(VEN / f"pop_{e}.tif").read(1) for e in EPOCHS}
    to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    to_m = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    cx, cy = to_m.transform(*CARACAS)

    resultados = {}
    names_cache: dict[tuple, str] = {}
    for umbral, cierre in ESCENARIOS:
        urban = built2020 >= umbral * 10_000
        r = max(1, cierre // 100)
        struct = np.ones((2 * r + 1, 2 * r + 1), dtype=bool)
        closed = ndimage.binary_closing(urban, structure=struct)
        lab, n = ndimage.label(closed)
        sizes = ndimage.sum(built2020, lab, index=np.arange(1, n + 1))
        top = np.argsort(sizes)[::-1][:TOP] + 1
        ciudades = []
        for comp in top:
            m = lab == comp
            ys, xs = np.nonzero(m)
            px, py = transform * (xs.mean() + 0.5, ys.mean() + 0.5)
            lng, lat = to_ll.transform(px, py)
            key = (round(lat, 2), round(lng, 2))
            if key not in names_cache:
                names_cache[key] = nombre(lat, lng)
            urb = {e: float(builts[e][m].sum(dtype="float64")) / 1e6 for e in EPOCHS}
            pob = {e: float(pops[e][m].sum(dtype="float64")) for e in EPOCHS}
            ciudades.append({
                "nombre": names_cache[key], "lat": round(lat, 4), "lng": round(lng, 4),
                "extension_2020_km2": round(m.sum() / 100, 1),
                "construido_km2": {e: round(urb[e], 1) for e in EPOCHS},
                "poblacion": {e: round(pob[e]) for e in EPOCHS},
                "construido_veces_1975_2020": round(urb[2020] / urb[1975], 2) if urb[1975] else None,
                "ods": {f"{a}-{b}": ods(urb, pob, a, b) for a, b in PERIODOS},
            })
        # Caracas metropolitana: todas las manchas cuyo centroide está a <35 km del centro.
        coms = ndimage.center_of_mass(closed, lab, index=np.arange(1, n + 1))
        near = [i + 1 for i, (yy, xx) in enumerate(coms)
                if math.dist(transform * (xx + 0.5, yy + 0.5), (cx, cy)) < 35_000]
        mm = np.isin(lab, near)
        urb = {e: float(builts[e][mm].sum(dtype="float64")) / 1e6 for e in EPOCHS}
        pob = {e: float(pops[e][mm].sum(dtype="float64")) for e in EPOCHS}
        caracas_metro = {"manchas": len(near), "construido_km2": {e: round(urb[e], 1) for e in EPOCHS},
                         "poblacion": {e: round(pob[e]) for e in EPOCHS},
                         "ods": {f"{a}-{b}": ods(urb, pob, a, b) for a, b in PERIODOS}}
        resultados[f"umbral_{int(umbral * 100)}_cierre_{cierre}m"] = {"ciudades": ciudades, "caracas_metropolitana": caracas_metro}
        print(f"\n=== umbral {int(umbral * 100)}%, cierre {cierre} m: {n:,} manchas ===")
        for c in ciudades:
            o = c["ods"]
            print(f"{c['nombre'][:42]:44}{c['construido_km2'][1975]:>7}→{c['construido_km2'][2020]:<7} km² "
                  f"×{c['construido_veces_1975_2020']:<5} ODS 75-90 {o['1975-1990']['ods_11_3_1']} · 90-00 {o['1990-2000']['ods_11_3_1']}"
                  f" · 00-15 {o['2000-2015']['ods_11_3_1']} · pobl. 15-20 {o['2015-2020']['poblacion_pct_anual']}%/año")
        cm = caracas_metro
        print(f"Caracas metropolitana ({cm['manchas']} manchas): {cm['construido_km2'][1975]}→{cm['construido_km2'][2020]} km² · "
              f"ODS 75-20 {cm['ods']['1975-2020']['ods_11_3_1']}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "p03_ciudades.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
