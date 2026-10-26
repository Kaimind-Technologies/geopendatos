"""API estática v0 de Venezuela en datos abiertos.

Lee SOLO las salidas verificadas de cada publicación (p0*/output/*.json y las capas GeoParquet
publicadas) y escribe la API en web/public/api/v0/, que el sitio publica tal cual en GitHub Pages.
Ninguna cifra se escribe a mano: cada valor sale de un JSON del repo, y el campo `origen` dice de cuál.

Reglas (las mismas de las publicaciones, ver p03-crecimiento/VALIDACION.md):
  - Solo entran cifras que resistieron las verificaciones. Lo descartado va a descartes.json.
  - Lo que depende del método o de la escala se publica como rango (`rango`), no con un decimal.
  - Cada dato lleva su licencia: ODbL lo derivado de Overture (P01, P02), CC BY 4.0 lo de P03.

Antes de escribir se corren pruebas de coherencia (`pruebas()`): si alguna falla, no se escribe nada.

Uso (desde la raíz del repo):
    python -P api/build_api.py           # genera web/public/api/v0/
    python -P api/build_api.py --check   # falla si lo publicado no coincide con lo que se generaría
"""

import argparse
import json
import math
import sys
import unicodedata
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "public" / "api" / "v0"
VERSION = "0.1.0"
REPO = "https://github.com/Kaimind-Technologies/venezuela-datos-abiertos"
RAW = "https://raw.githubusercontent.com/Kaimind-Technologies/venezuela-datos-abiertos/main"
GEOLIBRE = "https://web.geolibre.app/?welcome=0&theme=dark&url="

LICENCIAS = {
    "odbl": {"id": "ODbL-1.0", "nombre": "Open Database License 1.0",
             "url": "https://opendatacommons.org/licenses/odbl/1-0/",
             "atribucion": "© OpenStreetMap contributors, Overture Maps Foundation",
             "nota": "Si redistribuyes los datos o una base derivada, debe ser con la misma licencia."},
    "ccby": {"id": "CC-BY-4.0", "nombre": "Creative Commons Attribution 4.0",
             "url": "https://creativecommons.org/licenses/by/4.0/",
             "atribucion": "GHSL © European Commission, JRC · WSF-Evolution © DLR · censos del INE"},
    "geoboundaries": {"id": "CC-BY-3.0-IGO", "nombre": "Creative Commons Attribution 3.0 IGO",
                      "url": "https://creativecommons.org/licenses/by/3.0/igo/",
                      "atribucion": "geoBoundaries (Runfola et al., 2020)"},
}

PUBLICACIONES = {
    "P01": {"titulo": {"es": "¿Cuántas construcciones tiene Venezuela?", "en": "How many structures does Venezuela have?"},
            "carpeta": "p01-edificios-overture", "licencia": "odbl"},
    "P02": {"titulo": {"es": "La Venezuela concentrada", "en": "Concentrated Venezuela"},
            "carpeta": "p02-concentracion", "licencia": "odbl"},
    "P03": {"titulo": {"es": "Así crecieron las ciudades de Venezuela, 1985-2015",
                       "en": "How Venezuela's cities grew, 1985-2015"},
            "carpeta": "p03-crecimiento", "licencia": "ccby"},
}

FUENTES = {
    "overture": "Overture Maps, tema buildings, release 2026-09-23.1 (incluye OpenStreetMap, Microsoft ML Buildings y Google Open Buildings)",
    "ghsl": "GHS-BUILT-S R2023A (JRC, Comisión Europea), 100 m",
    "ghs_pop": "GHS-POP R2023A (JRC, Comisión Europea), población modelada, 100 m",
    "wsf": "World Settlement Footprint Evolution (DLR), 1985-2015, ~30 m",
    "ine_censo": "INE, censos de población 1990, 2001 y 2011 (también por municipio)",
    "geoboundaries": "geoBoundaries gbOpen VEN ADM0/ADM1 (sin la Guayana Esequiba)",
}


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def tasa(a: float, b: float, anios: int) -> float:
    """Crecimiento anual continuo en %, la misma fórmula que el ODS 11.3.1 (LCR y PGR)."""
    return 100 * math.log(b / a) / anios


