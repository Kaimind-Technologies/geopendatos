"""Genera los proyectos de GeoLibre de P03 (Time Slider con años reales 1985-2015, WSF).

  geolibre/p03_video.geolibre.json     cámara del video (eje central, más cerca)
  geolibre/p03_explorar.geolibre.json  cámara para explorar (eje central, más abierta)

Las dos tienen las mismas capas: hexágonos res 8 con el año de urbanización (Time Slider)
y contornos celestes en las celdas de ~5 km² que suman la mitad del crecimiento 2000-2015 (WSF).

Parte del estado real de GeoLibre 3.4.0 capturado en P02 (plantilla con el puente embed).
Colores: lo que ya era asentamiento en 1985 en verde azulado; lo nuevo, de fucsia (1986) a
amarillo (2015). Debajo, el país (fondo azul y contorno claro) y los límites de los estados. Altura 3D según el % del hexágono que es asentamiento en 2015.

Uso:
    python -P geolibre_project.py --base http://localhost:8766/p03-crecimiento   (pruebas)
    python -P geolibre_project.py --base https://raw.githubusercontent.com/Kaimind-Technologies/venezuela-datos-abiertos/main/p03-crecimiento
"""

import argparse
import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "p02-concentracion" / "geolibre" / "plantilla_estado_geolibre.json"
GEO = HERE / "geolibre"
DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

# Ya existía en 1985: verde azulado (paleta Kaimind). Lo nuevo: de fucsia (1986) a amarillo (2015).
COLOR_ANIO = ["case", ["<=", ["get", "anio"], 1985], "#3f8f87",
              ["interpolate", ["linear"], ["get", "anio"],
               1986, "#c026d3", 1995, "#f43f5e", 2005, "#fb923c", 2015, "#fde047"]]


def year_ms(y: int) -> int:
    return int(datetime(y, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def base_project(name: str, view: dict) -> tuple[dict, dict]:
    st = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    p = copy.deepcopy(st)
    p["name"] = name
    p["basemapStyleUrl"] = DARK
    p["mapView"] = view
    layer_tpl = p["layers"][0]
    p["layers"], p["styles"] = [], {}
    ts = p["plugins"].setdefault("settings", {}).setdefault("maplibre-gl-time-slider", {})
    ts.update({"startDate": "1985-01-01T00:00:00.000Z", "endDate": "2015-01-01T00:00:00.000Z",
               "currentDate": "1985-01-01T00:00:00.000Z", "interval": 1, "granularity": "year",
               "granularities": ["year"], "speed": 400, "loop": False, "autoPlay": False,
               "collapsed": False, "theme": "dark"})
    if "maplibre-gl-time-slider" not in p["plugins"]["activePluginIds"]:
        p["plugins"]["activePluginIds"].append("maplibre-gl-time-slider")
    return p, layer_tpl


def add_layer(p: dict, tpl: dict, name: str, url: str, fields: list[str], count: int, style: dict,
              time_bound: bool) -> None:
    layer = copy.deepcopy(tpl)
    layer["id"] = str(uuid.uuid4())
    layer["name"] = name
    layer["sourcePath"] = url
    if isinstance(layer.get("source"), dict):
        layer["source"]["url"] = url
    layer["style"].update(style)
    md = layer["metadata"]
    md["fields"], md["featureCount"] = fields, count
    md.pop("bounds", None)
    if time_bound:
        md["timeBinding"] = {"property": "anio", "valueKind": "year", "min": year_ms(1985), "max": year_ms(2015),
                             "granularity": "year", "window": {"unit": "year", "before": 0, "after": 1},
                             "cumulative": True}
    else:
        md.pop("timeBinding", None)
    p["layers"].append(layer)
    p["styles"][layer["id"]] = layer["style"]


def slider_style(height_factor: float) -> dict:
    return {
        "vectorStyleMode": "single", "fillColor": "#f0614a", "fillOpacity": 0.9, "strokeWidth": 0,
        "extrusionEnabled": True, "extrusionAdvancedStyleEnabled": True, "extrusionOpacity": 0.92,
        "extrusionColorExpression": json.dumps(COLOR_ANIO),
        "extrusionHeightExpression": json.dumps(["*", ["sqrt", ["get", "asentamiento_2015_pct"]], height_factor]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    args = ap.parse_args()
    GEO.mkdir(exist_ok=True)
    con = duckdb.connect()
    cnt = lambda f, w="": con.execute(f"SELECT count(*) FROM read_parquet('{(HERE / 'output' / f).as_posix()}') {w}").fetchone()[0]

    # Mismo contenido para el video y para explorar: eje central (Valencia-Maracay-Caracas), donde se
    # concentra el crecimiento. A escala nacional el crecimiento (4.400 km² en 916.000) se ve como puntos sueltos.
    vistas = {
        "p03_video.geolibre.json": {"center": [-67.45, 10.3], "zoom": 8.75, "bearing": -12, "pitch": 55},
        "p03_explorar.geolibre.json": {"center": [-67.55, 10.25], "zoom": 8.4, "bearing": -15, "pitch": 50},
    }
    for fname, view in vistas.items():
        proj, tpl = base_project("Kaimind · Así crecieron las ciudades de Venezuela, 1985-2015 (P03)", view)
        # Contexto: el país (fondo y contorno) y sus estados, debajo de los hexágonos.
        add_layer(proj, tpl, "Venezuela", f"{args.base}/output/ven_contorno.parquet", ["nombre"],
                  cnt("ven_contorno.parquet"),
                  {"vectorStyleMode": "single", "fillColor": "#1F2AA5", "fillOpacity": 0.28, "strokeColor": "#e5e7eb",
                   "strokeWidth": 2.5, "extrusionEnabled": False}, False)
        add_layer(proj, tpl, "Estados", f"{args.base}/output/ven_estados.parquet", ["nombre"], cnt("ven_estados.parquet"),
                  {"vectorStyleMode": "single", "fillColor": "#000000", "fillOpacity": 0, "strokeColor": "#64748b",
                   "strokeWidth": 1, "extrusionEnabled": False}, False)
        add_layer(proj, tpl, "La mitad del crecimiento 2000-2015 (~5 km²)", f"{args.base}/output/hex_r7_mitad_crecimiento.parquet",
                  ["h3", "nuevo_wsf_m2", "nuevo_ghsl_m2", "tambien_en_ghsl"], cnt("hex_r7_mitad_crecimiento.parquet"),
                  {"vectorStyleMode": "single", "fillColor": "#22d3ee", "fillOpacity": 0.14, "strokeColor": "#67e8f9",
                   "strokeWidth": 2.5, "extrusionEnabled": False}, False)
        add_layer(proj, tpl, "Asentamiento por año (~0,74 km²)", f"{args.base}/output/hex_r8_urbanizacion_wsf.parquet",
                  ["h3", "anio", "asentamiento_2015_pct"], cnt("hex_r8_urbanizacion_wsf.parquet"), slider_style(600), True)
        (GEO / fname).write_text(json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("proyectos:", [f.name for f in GEO.glob("*.geolibre.json")])


if __name__ == "__main__":
    main()
