"""P02: puntos calientes Getis-Ord Gi* con p-valores por Monte Carlo.

El z de Gi* suele compararse con una curva normal, pero estos datos están muy lejos de
ser normales (54% de celdas vacías, media de 56 construcciones, máximo de 19.087): la
normal exagera la significancia. Por eso el p-valor sale de simular la hipótesis nula de
Gi* (aleatorización total: los valores de las celdas repartidos al azar en el territorio).

- Celdas: H3 res 7 (~5 km²) de todo el territorio (sin Esequibo), con 0 si no tienen
  construcciones. Los conteos salen de la capa publicada output/hex_r7_ranking.parquet.
- Vecindad: la celda y sus 6 vecinas, con pesos binarios.
- p-valor de dos colas contra N_SIMS sumas de celdas tomadas al azar.
- Corrección por comparaciones múltiples: FDR de Benjamini-Hochberg.
- Se guarda también el p-valor de la normal para comparar con la versión anterior.

Salidas en output/:
    hex_r7_gistar.parquet   capa con z, p (Monte Carlo), p_normal y clase
    p02_gistar.json         resumen y comparación con la normal

Uso (después de layers.py):
    python -P gistar.py
"""

import json
import math
from pathlib import Path

import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "output"
RANKING = OUT / "hex_r7_ranking.parquet"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
N_SIMS = 5_000_000
CHUNK = 500_000
SEED = 2026


def neighborhoods(con) -> dict[str, np.ndarray]:
    """Cada celda del territorio con su conteo, área, nº de vecinas en el territorio (w) y suma vecinal (lag)."""
    con.execute(f"""
        CREATE TABLE terr AS
        WITH parts AS (SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}')),
        cells AS (SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), 7)) AS cell FROM parts),
        counts AS (SELECT h3_string_to_h3(h3) AS cell, construcciones AS n FROM read_parquet('{RANKING.as_posix()}'))
        SELECT cell, coalesce(n, 0) AS n, h3_cell_area(cell, 'km^2') AS km2
        FROM (SELECT cell FROM cells UNION SELECT cell FROM counts) c LEFT JOIN counts USING (cell)
    """)
    return con.execute("""
        WITH nb AS (SELECT cell, unnest(h3_grid_disk(cell, 1)) AS nbr FROM terr)
        SELECT t.cell, t.n, t.km2, count(*) AS w, sum(t2.n) AS lag
        FROM nb JOIN terr t2 ON t2.cell = nb.nbr JOIN terr t ON t.cell = nb.cell
        GROUP BY t.cell, t.n, t.km2
    """).fetchnumpy()


def null_sums(x: np.ndarray, w_max: int, rng: np.random.Generator) -> np.ndarray:
    """Sumas ordenadas de w celdas al azar (fila w-1, para w = 1..w_max), N_SIMS veces.

    Con reposición: con 192.832 celdas, la diferencia con sacarlas sin reposición es despreciable.
    """
    sums = np.empty((w_max, N_SIMS))
    for start in range(0, N_SIMS, CHUNK):
        m = min(CHUNK, N_SIMS - start)
        sums[:, start:start + m] = x[rng.integers(0, len(x), size=(m, w_max))].cumsum(axis=1).T
    sums.sort(axis=1)
    return sums


def montecarlo_p(lag: np.ndarray, w: np.ndarray, sums: np.ndarray) -> np.ndarray:
    p = np.ones(len(lag))
    for wv in np.unique(w):
        m = w == wv
        s = sums[wv - 1]
        ge = N_SIMS - np.searchsorted(s, lag[m], side="left")
        le = np.searchsorted(s, lag[m], side="right")
        p[m] = np.minimum(1.0, 2 * (1 + np.minimum(ge, le)) / (N_SIMS + 1))
    return p


def bh_cuts(p: np.ndarray) -> dict[int, float]:
    """Benjamini-Hochberg: umbral de p por nivel de confianza controlando la tasa de falsos descubrimientos."""
    order = np.sort(p)
    ranks = np.arange(1, len(p) + 1)

    def cut(alpha: float) -> float:
        ok = order <= ranks / len(p) * alpha
        return float(order[ok].max()) if ok.any() else 0.0

    return {99: cut(0.01), 95: cut(0.05), 90: cut(0.10)}