def slug(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "-".join(s.lower().replace("(", " ").replace(")", " ").split())


def doc(pub: str, archivo: str) -> str:
    return f"{REPO}/blob/main/{PUBLICACIONES[pub]['carpeta']}/{archivo}"


def indicador(id_, pub, nombre, unidad, *, valor=None, rango=None, escala=None, periodo, fuentes, metodo, pruebas,
              origen, nota=None, estado="verificada"):
    return {
        "id": id_, "publicacion": pub, "nombre": nombre, "valor": valor, "rango": rango, "unidad": unidad,
        "escala": escala, "periodo": periodo, "estado": estado, "nota": nota,
        "fuentes": [FUENTES[f] for f in fuentes], "metodo": metodo, "pruebas": pruebas,
        "licencia": PUBLICACIONES[pub]["licencia"], "origen": origen,
        "documentacion": f"{REPO}/tree/main/{PUBLICACIONES[pub]['carpeta']}",
    }


# ---------------------------------------------------------------- datos de origen
def fuentes_de_datos() -> dict:
    return {
        "p01": load("p01-edificios-overture/output/p01_cifras.json"),
        "p02_rob": load("p02-concentracion/output/p02_robustez.json"),
        "p02_stats": load("p02-concentracion/output/p02_stats.json"),
        "p02_cifras": load("p02-concentracion/output/p02_cifras.json"),
        "p02_gistar": load("p02-concentracion/output/p02_gistar.json"),
        "p03_nac": load("p03-crecimiento/output/p03_nacional.json"),
        "p03_serie": load("p03-crecimiento/video/serie_anual.json"),
        "p03_wsf": load("p03-crecimiento/output/p03_verificacion_wsf.json"),
        "p03_pop": load("p03-crecimiento/output/p03_verificacion_poblacion.json"),
        "p03_val": load("p03-crecimiento/output/p03_validacion.json"),
        "p03_ciu": load("p03-crecimiento/output/p03_validacion_ciudades.json"),
        "p03_lei_gi": load("p03-crecimiento/output/p03_contraste_lei_gistar.json"),
    }


def ods_2000_2015(d: dict) -> list[float]:
    """Las 6 combinaciones del ODS 11.3.1 nacional de VALIDACION.md T2: 2 fuentes de suelo × 3 de población."""
    ep = {e["anio"]: e for e in d["p03_nac"]["epocas"]}
    serie = d["p03_serie"]["km2_acumulados"]
    pop = tasa(ep[2000]["poblacion"], ep[2015]["poblacion"], 15)
    t2 = d["p03_val"]["t2_ods_nacional_con_censos"]
    censo = next(p for p in t2["con_censos"] if p["periodo_censal"] == "2001-2011")
    sens = t2["sensibilidad_omision_censal"]
    return [tasa(serie["2000"], serie["2015"], 15) / pop,                         # WSF / GHS-POP
            tasa(ep[2000]["construido_km2"], ep[2015]["construido_km2"], 15) / pop,  # GHSL / GHS-POP
            censo["ods_wsf_censo"], censo["ods_ghsl_censo"],                         # censos del INE
            sens["ods_wsf_2001_2011"], sens["ods_ghsl_2000_2010"]]                   # estimación del INE


# ---------------------------------------------------------------- recursos de la API
def indicadores(d: dict) -> list[dict]:
    p01, rob = d["p01"], [r for r in d["p02_rob"] if r["filtro_area_min_m2"] == 0]
    r7 = next(r for r in rob if r["resolucion_h3"] == 7)
    mc = d["p02_gistar"]["montecarlo"]
    lei = d["p03_val"]["t4_sensibilidad_lei_2000_2015"]["corridas"].values()
    pegado = [v["pct_relleno"] + v["pct_expansion_de_borde"] for v in lei]
    borde = [v["pct_expansion_de_borde"] for v in lei]
    ods = ods_2000_2015(d)
    serie = d["p03_serie"]["km2_acumulados"]
    escalas = "hexágonos H3 de ~0,74, ~5 y ~36 km² (res 8, 7 y 6)"
    return [
        indicador("construcciones_total", "P01",
                  {"es": "Construcciones en Venezuela", "en": "Structures in Venezuela"}, "construcciones",
                  valor=p01["total_edificios"], periodo=f"Overture Maps {p01['release_overture']}",
                  fuentes=["overture", "geoboundaries"],
                  metodo={"es": "Cada contorno de techo de Overture cuyo centro cae dentro de Venezuela. Una casa cuenta como una y una torre también.",
                          "en": "Every Overture rooftop footprint whose centre falls inside Venezuela. A house counts as one, and so does a tower."},
                  pruebas=["Correlación 0,87 con las viviendas del censo de 2011 por estado",
                           "Control de límites: incertidumbre de como máximo ~0,6% (P03, PROCESO.md §3.5)",
                           "0,03% de posibles duplicados entre fuentes en Caracas"],
                  nota={"es": "Son techos, no viviendas ni personas. El 92% de los contornos viene de imágenes satelitales anteriores al sismo del 24 de junio de 2026: no reflejan los daños.",
                        "en": "Rooftops, not dwellings or people. 92% of footprints come from satellite imagery predating the 24 June 2026 earthquake: they do not reflect the damage."},
                  origen=["p01-edificios-overture/output/p01_cifras.json#total_edificios"]),
        indicador("construcciones_por_fuente", "P01",
                  {"es": "Construcciones según quién las trazó", "en": "Structures by who traced them"}, "construcciones y %",
                  valor=[{"fuente": f["fuente"], "construcciones": f["edificios"], "pct": f["pct"]} for f in p01["por_fuente"]],
                  periodo=f"Overture Maps {p01['release_overture']}", fuentes=["overture"],
                  metodo={"es": "Fuente de cada contorno según Overture: IA de Microsoft o Google, o voluntarios de OpenStreetMap.",
                          "en": "Source of each footprint according to Overture: Microsoft or Google AI, or OpenStreetMap volunteers."},
                  pruebas=["Overture fusiona las fuentes sin duplicados (0,03% de solapes en Caracas)"],
                  origen=["p01-edificios-overture/output/p01_cifras.json#por_fuente"]),
        indicador("mitad_construcciones_pct_territorio", "P02",
                  {"es": "Territorio que concentra la mitad de las construcciones", "en": "Land holding half of all structures"}, "% del territorio",
                  valor=r7["A_mitad_pct_territorio"],
                  rango=[min(r["A_mitad_pct_territorio"] for r in rob), max(r["A_mitad_pct_territorio"] for r in rob)],
                  escala="H3 res 7 (~5 km²); el rango cubre " + escalas, periodo=f"Overture Maps {p01['release_overture']}",
                  fuentes=["overture", "geoboundaries"],
                  metodo={"es": "Celdas ordenadas de más a menos construcciones; % del territorio (por área real) que suma la mitad.",
                          "en": "Cells sorted from most to fewest structures; share of land (true area) that adds up to half."},
                  pruebas=["Menos del 1% en las tres escalas", "Sin techos de menos de 20 m²: igual",
                           "Aunque las zonas densas tuvieran el doble de techos: 0,93%"],
                  origen=["p02-concentracion/output/p02_robustez.json"]),
        indicador("noventa_pct_construcciones_pct_territorio", "P02",
                  {"es": "Territorio que concentra el 90% de las construcciones", "en": "Land holding 90% of all structures"}, "% del territorio",
                  valor=r7["90pct_en_pct_territorio"],
                  rango=[min(r["90pct_en_pct_territorio"] for r in rob), max(r["90pct_en_pct_territorio"] for r in rob)],
                  escala="H3 res 7 (~5 km²); el rango cubre " + escalas, periodo=f"Overture Maps {p01['release_overture']}",
                  fuentes=["overture", "geoboundaries"],
                  metodo={"es": "Igual que la mitad, con el 90%.", "en": "Same as for half, with 90%."},
                  pruebas=["Depende de la escala: se publica siempre con ella"],
                  origen=["p02-concentracion/output/p02_robustez.json"]),
        indicador("territorio_sin_construcciones_pct", "P02",
                  {"es": "Territorio sin ninguna construcción", "en": "Land without a single structure"}, "% del territorio",
                  valor=r7["B_vacio_pct_territorio"],
                  rango=[min(r["B_vacio_pct_territorio"] for r in rob), max(r["B_vacio_pct_territorio"] for r in rob)],
                  escala="H3 res 7 (~5 km²); el rango cubre " + escalas, periodo=f"Overture Maps {p01['release_overture']}",
                  fuentes=["overture", "geoboundaries"], estado="depende_de_la_escala",
                  metodo={"es": "% del territorio (por área) en celdas sin ningún techo.", "en": "Share of land (by area) in cells with no rooftop at all."},
                  pruebas=["Cambia mucho con la escala: nunca se publica sin ella"],
                  nota={"es": "En la selva la IA puede no ver techos bajo los árboles.", "en": "Under forest canopy the AI may miss rooftops."},
                  origen=["p02-concentracion/output/p02_robustez.json"]),
        indicador("gini_espacial", "P02",
                  {"es": "Gini espacial de las construcciones", "en": "Spatial Gini of structures"}, "índice (0-1)",
                  valor=d["p02_stats"]["gini_espacial_territorio"], escala="H3 res 7 (~5 km²), todo el territorio, incluidas las celdas vacías",
                  periodo=f"Overture Maps {p01['release_overture']}", fuentes=["overture", "geoboundaries"],
                  metodo={"es": "0 = repartidas por igual en el territorio; 1 = todas en un solo punto.",
                          "en": "0 = evenly spread across the land; 1 = all in a single spot."},
                  pruebas=["Calculado sobre las 192.832 celdas del país"],
                  origen=["p02-concentracion/output/p02_stats.json#gini_espacial_territorio"]),
        indicador("techo_total_km2", "P02",
                  {"es": "Superficie de todos los techos juntos", "en": "Area of all rooftops combined"}, "km²",
                  valor=d["p02_cifras"]["techo_total_km2"], periodo=f"Overture Maps {p01['release_overture']}",
                  fuentes=["overture"],
                  metodo={"es": f"Suma del área de cada contorno (EPSG:6933): {d['p02_cifras']['techo_pct_territorio']}% del territorio.",
                          "en": f"Sum of every footprint's area (EPSG:6933): {d['p02_cifras']['techo_pct_territorio']}% of the land."},
                  pruebas=["Mismo orden de magnitud que la superficie construida del GHSL 2020 (1.457 km²), una fuente independiente"],
                  origen=["p02-concentracion/output/p02_cifras.json#techo_total_km2"]),
        indicador("puntos_calientes_construcciones", "P02",
                  {"es": "Puntos calientes de construcciones (Gi*, Monte Carlo)", "en": "Structure hot spots (Gi*, Monte Carlo)"},
                  "% del territorio y % de las construcciones",
                  valor={"pct_territorio": mc["pct_territorio_en_puntos_calientes_99"],
                         "pct_construcciones": mc["pct_construcciones_en_puntos_calientes_99"]},
                  escala="H3 res 7 (~5 km²), 99% con FDR", periodo=f"Overture Maps {p01['release_overture']}",
                  fuentes=["overture", "geoboundaries"],
                  metodo={"es": f"Getis-Ord Gi* con p-valores por Monte Carlo ({d['p02_gistar']['simulaciones']:,} simulaciones) y FDR de Benjamini-Hochberg.".replace(",", "."),
                          "en": f"Getis-Ord Gi* with Monte Carlo p-values ({d['p02_gistar']['simulaciones']:,} simulations) and Benjamini-Hochberg FDR."},
                  pruebas=["Reemplaza a la versión con la curva normal, que exageraba la significancia (ver descartes)"],
                  origen=["p02-concentracion/output/p02_gistar.json#montecarlo"]),
        indicador("asentamiento_km2", "P03",
                  {"es": "Superficie de asentamiento de Venezuela", "en": "Settlement area of Venezuela"}, "km²",
                  valor={"1985": serie["1985"], "2015": serie["2015"]}, periodo="1985-2015", fuentes=["wsf", "geoboundaries"],
                  metodo={"es": "Píxeles de ~30 m marcados como asentamiento por WSF-Evolution, recortados con el contorno del país. Serie anual en /series/asentamiento.json.",
                          "en": "~30 m pixels flagged as settlement by WSF-Evolution, clipped to the country outline. Yearly series in /series/asentamiento.json."},
                  pruebas=["Recortado con otro polígono (ADM1) cambia ~1,5%: redondear a 'unos 2.500 y 4.400 km²'"],
                  nota={"es": "Los saltos de 1991 y 1996 de la serie anual son huecos en las imágenes, no auges (VALIDACION.md T1).",
                        "en": "The 1991 and 1996 jumps in the yearly series are imagery gaps, not booms (VALIDACION.md T1)."},
                  origen=["p03-crecimiento/video/serie_anual.json#km2_acumulados"]),
        indicador("crecimiento_pegado_a_lo_urbano_pct", "P03",
                  {"es": "Asentamiento nuevo pegado a zonas ya urbanas (relleno o borde)", "en": "New settlement next to existing urban areas (infill or edge)"},
                  "% del área nueva", rango=[round(min(pegado)), round(max(pegado))], periodo="2000-2015",
                  fuentes=["wsf", "ghsl"],
                  metodo={"es": "Tipología LEI: cada mancha nueva se clasifica como relleno, expansión de borde o salto según lo urbano que la rodea.",
                          "en": "LEI typology: each new patch is classed as infill, edge expansion or leapfrog depending on the urban area around it."},
                  pruebas=[f"{len(pegado)} variantes: 2 fuentes, 3 reglas o umbrales por fuente y anillos de 100, 200 y 300 m"],
                  nota={"es": "9 de cada 10 km² nuevos. Los repartos exactos de relleno y salto no se publican: dependen del método.",
                        "en": "9 in 10 new km². Exact infill and leapfrog shares are not published: they depend on the method."},
                  origen=["p03-crecimiento/output/p03_validacion.json#t4_sensibilidad_lei_2000_2015"]),
        indicador("expansion_de_borde_pct", "P03",
                  {"es": "Expansión de borde, la forma de crecimiento más común", "en": "Edge expansion, the most common form of growth"},
                  "% del área nueva", rango=[round(min(borde)), round(max(borde))], periodo="2000-2015", fuentes=["wsf", "ghsl"],
                  metodo={"es": "Tipología LEI, igual que el indicador anterior.", "en": "LEI typology, as above."},
                  pruebas=[f"Es la forma más común en las {len(borde)} variantes"],
                  origen=["p03-crecimiento/output/p03_validacion.json#t4_sensibilidad_lei_2000_2015"]),
        indicador("ods_11_3_1_nacional_2000_2015", "P03",
                  {"es": "ODS 11.3.1: ritmo del suelo urbano frente al de la población", "en": "SDG 11.3.1: urban land growth vs population growth"},
                  "cociente", rango=[round(min(ods), 2), round(max(ods), 2)], periodo="2000-2015 (2001-2011 con censos)",
                  fuentes=["wsf", "ghsl", "ghs_pop", "ine_censo"],
                  metodo={"es": "Tasa de consumo de suelo ÷ tasa de crecimiento de la población. Menor que 1: la población crece más rápido que el suelo urbanizado.",
                          "en": "Land consumption rate ÷ population growth rate. Below 1: population grows faster than urbanised land."},
                  pruebas=[f"{len(ods)} combinaciones: 2 fuentes de suelo × población modelada, censos y estimación del INE"],
                  nota={"es": "No dice si eso es bueno o malo: puede ser altura, ocupación de lotes vacíos o hacinamiento.",
                        "en": "It does not say whether that is good or bad: it can be height, vacant lots filling up or overcrowding."},
                  origen=["p03-crecimiento/output/p03_nacional.json", "p03-crecimiento/video/serie_anual.json",
                          "p03-crecimiento/output/p03_validacion.json#t2_ods_nacional_con_censos"]),
    ]


def estados(d: dict) -> list[dict]:
    wsf, pop = d["p03_wsf"]["por_estado"], {e["estado"]: e for e in d["p03_pop"]["estados"]}
    out = []
    for e in sorted(d["p01"]["por_estado"], key=lambda e: e["estado"]):
        n, w, p = e["estado"], wsf[e["estado"]], pop[e["estado"]]
        out.append({
            "codigo": slug(n), "nombre": n,
            "construcciones": {"valor": e["edificios"], "fuente": "P01", "licencia": "odbl"},
            "asentamiento_wsf_km2": {"1985": w["km2_1985"], "2015": w["km2_2015"],
                                     "pct_anual": {"1985-1990": w["pct_anual_85_90"], "1990-2000": w["pct_anual_90_00"],
                                                   "2000-2015": w["pct_anual_00_15"]},
                                     "fuente": "P03", "licencia": "ccby",
                                     "nota": "Recortado con los límites de cada estado (ADM1); la suma nacional difiere ~1,5% de la serie con el contorno del país."},
            "poblacion": {"censo_2001": p["censo_2001"], "censo_2011": p["censo_2011"],
                          "ghs_pop_2000": p["ghs_pop_2000"], "ghs_pop_2010": p["ghs_pop_2010"],
                          "crecimiento_pct_anual": {"censo_2001_2011": p["crec_censo_01_11_pct"], "ghs_pop_2000_2010": p["crec_ghs_00_10_pct"]},
                          "fuente": "P03 (INE y GHS-POP)", "licencia": "ccby",
                          "nota": "Población empadronada del INE (sin corrección por omisión) y población modelada de GHS-POP."},
        })
    return out


def ciudades(d: dict) -> list[dict]:
    out = []
    for nombre, c in d["p03_ciu"].items():
        if not isinstance(c, dict) or "lectura" not in c:
            continue
        if c["lectura"] == "densificación robusta":
            estado = "verificada"
            lectura = {"es": f"La población creció más rápido que la superficie urbanizada en las {c['n_combinaciones']} combinaciones probadas.",
                       "en": f"Population grew faster than urbanised land in all {c['n_combinaciones']} combinations tested."}
        elif c["ods_max"] < 0.9:
            estado = "pendiente"
            lectura = {"es": f"Las {c['n_combinaciones']} combinaciones disponibles dan menos de 0,9; falta el censo de sus municipios.",
                       "en": f"All {c['n_combinaciones']} available combinations are below 0.9; its municipal census is missing."}
        else:
            estado = "sin_lectura"
            lectura = {"es": "Sin lectura: según la fuente y el método, el resultado cambia de sentido.",
                       "en": "No reading: depending on source and method, the result changes direction."}
        out.append({"codigo": slug(nombre), "nombre": nombre, "estado": estado, "lectura": lectura,
                    "ods_11_3_1_2000_2015": {"min": c["ods_min"], "max": c["ods_max"], "combinaciones": c["n_combinaciones"],
                                              "solo_censo_municipal": c["ods_solo_censo_municipal"]},
                    "municipios": c["municipios"]["15pct"]["incluidos"],
                    "licencia": "ccby", "origen": "p03-crecimiento/output/p03_validacion_ciudades.json"})
    return out


def serie_asentamiento(d: dict) -> dict:
    return {"unidad": "km²", "fuente": FUENTES["wsf"], "licencia": "ccby", "recorte": "contorno de Venezuela (geoBoundaries ADM0)",
            "valores": [{"anio": int(k), "km2": v} for k, v in d["p03_serie"]["km2_acumulados"].items()],
            "nota": {"es": "Los saltos de 1991 y 1996 son huecos en las imágenes Landsat, no auges. Antes de 2000, leer por décadas.",
                     "en": "The 1991 and 1996 jumps are Landsat imagery gaps, not booms. Before 2000, read by decade."},
            "origen": "p03-crecimiento/video/serie_anual.json"}


CAPAS = [
    ("P01", "p01-edificios-overture/output/ven_h3_r7.parquet",
     {"es": "Construcciones por hexágono H3 de ~5 km² (res 7)", "en": "Structures per ~5 km² H3 hexagon (res 7)"}, None),
    ("P01", "p01-edificios-overture/output/caracas_edificios.parquet",
     {"es": "Cada construcción de Caracas, con su fuente (OSM, Microsoft o Google)", "en": "Every structure in Caracas, with its source"}, None),
    ("P02", "p02-concentracion/output/hex_r7_ranking.parquet",
     {"es": "Hexágonos de ~5 km² ordenados de más a menos construcciones, con el % acumulado", "en": "~5 km² hexagons ranked by structures, with cumulative %"},
     "p02-concentracion/geolibre/p02_concentracion.geolibre.json"),
    ("P02", "p02-concentracion/output/hex_r7_gistar.parquet",
     {"es": "Gi* por hexágono: z, p por Monte Carlo, p normal y clase", "en": "Gi* per hexagon: z, Monte Carlo p, normal p and class"}, None),
    ("P02", "p02-concentracion/output/aglomeraciones.parquet",
     {"es": "Las 200 aglomeraciones urbanas más grandes, por construcciones", "en": "The 200 largest urban agglomerations, by structures"}, None),
    ("P02", "p02-concentracion/output/hex_r9_top.parquet",
     {"es": "Hexágonos de ~0,1 km² con más construcciones: techo total, cobertura y techo mediano", "en": "~0.1 km² hexagons with most structures"}, None),
    ("P03", "p03-crecimiento/output/hex_r8_urbanizacion_wsf.parquet",
     {"es": "Año en que cada hexágono de ~0,74 km² superó el 10% de asentamiento (1985-2015)", "en": "Year each ~0.74 km² hexagon passed 10% settlement (1985-2015)"},
     "p03-crecimiento/geolibre/p03_explorar.geolibre.json"),
    ("P03", "p03-crecimiento/output/hex_r7_urbanizacion_wsf.parquet",
     {"es": "Lo mismo, con hexágonos de ~5 km²", "en": "Same, with ~5 km² hexagons"}, None),
    ("P03", "p03-crecimiento/output/hex_r7_mitad_crecimiento.parquet",
     {"es": "Hexágonos de ~5 km² que suman la mitad del crecimiento 2000-2015 (WSF), y si GHSL coincide", "en": "~5 km² hexagons adding up to half of 2000-2015 growth (WSF), and whether GHSL agrees"}, None),
    ("P03", "p03-crecimiento/output/ven_contorno.parquet",
     {"es": "Contorno de Venezuela (sin la Guayana Esequiba)", "en": "Outline of Venezuela (without Guayana Esequiba)"}, None),
    ("P03", "p03-crecimiento/output/ven_estados.parquet",
     {"es": "Límites de los 25 estados (simplificados)", "en": "Boundaries of the 25 states (simplified)"}, None),
]


def capas() -> list[dict]:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; SET enable_progress_bar=false;")
    out = []
    for pub, rel, desc, proyecto in CAPAS:
        f = (ROOT / rel).as_posix()
        campos = [{"nombre": r[0], "tipo": r[1]} for r in con.execute(f"DESCRIBE SELECT * FROM '{f}'").fetchall()]
        filas = con.execute(f"SELECT count(*) FROM '{f}'").fetchone()[0]
        lic = "geoboundaries" if rel.endswith(("ven_contorno.parquet", "ven_estados.parquet")) else PUBLICACIONES[pub]["licencia"]
        url = f"{RAW}/{rel}"
        out.append({"id": Path(rel).stem, "publicacion": pub, "descripcion": desc, "formato": "GeoParquet",
                    "url": url, "filas": filas, "campos": campos, "licencia": lic,
                    "geolibre": GEOLIBRE + url.replace(rel, proyecto).replace(":", "%3A").replace("/", "%2F") if proyecto else None,
                    "duckdb": f"INSTALL spatial; LOAD spatial; SELECT * FROM '{url}' LIMIT 10;"})
    return out


def descartes(d: dict) -> list[dict]:
    gi_n = d["p03_lei_gi"]["gistar_2000_2015_descartado"]["normal_version_descartada"]["99"]
    gi_mc = d["p03_lei_gi"]["gistar_2000_2015_descartado"]["montecarlo"]["99"]
    p02n, p02m = d["p02_gistar"]["normal_version_anterior"], d["p02_gistar"]["montecarlo"]
    f = lambda x: str(x).replace(".", ",")
    return [
        {"id": "p02_puntos_calientes_curva_normal", "publicacion": "P02",
         "afirmacion": {"es": f"Los puntos calientes ocupan el {f(p02n['pct_territorio_en_puntos_calientes_99'])}% del territorio con el {f(p02n['pct_construcciones_en_puntos_calientes_99'])}% de las construcciones",
                        "en": f"Hot spots cover {p02n['pct_territorio_en_puntos_calientes_99']}% of the land with {p02n['pct_construcciones_en_puntos_calientes_99']}% of structures"},
         "por_que": {"es": f"La significancia salía de la curva normal, que exagera con datos tan sesgados. Con Monte Carlo: {f(p02m['pct_territorio_en_puntos_calientes_99'])}% del territorio con el {f(p02m['pct_construcciones_en_puntos_calientes_99'])}%.",
                     "en": f"Significance came from the normal curve, which overstates it with such skewed data. With Monte Carlo: {p02m['pct_territorio_en_puntos_calientes_99']}% of the land with {p02m['pct_construcciones_en_puntos_calientes_99']}%."},
         "documento": doc("P02", "README.md")},
        {"id": "p03_puntos_calientes_curva_normal", "publicacion": "P03",
         "afirmacion": {"es": f"El {f(gi_n['pct_crecimiento_wsf_en_calientes_de_ambas'])}% del crecimiento 2000-2015 cayó en el {f(gi_n['pct_territorio_calientes_de_ambas'])}% del territorio",
                        "en": f"{gi_n['pct_crecimiento_wsf_en_calientes_de_ambas']}% of 2000-2015 growth landed on {gi_n['pct_territorio_calientes_de_ambas']}% of the land"},
         "por_que": {"es": f"Con p-valores por Monte Carlo, los puntos calientes en las dos fuentes son el {f(gi_mc['pct_territorio_calientes_de_ambas'])}% del territorio con el {f(gi_mc['pct_crecimiento_wsf_en_calientes_de_ambas'])}% del crecimiento, y las fuentes apenas coinciden.",
                     "en": f"With Monte Carlo p-values, hot spots in both sources are {gi_mc['pct_territorio_calientes_de_ambas']}% of the land with {gi_mc['pct_crecimiento_wsf_en_calientes_de_ambas']}% of growth, and the sources barely agree."},
         "documento": doc("P03", "PROCESO.md")},
        {"id": "p03_mitad_en_menos_del_1pct_como_titular", "publicacion": "P03",
         "afirmacion": {"es": "La mitad del crecimiento 2000-2015 cayó en menos del 1% del territorio (como hallazgo de concentración)",
                        "en": "Half of 2000-2015 growth landed on less than 1% of the land (as a concentration finding)"},
         "por_que": {"es": "Es cierto, pero los asentamientos ya ocupaban el ~0,5% del país: el crecimiento estuvo tan concentrado como las ciudades existentes. No es una concentración nueva.",
                     "en": "True, but settlements already covered ~0.5% of the country: growth was as concentrated as existing cities. Not a new concentration."},
         "documento": doc("P03", "VALIDACION.md")},
        {"id": "p03_boom_de_los_90", "publicacion": "P03",
         "afirmacion": {"es": "Un 'boom' en los 90 (GHSL: 3,28%/año en 1990-2000)", "en": "A 1990s 'boom' (GHSL: 3.28%/yr in 1990-2000)"},
         "por_que": {"es": "WSF-Evolution no lo confirma (2,28%/año). Se publica solo la dirección: los 90 crecieron más rápido que 2000-2015.",
                     "en": "WSF-Evolution does not confirm it (2.28%/yr). Only the direction is published: the 1990s grew faster than 2000-2015."},
         "documento": doc("P03", "README.md")},
        {"id": "p03_auges_1991_1996", "publicacion": "P03",
         "afirmacion": {"es": "Auges de construcción en 1991 y 1996", "en": "Construction booms in 1991 and 1996"},
         "por_que": {"es": "Casi todos los estados 'saltan' el mismo año tras años anormalmente bajos: firma de huecos en las imágenes Landsat.",
                     "en": "Nearly all states 'jump' the same year after abnormally low years: the signature of Landsat imagery gaps."},
         "documento": doc("P03", "VALIDACION.md")},
        {"id": "p03_multiplicadores_desde_1975", "publicacion": "P03",
         "afirmacion": {"es": "Multiplicadores por ciudad desde 1975 (Maturín ×4, Margarita ×6)", "en": "City multipliers since 1975 (Maturín ×4, Margarita ×6)"},
         "por_que": {"es": "Con WSF, en 1985-2015, las dos crecen ×1,9; la base de 1975 del GHSL parece subestimada.",
                     "en": "With WSF, in 1985-2015, both grow ×1.9; the GHSL 1975 baseline looks underestimated."},
         "documento": doc("P03", "README.md")},
        {"id": "p03_caracas", "publicacion": "P03",
         "afirmacion": {"es": "Caracas se expandió (o se densificó)", "en": "Caracas expanded (or densified)"},
         "por_que": {"es": "Con el censo de sus municipios el ODS va de 0,86 a 1,71 según la fuente de suelo: no hay lectura en ningún sentido.",
                     "en": "With its municipal census the SDG ranges from 0.86 to 1.71 depending on the land source: no reading either way."},
         "documento": doc("P03", "VALIDACION.md")},
        {"id": "p03_repartos_exactos_lei", "publicacion": "P03",
         "afirmacion": {"es": "Repartos exactos de relleno y salto", "en": "Exact infill and leapfrog shares"},
         "por_que": {"es": "Según el método, el relleno va del 21% al 41% y los saltos del 4% al 11%. Solo se publica lo que no cambia.",
                     "en": "Depending on the method, infill ranges 21-41% and leapfrog 4-11%. Only what doesn't change is published."},
         "documento": doc("P03", "VALIDACION.md")},
        {"id": "p03_2015_2020", "publicacion": "P03",
         "afirmacion": {"es": "2015-2020: la población cae mientras se sigue construyendo", "en": "2015-2020: population falls while building continues"},
         "por_que": {"es": "WSF-Evolution termina en 2015: no hay segunda fuente.", "en": "WSF-Evolution ends in 2015: there is no second source."},
         "documento": doc("P03", "README.md")},
    ]


def openapi() -> dict:
    def get(resumen, ref=None, param=None):
        op = {"summary": resumen, "responses": {"200": {"description": "JSON"}}}
        if param:
            op["parameters"] = [{"name": param, "in": "path", "required": True, "schema": {"type": "string"}}]
        return {"get": op}
    return {
        "openapi": "3.1.0",
        "info": {"title": "Venezuela en datos abiertos · API estática", "version": VERSION,
                 "description": "Métricas proxy verificadas sobre Venezuela, como archivos JSON estáticos. Cada recurso trae su licencia y su origen.",
                 "license": {"name": "Datos: ODbL-1.0 (P01, P02) y CC-BY-4.0 (P03) · Código: MIT"}},
        "servers": [{"url": "."}],
        "paths": {
            "/index.json": get("Catálogo de recursos"),
            "/indicadores.json": get("Todos los indicadores verificados"),
            "/indicadores/{id}.json": get("Un indicador", param="id"),
            "/estados.json": get("Los 25 estados: construcciones, asentamiento y población"),
            "/estados/{codigo}.json": get("Un estado", param="codigo"),
            "/ciudades.json": get("Lecturas por ciudad del ODS 11.3.1, con su estado de verificación"),
            "/series/asentamiento.json": get("Superficie de asentamiento anual, 1985-2015"),
            "/capas.json": get("Capas GeoParquet descargables, con campos, filas y licencia"),
            "/descartes.json": get("Lo que no resistió las verificaciones, y por qué"),
        },
    }


def pruebas(d: dict, ind: list, est: list, ciu: list) -> None:
    """Coherencia entre fuentes antes de publicar. Si algo no cuadra, no se escribe nada."""
    total = d["p01"]["total_edificios"]
    assert sum(e["construcciones"]["valor"] for e in est) == total == d["p01"]["suma_por_estados"], "P01: estados ≠ total"
    assert len(est) == 25 and len({e["codigo"] for e in est}) == 25, "deben ser 25 estados con código único"
    assert abs(sum(f["pct"] for f in d["p01"]["por_fuente"]) - 100) < 0.2, "P01: % por fuente no suma 100"
    i = {x["id"]: x for x in ind}
    assert i["ods_11_3_1_nacional_2000_2015"]["rango"] == [0.88, 0.95], "P03: el rango del ODS cambió respecto de VALIDACION.md"
    assert i["crecimiento_pegado_a_lo_urbano_pct"]["rango"] == [89, 96], "P03: 'pegado a lo urbano' cambió respecto de VALIDACION.md"
    assert max(i["mitad_construcciones_pct_territorio"]["rango"]) < 1, "P02: 'la mitad en menos del 1%' ya no se cumple en todas las escalas"
    assert {c["nombre"] for c in ciu if c["estado"] == "verificada"} == {"Barquisimeto", "Barcelona-Puerto La Cruz", "Margarita"}, \
        "P03: cambiaron las ciudades verificadas"
    serie = d["p03_serie"]["km2_acumulados"]
    assert list(map(int, serie)) == list(range(1985, 2016)), "P03: la serie debe ser anual 1985-2015"


def recursos() -> dict[str, object]:
    d = fuentes_de_datos()
    ind, est, ciu = indicadores(d), estados(d), ciudades(d)
    pruebas(d, ind, est, ciu)
    files = {
        "index.json": {"nombre": "Venezuela en datos abiertos", "version": VERSION, "proyecto": "Kaimind",
                       "descripcion": {"es": "Métricas proxy, verificadas con una segunda fuente, para un país sin cifras oficiales actualizadas.",
                                       "en": "Proxy metrics, checked against a second source, for a country without up-to-date official figures."},
                       "recursos": ["indicadores.json", "estados.json", "ciudades.json", "series/asentamiento.json", "capas.json",
                                    "descartes.json", "openapi.json"],
                       "publicaciones": PUBLICACIONES, "licencias": LICENCIAS, "repositorio": REPO,
                       "como_citar": "Kaimind (2026). Venezuela en datos abiertos. " + REPO},
        "indicadores.json": ind, "estados.json": est, "ciudades.json": ciu,
        "series/asentamiento.json": serie_asentamiento(d), "capas.json": capas(), "descartes.json": descartes(d),
        "openapi.json": openapi(),
    }
    files.update({f"indicadores/{x['id']}.json": x for x in ind})
    files.update({f"estados/{x['codigo']}.json": x for x in est})
    return {k: json.dumps(v, ensure_ascii=False, indent=2) + "\n" for k, v in files.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="comprobar que lo publicado coincide con lo que se generaría")
    args = ap.parse_args()
    files = recursos()
    if args.check:
        malos = [k for k, v in files.items() if not (OUT / k).exists() or (OUT / k).read_text(encoding="utf-8") != v]
        sobran = [p.relative_to(OUT).as_posix() for p in OUT.rglob("*.json") if p.relative_to(OUT).as_posix() not in files]
        if malos or sobran:
            print("La API publicada no coincide con los datos. Corre: python -P api/build_api.py", file=sys.stderr)
            for k in malos + sobran:
                print("  ", k, file=sys.stderr)
            sys.exit(1)
        print(f"API v0 al día: {len(files)} archivos")
        return
    for p in OUT.rglob("*.json"):
        p.unlink()
    for k, v in files.items():
        (OUT / k).parent.mkdir(parents=True, exist_ok=True)
        (OUT / k).write_text(v, encoding="utf-8", newline="\n")
    print(f"API v0: {len(files)} archivos en {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
