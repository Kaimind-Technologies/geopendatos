"""P02: el tamaño de las ciudades medido con la misma regla para todas, y cuánto depende Zipf del ajuste.

Parte de output/aglomeraciones.parquet (stats.py): las 200 manchas urbanas continuas más
grandes (celdas H3 res 8 contiguas con ≥250 construcciones/km²).

1. Áreas metropolitanas con una sola regla: cada ciudad suma las manchas cuyo centro está
   a menos de R km del centro de su mancha principal (R = 15, 30 y 45 km). El Ávila y los
   cerros parten a Caracas en varios núcleos; con esta regla se le suman (Valles del Tuy,
   Guarenas-Guatire, Los Teques, el litoral...), pero a Maracaibo, Valencia y las demás
   también se les suman los suyos. Solo entran las 200 manchas publicadas.
2. Sensibilidad del exponente de Zipf al número de aglomeraciones del ajuste (10 a 200):
   mínimos cuadrados en log-log, como stats.py, y el estimador de Gabaix e Ibragimov (2011),
   que usa log(rango − 1/2) y corrige el sesgo de muestras chicas.

Salida: output/p02_aglomeraciones.json

Uso (después de stats.py):
    python -P aglomeraciones.py
"""

import json
from pathlib import Path

import duckdb
import numpy as np

OUT = Path(__file__).resolve().parent / "output"
AGLO = OUT / "aglomeraciones.parquet"
# Mancha principal de cada ciudad (rango con umbral 250), verificadas con Nominatim.
CIUDADES = {1: "Maracaibo", 2: "Valencia", 3: "Caracas", 4: "Barquisimeto", 5: "Ciudad Guayana", 6: "Maracay"}
RADIOS_KM = (15, 30, 45)
ZIPF_N = (10, 20, 30, 50, 100, 200)


def metros(con) -> list[dict]:
    con.execute(f"CREATE TABLE a AS SELECT rango, construcciones, ST_Centroid(geometry) AS c FROM read_parquet('{AGLO.as_posix()}')")
    rows = con.execute(f"""
        SELECT m.rango AS ciudad, a.rango, a.construcciones, ST_Distance_Sphere(m.c, a.c) / 1000 AS km
        FROM a AS m, a WHERE m.rango IN ({", ".join(map(str, CIUDADES))})
        ORDER BY ciudad, a.rango
    """).fetchall()
    result = []
    for rango, nombre in CIUDADES.items():
        own = [(r, n, km) for c, r, n, km in rows if c == rango]
        fila = {"ciudad": nombre, "rango_mancha_principal": rango,
                "mancha_principal": int(next(n for r, n, _ in own if r == rango))}
        for radio in RADIOS_KM:
            dentro = [(r, n) for r, n, km in own if km <= radio]
            fila[f"{radio}_km"] = {"construcciones": int(sum(n for _, n in dentro)), "manchas": len(dentro),
                                   "rangos": [r for r, _ in dentro]}
        result.append(fila)
    return result


def zipf(con) -> dict:
    sizes = np.array([n for (n,) in con.execute("SELECT construcciones FROM a ORDER BY rango").fetchall()], dtype=float)
    ajustes = []
    for n in ZIPF_N:
        top = sizes[:n]
        rank = np.arange(1, n + 1)
        slope, intercept = np.polyfit(np.log(rank), np.log(top), 1)
        pred = intercept + slope * np.log(rank)
        r2 = 1 - np.sum((np.log(top) - pred) ** 2) / np.sum((np.log(top) - np.log(top).mean()) ** 2)
        alpha = -np.polyfit(np.log(top), np.log(rank - 0.5), 1)[0]  # Gabaix-Ibragimov: exponente de Pareto
        ajustes.append({"aglomeraciones": n, "exponente_mco": round(float(-slope), 3),
                        "exponente_gabaix_ibragimov": round(float(1 / alpha), 3), "r2": round(float(r2), 3)})
    return {"primacia_1_sobre_2": round(float(sizes[0] / sizes[1]), 2), "ajustes": ajustes}


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; SET enable_progress_bar=false; SET geometry_always_xy = true;")
    result = {"metros": metros(con), "zipf": zipf(con)}
    (OUT / "p02_aglomeraciones.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{'ciudad':16}{'mancha':>10}" + "".join(f"{f'{r} km':>16}" for r in RADIOS_KM))
    for m in result["metros"]:
        print(f"{m['ciudad']:16}{m['mancha_principal']:>10,}"
              + "".join(f"{m[f'{r}_km']['construcciones']:>10,} ({m[f'{r}_km']['manchas']:>2})" for r in RADIOS_KM))
    print("primacía 1/2:", result["zipf"]["primacia_1_sobre_2"])
    for z in result["zipf"]["ajustes"]:
        print(f"Zipf con {z['aglomeraciones']:>3}: MCO {z['exponente_mco']} · Gabaix-Ibragimov "
              f"{z['exponente_gabaix_ibragimov']} · R² {z['r2']}")


if __name__ == "__main__":
    main()
