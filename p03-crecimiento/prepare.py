"""P03: mosaico y recorte del GHSL para Venezuela + cifras nacionales por época.

Para cada época 1975-2020 une los 6 tiles de GHS-BUILT-S (m² construidos por celda
de 100 m) y GHS-POP (habitantes por celda), recorta con el polígono de Venezuela
(geoBoundaries, sin Esequibo) reproyectado a Mollweide y guarda GeoTIFF comprimidos.

Salidas:
    data/ghsl/ven/built_{año}.tif, pop_{año}.tif, mask_estados.tif
    output/p03_nacional.json   superficie construida, población, m²/hab por época

Uso:
    python -P prepare.py
"""

import json
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.merge import merge
from rasterio.transform import from_origin
from shapely.geometry import mapping, shape
from shapely.ops import transform as shp_transform

ROOT = Path(__file__).resolve().parents[1]
GHSL = ROOT / "data" / "ghsl"
VEN = GHSL / "ven"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
ADM1 = ROOT / "data" / "boundaries" / "gb-VEN-ADM1.geojson"
OUT = Path(__file__).resolve().parent / "output"
EPOCHS = list(range(1975, 2021, 5))
OBSERVADAS = {1975, 1990, 2000}  # épocas de 100 m que coinciden con observaciones (2014 y 2018 caen cerca de 2015 y 2020)
CRS = "ESRI:54009"


def load_polys(path: Path) -> list[tuple[str, object]]:
    to_moll = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform
    feats = json.loads(path.read_text(encoding="utf-8"))["features"]
    return [(f["properties"].get("shapeName", ""), shp_transform(to_moll, shape(f["geometry"]))) for f in feats]


def grid_for(poly) -> tuple[rasterio.Affine, int, int]:
    xmin, ymin, xmax, ymax = poly.bounds
    xmin, ymax = np.floor(xmin / 100) * 100, np.ceil(ymax / 100) * 100
    xmax, ymin = np.ceil(xmax / 100) * 100, np.floor(ymin / 100) * 100
    return from_origin(xmin, ymax, 100, 100), int((xmax - xmin) / 100), int((ymax - ymin) / 100)


def mosaic(files: list[Path], bounds) -> np.ndarray:
    srcs = [rasterio.open(f) for f in files]
    arr, _ = merge(srcs, bounds=bounds, res=100, nodata=0)
    for s in srcs:
        s.close()
    return arr[0]


def main() -> None:
    VEN.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (_, ven), = load_polys(ADM0)[:1]
    states = load_polys(ADM1)
    transform, width, height = grid_for(ven)
    bounds = (transform.c, transform.f - height * 100, transform.c + width * 100, transform.f)
    mask = rasterize([(mapping(ven), 1)], out_shape=(height, width), transform=transform, dtype="uint8").astype(bool)
    labels = rasterize([(mapping(g), i + 1) for i, (_, g) in enumerate(states)],
                       out_shape=(height, width), transform=transform, dtype="uint8")
    profile = dict(driver="GTiff", width=width, height=height, count=1, crs=CRS, transform=transform,
                   compress="deflate", tiled=True, blockxsize=512, blockysize=512)
    with rasterio.open(VEN / "mask_estados.tif", "w", dtype="uint8", nodata=0, **profile) as dst:
        dst.write(labels, 1)
    (VEN / "estados.json").write_text(json.dumps({i + 1: n for i, (n, _) in enumerate(states)}, ensure_ascii=False),
                                      encoding="utf-8")
    print(f"grilla de Venezuela: {width} x {height} celdas de 100 m · celdas dentro del país: {mask.sum():,} "
          f"({mask.sum() / 100:,.0f} km²)")

    rows = []
    for e in EPOCHS:
        built = mosaic(sorted((GHSL / "BUILT_S" / str(e)).glob("*.tif")), bounds).astype("uint16")
        pop = mosaic(sorted((GHSL / "POP" / str(e)).glob("*.tif")), bounds).astype("float32")
        built[~mask] = 0
        pop[~mask] = 0
        pop[pop < 0] = 0
        with rasterio.open(VEN / f"built_{e}.tif", "w", dtype="uint16", nodata=0, **profile) as dst:
            dst.write(built, 1)
        with rasterio.open(VEN / f"pop_{e}.tif", "w", dtype="float32", nodata=0, **profile) as dst:
            dst.write(pop, 1)
        built_km2 = float(built.sum(dtype="float64")) / 1e6
        pop_total = float(pop.sum(dtype="float64"))
        rows.append({
            "anio": e,
            "observada": e in OBSERVADAS,
            "construido_km2": round(built_km2, 1),
            "poblacion": round(pop_total),
            "m2_construidos_por_habitante": round(built_km2 * 1e6 / pop_total, 1),
            "celdas_con_construccion": int((built > 0).sum()),
        })
        print(rows[-1], flush=True)

    first, last = rows[0], rows[-1]
    years = last["anio"] - first["anio"]
    resumen = {
        "construido_veces_1975_2020": round(last["construido_km2"] / first["construido_km2"], 2),
        "poblacion_veces_1975_2020": round(last["poblacion"] / first["poblacion"], 2),
        "tasa_anual_construido_pct": round(100 * ((last["construido_km2"] / first["construido_km2"]) ** (1 / years) - 1), 2),
        "tasa_anual_poblacion_pct": round(100 * ((last["poblacion"] / first["poblacion"]) ** (1 / years) - 1), 2),
    }
    (OUT / "p03_nacional.json").write_text(json.dumps({"epocas": rows, "resumen": resumen}, indent=2, ensure_ascii=False),
                                           encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
