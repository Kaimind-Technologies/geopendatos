"""P03 · Verificación de la población del GHSL (GHS-POP) contra los censos del INE.

El ODS 11.3.1 usa la tasa de crecimiento de la población; si GHS-POP reparte o hace
crecer mal la población, el indicador no sirve. Se contrasta por estado con los censos
2001 y 2011 (INE, XIV Censo, Cuadro 2.2):
  1. Distribución: participación de cada estado (GHS-POP 2010 vs censo 2011).
  2. Dinámica: crecimiento anual por estado (GHS-POP 2000→2010 vs censo 2001→2011).
Los totales no se comparan directamente: el censo es población empadronada (sin
omisión censal) y GHS-POP está alineado con UN WPP.

Salida: output/p03_verificacion_poblacion.json

Uso:
    python -P verify_pop.py
"""

import json
import math
import unicodedata
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
VEN = ROOT / "data" / "ghsl" / "ven"
OUT = Path(__file__).resolve().parent / "output"

# INE, XIV Censo Nacional de Población y Vivienda, Cuadro 2.2 (censos 2001 y 2011). Vargas = La Guaira.
CENSO = {
    "DISTRITO CAPITAL": (1_836_286, 1_943_901), "AMAZONAS": (70_464, 146_480), "ANZOATEGUI": (1_222_225, 1_469_747),
    "APURE": (377_756, 459_025), "ARAGUA": (1_449_616, 1_630_308), "BARINAS": (624_508, 816_264),
    "BOLIVAR": (1_214_846, 1_413_115), "CARABOBO": (1_932_168, 2_245_744), "COJEDES": (253_105, 323_165),
    "DELTA AMACURO": (97_987, 165_525), "FALCON": (763_188, 902_847), "GUARICO": (627_086, 747_739),
    "LARA": (1_556_415, 1_774_867), "MERIDA": (715_268, 828_592), "MIRANDA": (2_330_872, 2_675_165),
    "MONAGAS": (712_626, 905_443), "NUEVA ESPARTA": (373_851, 491_610), "PORTUGUESA": (725_740, 876_496),
    "SUCRE": (786_483, 896_291), "TACHIRA": (992_669, 1_168_908), "TRUJILLO": (608_563, 686_367),
    "YARACUY": (499_049, 600_852), "ZULIA": (2_983_679, 3_704_404), "LA GUAIRA": (298_109, 352_920),
    "DEPENDENCIAS FEDERALES": (1_651, 2_155),
}


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()


def main() -> None:
    names = {int(k): v for k, v in json.loads((VEN / "estados.json").read_text(encoding="utf-8")).items()}
    with rasterio.open(VEN / "mask_estados.tif") as src:
        lab = src.read(1)
    pops = {}
    for e in (2000, 2010):
        with rasterio.open(VEN / f"pop_{e}.tif") as src:
            p = src.read(1)
        pops[e] = np.bincount(lab.ravel(), weights=p.ravel(), minlength=len(names) + 1)

    rows = []
    for i, n in names.items():
        c01, c11 = CENSO[norm(n)]
        rows.append({"estado": n, "censo_2001": c01, "censo_2011": c11,
                     "ghs_pop_2000": round(float(pops[2000][i])), "ghs_pop_2010": round(float(pops[2010][i]))})
    tot = {k: sum(r[k] for r in rows) for k in ("censo_2001", "censo_2011", "ghs_pop_2000", "ghs_pop_2010")}
    for r in rows:
        r["pct_censo_2011"] = round(100 * r["censo_2011"] / tot["censo_2011"], 2)
        r["pct_ghs_2010"] = round(100 * r["ghs_pop_2010"] / tot["ghs_pop_2010"], 2)
        r["crec_censo_01_11_pct"] = round(100 * math.log(r["censo_2011"] / r["censo_2001"]) / 10, 2)
        r["crec_ghs_00_10_pct"] = round(100 * math.log(r["ghs_pop_2010"] / r["ghs_pop_2000"]) / 10, 2) if r["ghs_pop_2000"] else None

    big = [r for r in rows if r["censo_2011"] > 100_000]
    share_c = np.array([r["pct_censo_2011"] for r in big])
    share_g = np.array([r["pct_ghs_2010"] for r in big])
    gr_c = np.array([r["crec_censo_01_11_pct"] for r in big])
    gr_g = np.array([r["crec_ghs_00_10_pct"] for r in big])
    res = {
        "totales": tot,
        "distribucion_correlacion": round(float(np.corrcoef(share_c, share_g)[0, 1]), 3),
        "distribucion_error_medio_puntos_pct": round(float(np.abs(share_c - share_g).mean()), 2),
        "crecimiento_correlacion": round(float(np.corrcoef(gr_c, gr_g)[0, 1]), 3),
        "crecimiento_error_medio_puntos_pct_anual": round(float(np.abs(gr_c - gr_g).mean()), 2),
        "estados": rows,
    }
    (OUT / "p03_verificacion_poblacion.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"totales: censo 2001 {tot['censo_2001']:,} · censo 2011 {tot['censo_2011']:,} · "
          f"GHS-POP 2000 {tot['ghs_pop_2000']:,} · GHS-POP 2010 {tot['ghs_pop_2010']:,}")
    print(f"distribución por estado: correlación {res['distribucion_correlacion']} · error medio "
          f"{res['distribucion_error_medio_puntos_pct']} puntos de %")
    print(f"crecimiento por estado: correlación {res['crecimiento_correlacion']} · error medio "
          f"{res['crecimiento_error_medio_puntos_pct_anual']} puntos de %/año")
    print(f"\n{'estado':24}{'% censo':>9}{'% GHS':>8}{'crec. censo':>13}{'crec. GHS':>11}")
    for r in sorted(big, key=lambda r: -r["censo_2011"]):
        print(f"{r['estado'][:23]:24}{r['pct_censo_2011']:>9}{r['pct_ghs_2010']:>8}"
              f"{r['crec_censo_01_11_pct']:>12}%{r['crec_ghs_00_10_pct']:>10}%")


if __name__ == "__main__":
    main()