def classify(p: np.ndarray, z: np.ndarray, cuts: dict[int, float]) -> np.ndarray:
    clase = np.full(len(p), "No significativo", dtype=object)
    for conf in (90, 95, 99):
        sig = p <= cuts[conf]
        clase[sig & (z > 0)] = f"Punto caliente {conf}%"
        clase[sig & (z < 0)] = f"Punto frío {conf}%"
    return clase


def summary(clase: np.ndarray, cuts: dict[int, float], x: np.ndarray, km2: np.ndarray) -> dict:
    hot99 = clase == "Punto caliente 99%"
    return {
        "umbral_p_FDR": {str(k): v for k, v in cuts.items()},
        "clases": {c: {"celdas": int((clase == c).sum()), "km2": round(float(km2[clase == c].sum())),
                       "construcciones": int(x[clase == c].sum())} for c in sorted(set(clase))},
        "pct_construcciones_en_puntos_calientes_99": round(100 * float(x[hot99].sum() / x.sum()), 1),
        "pct_territorio_en_puntos_calientes_99": round(100 * float(km2[hot99].sum() / km2.sum()), 2),
    }


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    nb = neighborhoods(con)
    cells, x, km2 = nb["cell"], nb["n"].astype(float), nb["km2"]
    w, lag = nb["w"].astype(int), nb["lag"].astype(float)
    N = len(x)
    xbar = x.mean()
    s = math.sqrt((x ** 2).mean() - xbar ** 2)

    def z_of(lag_, w_):
        # pesos binarios: sum(w) = sum(w²) = número de celdas en la vecindad
        return (lag_ - xbar * w_) / (s * np.sqrt((N * w_ - w_ ** 2) / (N - 1)))

    z = z_of(lag, w)
    p_normal = np.vectorize(math.erfc)(np.abs(z) / math.sqrt(2))  # dos colas
    p = montecarlo_p(lag, w, null_sums(x, int(w.max()), np.random.default_rng(SEED)))

    cuts_mc, cuts_n = bh_cuts(p), bh_cuts(p_normal)
    clase, clase_n = classify(p, z, cuts_mc), classify(p_normal, z, cuts_n)

    # La celda menos extrema que la normal daba como punto caliente al 99%: cuánto vale su p de verdad.
    borde = np.where((clase_n == "Punto caliente 99%") & (w == 7))[0]
    b = borde[np.argmin(z[borde])]
    result = {
        "celdas_territorio": N,
        "km2_territorio_celdas": round(float(km2.sum())),
        "simulaciones": N_SIMS,
        "semilla": SEED,
        "z_minimo_posible": round(float(z_of(0.0, 7.0)), 3),  # por eso no puede haber puntos fríos
        "montecarlo": summary(clase, cuts_mc, x, km2),
        "normal_version_anterior": summary(clase_n, cuts_n, x, km2),
        "borde_99_de_la_normal": {"z": round(float(z[b]), 3), "p_normal": float(p_normal[b]),
                                  "p_montecarlo": float(p[b])},
    }
    (OUT / "p02_gistar.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    con.register("gi_np", {"cell": cells, "construcciones": x.astype(np.int64), "z": np.round(z, 3),
                           "p": p, "p_normal": p_normal, "clase": clase.astype(str)})
    con.execute(f"""
        COPY (
            SELECT h3_h3_to_string(cell::UBIGINT) AS h3, construcciones, z, p, p_normal, clase,
                   ST_SetCRS(ST_GeomFromText(h3_cell_to_boundary_wkt(cell::UBIGINT)), 'OGC:CRS84') AS geometry
            FROM gi_np WHERE construcciones > 0 OR clase <> 'No significativo'
        ) TO '{(OUT / "hex_r7_gistar.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    for k in ("montecarlo", "normal_version_anterior"):
        r = result[k]
        print(f"{k:24} puntos calientes 99%: {r['clases'].get('Punto caliente 99%', {}).get('celdas', 0):>5} celdas · "
              f"{r['pct_construcciones_en_puntos_calientes_99']}% de las construcciones en "
              f"{r['pct_territorio_en_puntos_calientes_99']}% del territorio")
    print("borde del 99% de la normal:", result["borde_99_de_la_normal"], "| z mínimo posible:", result["z_minimo_posible"])


if __name__ == "__main__":
    main()
