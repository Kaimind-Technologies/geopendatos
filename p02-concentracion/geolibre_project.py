"""Genera el proyecto de GeoLibre de P02 (Time Slider acumulativo de la concentración).

Parte de un estado real exportado de GeoLibre 3.4.0 (geolibre/plantilla_estado_geolibre.json,
obtenido con el puente de embed) y configura:
- capa hex_r7_ranking: color graduado (paleta magma) y extrusión 3D por número de construcciones,
- Time Slider ligado al campo `anio` (1901-2000 = 1%-100% acumulado), en modo acumulativo,
- mapa base oscuro (CARTO dark-matter) y cámara inclinada sobre Venezuela.

Uso:
    python -P geolibre_project.py --base http://localhost:8766/p02-concentracion   (pruebas)
    python -P geolibre_project.py --base https://raw.githubusercontent.com/Kaimind-Technologies/venezuela-datos-abiertos/main/p02-concentracion
"""

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "geolibre" / "plantilla_estado_geolibre.json"
OUT = HERE / "geolibre" / "p02_concentracion.geolibre.json"
DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

MAGMA = [(1, "#3b0f70"), (50, "#721f81"), (300, "#b73779"), (1500, "#f1605d"), (5000, "#feb078"), (15000, "#fcfdbf")]


def year_ms(year: int) -> int:
    return int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="URL base donde está output/hex_r7_ranking.parquet")
    args = parser.parse_args()

    st = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    project = copy.deepcopy(st)
    project["name"] = "Kaimind · La Venezuela concentrada (P02)"
    project["basemapStyleUrl"] = DARK
    project["mapView"] = {"center": [-66.1, 7.2], "zoom": 5.65, "bearing": -10, "pitch": 35}  # encuadre vertical 1080x1350

    layer = project["layers"][0]
    layer["name"] = "Construcciones por hexágono (~5 km²)"
    layer["sourcePath"] = f"{args.base}/output/hex_r7_ranking.parquet"
    if isinstance(layer.get("source"), dict) and "url" in layer["source"]:
        layer["source"]["url"] = layer["sourcePath"]

    color_expr = ["interpolate", ["linear"], ["get", "construcciones"], *[v for stop in MAGMA for v in stop]]
    style = layer["style"]
    style.update({
        "vectorStyleMode": "graduated",
        "vectorStyleProperty": "construcciones",
        "vectorStyleStops": [{"value": v, "color": c} for v, c in MAGMA],
        "fillColor": "#f1605d",
        "fillOpacity": 0.9,
        "strokeWidth": 0,
        "extrusionEnabled": True,
        "extrusionAdvancedStyleEnabled": True,
        "extrusionColorExpression": json.dumps(color_expr),
        "extrusionHeightExpression": json.dumps(["*", ["sqrt", ["get", "construcciones"]], 250]),
        "extrusionOpacity": 0.92,
    })
    project.setdefault("styles", {})[layer["id"]] = style

    layer["metadata"]["timeBinding"] = {
        "property": "anio",
        "valueKind": "year",
        "min": year_ms(1901),
        "max": year_ms(2000),
        "granularity": "year",
        "window": {"unit": "year", "before": 0, "after": 1},
        "cumulative": True,
    }
    plugins = project.setdefault("plugins", {})
    active = plugins.setdefault("activePluginIds", [])
    if "maplibre-gl-time-slider" not in active:
        active.append("maplibre-gl-time-slider")
    # Rango de la línea de tiempo: 1901-2000 = 1%-100% acumulado de construcciones.
    ts = plugins.setdefault("settings", {}).setdefault("maplibre-gl-time-slider", {})
    ts.update({
        "startDate": "1901-01-01T00:00:00.000Z",
        "endDate": "2000-01-01T00:00:00.000Z",
        "currentDate": "1901-01-01T00:00:00.000Z",
        "interval": 1,
        "granularity": "year",
        "granularities": ["year"],
        "speed": 200,
        "loop": False,
        "autoPlay": False,
        "collapsed": False,
        "theme": "dark",
    })

    OUT.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    print("proyecto:", OUT)


if __name__ == "__main__":
    main()
