"""P03 · Matriz de robustez del ODS 11.3.1 por ciudad, 2000-2015.

Cruza 2 fuentes de suelo urbano (GHSL m² construidos, WSF-Evolution asentamiento) con
2 fuentes de crecimiento de población (GHS-POP dentro de la ciudad, y crecimiento
censal 2001→2011 del INE del estado o estados donde está la ciudad) = 4 combinaciones.

Regla de publicación:
  - "densificación robusta": las 4 combinaciones dan ODS < 0,9
  - "expansión robusta": las 4 dan ODS > 1,1
  - "el suelo creció al menos al ritmo de la población": las 4 dan ≥ 1
  - si no, "no concluyente" → no se publica una lectura para esa ciudad.

El censo por estado es un proxy grueso de la ciudad; por eso Caracas se prueba con dos
proxies (Distrito Capital solo, y Distrito Capital + Miranda).

Salida: output/p03_matriz_robustez.json

Uso:
    python -P robustness_matrix.py
"""

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "output"

# Estado(s) cuyo crecimiento censal 2001→2011 se usa como proxy de cada ciudad (por su nombre en p03_ciudades.json).
PROXY = {
    "Bustamante": ["ZULIA"], "Valencia": ["CARABOBO"], "Caracas, Parroquia Catedral": ["DISTRITO CAPITAL"],
    "La Morita": ["ARAGUA"], "Barquisimeto": ["LARA"], "Ciudad Guayana": ["BOLIVAR"], "Baralt": ["ZULIA"],
    "Barcelona": ["ANZOATEGUI"], "Maturín": ["MONAGAS"], "El Valle": ["NUEVA ESPARTA"],
    "Caracas metropolitana": ["DISTRITO CAPITAL", "MIRANDA"],
}
ALIAS = {"Bustamante": "Maracaibo", "Valencia": "Valencia", "Caracas, Parroquia Catedral": "Caracas (valle)",
         "La Morita": "Maracay-Turmero", "Barquisimeto": "Barquisimeto", "Ciudad Guayana": "Ciudad Guayana",
         "Baralt": "Costa Oriental del Lago", "Barcelona": "Barcelona-Puerto La Cruz", "Maturín": "Maturín",
         "El Valle": "Margarita", "Caracas metropolitana": "Caracas metropolitana"}


def key_for(name: str) -> str:
    return next(k for k in PROXY if k in name)


def main() -> None:
    pop_ver = json.loads((OUT / "p03_verificacion_poblacion.json").read_text(encoding="utf-8"))["estados"]
    import unicodedata
    norm = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    censo = {norm(r["estado"]): (r["censo_2001"], r["censo_2011"]) for r in pop_ver}
    wsf = json.loads((OUT / "p03_verificacion_wsf_ciudades.json").read_text(encoding="utf-8"))

    res = {}
    variants = []
    for name, d in wsf.items():
        k = key_for(name)
        variants.append((name, ALIAS[k], PROXY[k]))
        if k == "Caracas, Parroquia Catedral":
            variants.append((name, "Caracas (valle) · proxy DC+Miranda", ["DISTRITO CAPITAL", "MIRANDA"]))
    print(f"{'ciudad':38}{'GHSL/GHS':>9}{'WSF/GHS':>9}{'GHSL/cen':>9}{'WSF/cen':>9}   lectura robusta")
    for name, alias, states in variants:
        p = next(x for x in wsf[name]["periodos"] if x["periodo"] == "2000-2015")
        c01 = sum(censo[s][0] for s in states)
        c11 = sum(censo[s][1] for s in states)
        pgr_censo = 100 * math.log(c11 / c01) / 10
        combos = {
            "ghsl_ghspop": p["ghsl_pct"] / p["poblacion_pct"],
            "wsf_ghspop": p["wsf_pct"] / p["poblacion_pct"],
            "ghsl_censo": p["ghsl_pct"] / pgr_censo,
            "wsf_censo": p["wsf_pct"] / pgr_censo,
        }
        v = list(combos.values())
        if all(x < 0.9 for x in v):
            lect = "densificación robusta"
        elif all(x > 1.1 for x in v):
            lect = "expansión robusta"
        elif all(x >= 1.0 for x in v):  # "al menos al ritmo" = ODS >= 1 en las 4 combinaciones
            lect = "el suelo creció al menos al ritmo de la población"
        else:
            lect = "no concluyente"
        res[alias] = {"ods_2000_2015": {k: round(x, 2) for k, x in combos.items()},
                      "crec_poblacion_ghs_pct": p["poblacion_pct"], "crec_poblacion_censo_estado_pct": round(pgr_censo, 2),
                      "estados_proxy": states, "lectura": lect}
        print(f"{alias[:37]:38}{combos['ghsl_ghspop']:>9.2f}{combos['wsf_ghspop']:>9.2f}"
              f"{combos['ghsl_censo']:>9.2f}{combos['wsf_censo']:>9.2f}   {lect}")
    (OUT / "p03_matriz_robustez.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
