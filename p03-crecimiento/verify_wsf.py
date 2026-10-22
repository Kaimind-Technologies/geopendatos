"""P03 · Verificación independiente del "salto de los 90" del GHSL con WSF-Evolution.

WSF-Evolution (DLR, Marconcini et al.) marca cada píxel de ~30 m con el año en que
se detectó por primera vez como asentamiento (1985-2015), a partir de Landsat 5/7.
Es independiente del GHSL: otro algoritmo, otra resolución, otra definición
(extensión de asentamiento, no m² de techos). Si también muestra una aceleración en
1990-2000, el hallazgo se sostiene; si no, el salto del GHSL puede ser un artefacto.

Pasos:
  1. Descarga los tiles de 2°x2° que cubren Venezuela (data/wsf_evo/, fuera del repo).
  2. Recorta con el polígono del país y de los estados (geoBoundaries, EPSG:4326).
  3. Suma el área real de los píxeles (depende de la latitud) por año de detección.
  4. Compara tasas anuales 1985-1990, 1990-2000, 2000-2015 con las del GHSL.

Licencia WSF-Evolution: CC BY 4.0 (DLR).

Salida: output/p03_verificacion_wsf.json

Uso:
    python -P verify_wsf.py
"""

import json
import math
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "wsf_evo"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
ADM1 = ROOT / "data" / "boundaries" / "gb-VEN-ADM1.geojson"
OUT = Path(__file__).resolve().parent / "output"
BASE = "https://download.geoservice.dlr.de/WSF_EVO/files"
R = 6_371_008.8  # radio terrestre medio (m)
YEARS = list(range(1985, 2016))


def download() -> list[Path]:
    DEST.mkdir(parents=True, exist_ok=True)
    files = []
    for lon in range(-74, -59, 2):
        for lat in range(0, 13, 2):
            f = DEST / f"WSFevolution_v1_{lon}_{lat}.tif"
            if not f.exists():
                try:
                    f.write_bytes(urllib.request.urlopen(f"{BASE}/{f.name}", timeout=300).read())
                    print(f"descargado {f.name} ({f.stat().st_size / 1e6:.1f} MB)", flush=True)
                except urllib.error.HTTPError as err:
                    print(f"{f.name}: HTTP {err.code} (sin tile)")
                    continue
            files.append(f)
    return files


def row_areas(src) -> np.ndarray:
    """Área (m²) de un píxel en cada fila: R² · Δλ · (sin φ_norte − sin φ_sur)."""
    t = src.transform
    dlon = math.radians(abs(t.a))
    lat_top = t.f + np.arange(src.height) * t.e
    lat_bot = lat_top + t.e
    return R ** 2 * dlon * np.abs(np.sin(np.radians(lat_top)) - np.sin(np.radians(lat_bot)))


def main() -> None:
    files = download()
    ven = shape(json.loads(ADM0.read_text(encoding="utf-8"))["features"][0]["geometry"])
    states = [(f["properties"]["shapeName"], shape(f["geometry"]))
              for f in json.loads(ADM1.read_text(encoding="utf-8"))["features"]]
    nacional = np.zeros(len(YEARS))
    por_estado = {n: np.zeros(len(YEARS)) for n, _ in states}
    for f in files:
        with rasterio.open(f) as src:
            if not ven.intersects(box(*src.bounds)):
                continue
            a = src.read(1)
            labels = rasterize([(mapping(g), i + 1) for i, (_, g) in enumerate(states) if g.intersects(box(*src.bounds))],
                               out_shape=a.shape, transform=src.transform, dtype="uint8")
            areas = np.broadcast_to(row_areas(src)[:, None], a.shape)
            inside = (labels > 0) & (a >= 1985)
            yr, lab, ar = a[inside], labels[inside], areas[inside]
            for k, y in enumerate(YEARS):
                sel = yr == y
                nacional[k] += ar[sel].sum()
                if sel.any():
                    sums = np.bincount(lab[sel], weights=ar[sel], minlength=len(states) + 1)
                    for i, (n, _) in enumerate(states):
                        por_estado[n][k] += sums[i + 1]

    cum = np.cumsum(nacional) / 1e6  # km² acumulados de asentamiento
    acum = {y: round(float(c), 1) for y, c in zip(YEARS, cum)}

    def tasa(serie: dict, a: int, b: int) -> float:
        return round(100 * math.log(serie[b] / serie[a]) / (b - a), 2)

    ghsl = {e["anio"]: e["construido_km2"] for e in
            json.loads((OUT / "p03_nacional.json").read_text(encoding="utf-8"))["epocas"]}
    comparacion = []
    for a, b in ((1985, 1990), (1990, 2000), (2000, 2015), (1990, 1995), (1995, 2000)):
        comparacion.append({
            "periodo": f"{a}-{b}",
            "wsf_asentamiento_pct_anual": tasa(acum, a, b),
            "ghsl_construido_pct_anual": tasa(ghsl, a, b),
            "wsf_km2_nuevos": round(acum[b] - acum[a], 1),
        })
    estados = {}
    for n, s in por_estado.items():
        c = np.cumsum(s) / 1e6
        serie = {y: float(v) for y, v in zip(YEARS, c)}
        if serie[1985] > 0:
            estados[n] = {"km2_1985": round(serie[1985], 1), "km2_2015": round(serie[2015], 1),
                          "pct_anual_85_90": tasa(serie, 1985, 1990), "pct_anual_90_00": tasa(serie, 1990, 2000),
                          "pct_anual_00_15": tasa(serie, 2000, 2015)}
    res = {"wsf_km2_acumulados_por_anio": acum, "comparacion_nacional": comparacion, "por_estado": estados}
    (OUT / "p03_verificacion_wsf.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nWSF-Evolution, superficie de asentamiento en Venezuela: {acum[1985]} km² (1985) → {acum[2015]} km² (2015)")
    print(f"{'período':12}{'WSF %/año':>12}{'GHSL %/año':>12}{'WSF km² nuevos':>16}")
    for c in comparacion:
        print(f"{c['periodo']:12}{c['wsf_asentamiento_pct_anual']:>12}{c['ghsl_construido_pct_anual']:>12}{c['wsf_km2_nuevos']:>16}")
    acel = sum(1 for e in estados.values() if e["pct_anual_90_00"] > max(e["pct_anual_85_90"], e["pct_anual_00_15"]))
    print(f"estados donde 1990-2000 es el período de mayor crecimiento WSF: {acel} de {len(estados)}")


if __name__ == "__main__":
    main()
