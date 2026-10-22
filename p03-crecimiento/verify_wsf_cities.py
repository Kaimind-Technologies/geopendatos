"""P03 · Verificación por ciudad: crecimiento del suelo urbano GHSL vs WSF-Evolution.

Usa EXACTAMENTE la misma extensión de cada ciudad en las dos fuentes: la mancha
urbana continua de 2020 de cities.py (umbral 15%, cierre 300 m), convertida a
polígono, reproyectada de Mollweide a EPSG:4326 y aplicada sobre los píxeles de
~30 m del WSF-Evolution. Incluye Caracas metropolitana (manchas a <35 km del centro).

Para cada ciudad y período compara la tasa anual del GHSL (m² construidos) con la del
WSF (área de asentamiento) y el ODS 11.3.1 que resulta con cada una, usando la misma
población (GHS-POP). Una cifra de ciudad se considera publicable solo si las dos
fuentes coinciden en la lectura (expansión / equilibrio / densificación).

Salida: output/p03_verificacion_wsf_ciudades.json

Uso:
    python -P verify_wsf_cities.py
"""

import json
import math
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize, shapes
from scipy import ndimage
from shapely.geometry import box, mapping, shape
from shapely.ops import transform as shp_transform, unary_union

ROOT = Path(__file__).resolve().parents[1]
VEN = ROOT / "data" / "ghsl" / "ven"
WSF = ROOT / "data" / "wsf_evo"
OUT = Path(__file__).resolve().parent / "output"
URBANO = 1_500
CARACAS = (-66.9036, 10.4806)
YEARS = list(range(1985, 2016))
PERIODOS = [(1985, 1990), (1990, 2000), (2000, 2015), (1985, 2015)]
R = 6_371_008.8


def lectura(x: float | None) -> str:
    if x is None or math.isnan(x):
        return "sin lectura"
    return "densificación" if x < 0.9 else ("expansión" if x > 1.1 else "equilibrio")


def city_polygons() -> list[tuple[str, object]]:
    with rasterio.open(VEN / "built_2020.tif") as src:
        b = src.read(1)
        transform, crs = src.transform, src.crs
    closed = ndimage.binary_closing(b >= URBANO, structure=np.ones((7, 7), dtype=bool))
    lab, n = ndimage.label(closed)
    sizes = ndimage.sum(b, lab, index=np.arange(1, n + 1))
    top = list(np.argsort(sizes)[::-1][:10] + 1)
    ciudades = json.loads((OUT / "p03_ciudades.json").read_text(encoding="utf-8"))["umbral_15_cierre_300m"]["ciudades"]
    to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform
    to_m = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    cx, cy = to_m.transform(*CARACAS)

    def poly(mask: np.ndarray):
        geoms = [shape(g) for g, v in shapes(mask.astype("uint8"), mask=mask, transform=transform) if v == 1]
        return shp_transform(to_ll, unary_union(geoms))

    out = [(c["nombre"], poly(lab == comp)) for comp, c in zip(top, ciudades)]
    coms = ndimage.center_of_mass(closed, lab, index=np.arange(1, n + 1))
    near = [i + 1 for i, (yy, xx) in enumerate(coms) if math.dist(transform * (xx + 0.5, yy + 0.5), (cx, cy)) < 35_000]
    out.append(("Caracas metropolitana", poly(np.isin(lab, near))))
    return out


def row_areas(src) -> np.ndarray:
    t = src.transform
    lat_top = t.f + np.arange(src.height) * t.e
    return R ** 2 * math.radians(abs(t.a)) * np.abs(np.sin(np.radians(lat_top)) - np.sin(np.radians(lat_top + t.e)))


def main() -> None:
    cities = city_polygons()
    print("polígonos de ciudad listos:", len(cities), flush=True)
    acc = np.zeros((len(cities), len(YEARS)))
    # Caracas metropolitana se solapa con Caracas: se rasteriza aparte.
    groups = [list(range(len(cities) - 1)), [len(cities) - 1]]
    for f in sorted(WSF.glob("WSFevolution_v1_*.tif")):
        with rasterio.open(f) as src:
            tb = box(*src.bounds)
            idx_any = [i for i, (_, g) in enumerate(cities) if g.intersects(tb)]
            if not idx_any:
                continue
            a = src.read(1)
            areas = np.broadcast_to(row_areas(src)[:, None], a.shape)
            for group in groups:
                sel = [i for i in group if i in idx_any]
                if not sel:
                    continue
                lab = rasterize([(mapping(cities[i][1]), i + 1) for i in sel], out_shape=a.shape,
                                transform=src.transform, dtype="uint8")
                inside = (lab > 0) & (a >= 1985)
                yr, lb, ar = a[inside], lab[inside], areas[inside]
                for k, y in enumerate(YEARS):
                    m = yr == y
                    if m.any():
                        acc[:, k] += np.bincount(lb[m] - 1, weights=ar[m], minlength=len(cities))[:len(cities)]
        print("  procesado", f.name, flush=True)

    ghsl = json.loads((OUT / "p03_ciudades.json").read_text(encoding="utf-8"))["umbral_15_cierre_300m"]
    gcities = {c["nombre"]: c for c in ghsl["ciudades"]}
    gcities["Caracas metropolitana"] = ghsl["caracas_metropolitana"]
    res = {}
    for i, (name, _) in enumerate(cities):
        wsf = {y: float(v) / 1e6 for y, v in zip(YEARS, np.cumsum(acc[i]))}
        g = gcities[name]
        gb = {int(k): v for k, v in g["construido_km2"].items()}
        pop = {int(k): v for k, v in g["poblacion"].items()}
        filas = []
        for a, b in PERIODOS:
            yrs = b - a
            pgr = math.log(pop[b] / pop[a]) / yrs
            g_r = math.log(gb[b] / gb[a]) / yrs
            w_r = math.log(wsf[b] / wsf[a]) / yrs if wsf[a] > 0 else float("nan")
            og, ow = (g_r / pgr if pgr > 0 else float("nan")), (w_r / pgr if pgr > 0 else float("nan"))
            filas.append({"periodo": f"{a}-{b}", "poblacion_pct": round(100 * pgr, 2),
                          "ghsl_pct": round(100 * g_r, 2), "wsf_pct": round(100 * w_r, 2),
                          "ods_ghsl": round(og, 2), "ods_wsf": round(ow, 2),
                          "coinciden": lectura(og) == lectura(ow), "lectura_ghsl": lectura(og), "lectura_wsf": lectura(ow)})
        res[name] = {"wsf_km2_1985": round(wsf[1985], 1), "wsf_km2_2015": round(wsf[2015], 1), "periodos": filas}
        print(f"\n{name[:45]} · WSF {wsf[1985]:.1f} → {wsf[2015]:.1f} km²")
        for r in filas:
            mark = "✓" if r["coinciden"] else "✗"
            print(f"   {r['periodo']}: pobl {r['poblacion_pct']:>6}% · GHSL {r['ghsl_pct']:>5}% (ODS {r['ods_ghsl']:>5}) · "
                  f"WSF {r['wsf_pct']:>5}% (ODS {r['ods_wsf']:>5})  {mark} {r['lectura_ghsl']} / {r['lectura_wsf']}")
    (OUT / "p03_verificacion_wsf_ciudades.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
