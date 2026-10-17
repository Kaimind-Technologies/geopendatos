"""P02: estadística espacial de las construcciones de Venezuela.

1. Gini espacial + curva de Lorenz (H3 res 7 sobre TODO el territorio, con celdas vacías).
2. Ley de Zipf: aglomeraciones urbanas = componentes conexas de celdas H3 res 8 por
   encima de un umbral de densidad; ajuste rango-tamaño con 3 umbrales.

Los puntos calientes Getis-Ord Gi* están en gistar.py (p-valores por Monte Carlo) y la
sensibilidad de Zipf y las áreas metropolitanas, en aglomeraciones.py.

Salidas en output/:
    p02_stats.json, aglomeraciones.parquet, lorenz.png, zipf.png

Uso:
    python -P stats.py
"""

import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "ven_construcciones_metricas.parquet"
ADM0 = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
OUT = Path(__file__).resolve().parent / "output"
ZIPF_THRESHOLDS_KM2 = (150, 250, 400)  # construcciones por km² para considerar urbana una celda
ZIPF_TOP = 50                           # aglomeraciones usadas en el ajuste

BG, FG, MUTED, ACCENT = "#0b1020", "#f3f4f6", "#9aa0b5", "#f1605d"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL h3 FROM community; LOAD h3; SET enable_progress_bar=false;")
    con.execute(f"CREATE TABLE b AS SELECT lat, lng FROM read_parquet('{DERIVED.as_posix()}')")
    return con


def territory_cells(con, res: int) -> None:
    """Todas las celdas H3 de Venezuela (sin Esequibo), con 0 si no tienen construcciones."""
    con.execute(f"""
        CREATE TABLE terr{res} AS
        WITH parts AS (
            SELECT unnest(ST_Dump(geom)) AS d FROM ST_Read('{ADM0.as_posix()}')
        ), cells AS (
            SELECT DISTINCT unnest(h3_polygon_wkt_to_cells(ST_AsText(d.geom), {res})) AS cell FROM parts
        ), counts AS (
            SELECT h3_latlng_to_cell(lat, lng, {res}) AS cell, count(*) AS n FROM b GROUP BY cell
        )
        SELECT cell, coalesce(n, 0) AS n
        FROM (SELECT cell FROM cells UNION SELECT cell FROM counts) c LEFT JOIN counts USING (cell)
    """)


# ---------- 1. Gini + Lorenz ----------
def gini_lorenz(x: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    x = np.sort(x)
    n = len(x)
    cum = np.cumsum(x)
    gini = (2 * np.sum(np.arange(1, n + 1) * x)) / (n * cum[-1]) - (n + 1) / n
    pop = np.concatenate([[0], np.arange(1, n + 1) / n])
    share = np.concatenate([[0], cum / cum[-1]])
    return float(gini), pop, share


def plot_lorenz(pop, share, gini: float) -> None:
    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100, facecolor=BG)
    ax.set_facecolor(BG)
    idx = np.linspace(0, len(pop) - 1, 2000).astype(int)
    ax.plot([0, 1], [0, 1], color=MUTED, lw=1.5, ls="--", label="Distribución perfectamente pareja")
    ax.fill_between(pop[idx], share[idx], pop[idx], color=ACCENT, alpha=0.25)
    ax.plot(pop[idx], share[idx], color=ACCENT, lw=3.5, label="Venezuela")
    ax.set_xlabel("% del territorio (de menos a más construido)", color=FG, fontsize=18)
    ax.set_ylabel("% acumulado de construcciones", color=FG, fontsize=18)
    ax.tick_params(colors=MUTED, labelsize=14)
    for s in ax.spines.values():
        s.set_color(MUTED)
    ax.set_xticks([0, .25, .5, .75, 1], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_yticks([0, .25, .5, .75, 1], ["0%", "25%", "50%", "75%", "100%"])
    ax.text(0.04, 0.9, f"Gini espacial = {gini:.2f}".replace(".", ","), color=FG, fontsize=34, fontweight="bold", transform=ax.transAxes)
    ax.legend(loc="center left", facecolor=BG, edgecolor=MUTED, labelcolor=FG, fontsize=14)
    fig.text(0.02, 0.01, "Celdas H3 de ~5 km² · Overture Maps 2026-09-23.1 · Kaimind", color=MUTED, fontsize=12)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "lorenz.png", facecolor=BG)
    plt.close(fig)


# ---------- 2. Zipf ----------
def components(cells: list[int], edges: list[tuple[int, int]]) -> dict[int, int]:
    parent = {c: c for c in cells}

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return {c: find(c) for c in cells}


def zipf(con) -> dict:
    con.execute("""
        CREATE TABLE r8 AS
        SELECT h3_latlng_to_cell(lat, lng, 8) AS cell, count(*) AS n FROM b GROUP BY cell
    """)
    results = {}
    for thr in ZIPF_THRESHOLDS_KM2:
        con.execute(f"""
            CREATE OR REPLACE TABLE urb AS
            SELECT cell, n FROM r8 WHERE n / (h3_cell_area(cell, 'km^2')) >= {thr}
        """)
        cells = [c for (c,) in con.execute("SELECT cell FROM urb").fetchall()]
        edges = con.execute("""
            SELECT u.cell, v.cell FROM urb u, unnest(h3_grid_disk(u.cell, 1)) AS t(nbr)
            JOIN urb v ON v.cell = t.nbr WHERE u.cell < v.cell
        """).fetchall()
        comp = components(cells, edges)
        con.register("comp_np", {"cell": np.array(list(comp.keys()), dtype=np.uint64),
                                 "comp": np.array(list(comp.values()), dtype=np.uint64)})
        aggs = con.execute("""
            SELECT c.comp, sum(u.n) AS construcciones, sum(h3_cell_area(u.cell, 'km^2')) AS km2,
                   avg(h3_cell_to_lat(u.cell)) AS lat, avg(h3_cell_to_lng(u.cell)) AS lng
            FROM comp_np c JOIN urb u ON u.cell = c.cell
            GROUP BY c.comp ORDER BY construcciones DESC
        """).fetchall()
        sizes = np.array([a[1] for a in aggs], dtype=float)
        top = sizes[:ZIPF_TOP]
        rank = np.arange(1, len(top) + 1)
        slope, intercept = np.polyfit(np.log(rank), np.log(top), 1)
        pred = intercept + slope * np.log(rank)
        r2 = 1 - np.sum((np.log(top) - pred) ** 2) / np.sum((np.log(top) - np.log(top).mean()) ** 2)
        results[thr] = {
            "aglomeraciones": len(aggs),
            "exponente_zipf": round(float(-slope), 3),
            "r2": round(float(r2), 3),
            "primacia_1_sobre_2": round(float(sizes[0] / sizes[1]), 2),
            "pct_construcciones_en_la_mayor": round(100 * float(sizes[0] / sizes.sum()), 1),
            "top10": [{"construcciones": int(a[1]), "km2": round(a[2], 1),
                       "lat": round(a[3], 4), "lng": round(a[4], 4)} for a in aggs[:10]],
        }
        if thr == 250:
            con.execute("""
                CREATE OR REPLACE TABLE aglo AS
                SELECT c.comp, sum(u.n) AS construcciones,
                       ST_Union_Agg(ST_GeomFromText(h3_cell_to_boundary_wkt(u.cell))) AS geometry
                FROM comp_np c JOIN urb u ON u.cell = c.cell GROUP BY c.comp
            """)
            con.execute(f"""
                COPY (SELECT row_number() OVER (ORDER BY construcciones DESC) AS rango, construcciones,
                             ST_SetCRS(geometry, 'OGC:CRS84') AS geometry
                      FROM aglo ORDER BY construcciones DESC LIMIT 200)
                TO '{(OUT / "aglomeraciones.parquet").as_posix()}' (FORMAT parquet, COMPRESSION zstd)
            """)
            plot_zipf(sizes, slope, intercept, r2)
    return results


def plot_zipf(sizes: np.ndarray, slope: float, intercept: float, r2: float) -> None:
    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100, facecolor=BG)
    ax.set_facecolor(BG)
    rank = np.arange(1, len(sizes) + 1)
    ax.loglog(rank, sizes, "o", color=ACCENT, ms=6, alpha=0.85, label="Aglomeraciones urbanas")
    r = np.arange(1, ZIPF_TOP + 1)
    ax.loglog(r, np.exp(intercept) * r ** slope, color=FG, lw=2,
              label=f"Ajuste top {ZIPF_TOP}: exponente {-slope:.2f} (R² = {r2:.2f})".replace(".", ","))
    ax.loglog(r, sizes[0] / r, color=MUTED, lw=1.5, ls="--", label="Ley de Zipf ideal (exponente 1)")
    ax.set_xlabel("Rango de la aglomeración (1 = la más grande)", color=FG, fontsize=18)
    ax.set_ylabel("Construcciones", color=FG, fontsize=18)
    ax.tick_params(colors=MUTED, labelsize=14, which="both")
    for s in ax.spines.values():
        s.set_color(MUTED)
    ax.legend(facecolor=BG, edgecolor=MUTED, labelcolor=FG, fontsize=14)
    fig.text(0.02, 0.01, "Aglomeraciones = celdas H3 de ~0,74 km² con ≥250 construcciones/km², contiguas · Kaimind",
             color=MUTED, fontsize=12)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "zipf.png", facecolor=BG)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = connect()
    territory_cells(con, 7)
    x = np.array([n for (n,) in con.execute("SELECT n FROM terr7").fetchall()], dtype=float)
    gini, pop, share = gini_lorenz(x)
    gini_ocupadas, _, _ = gini_lorenz(x[x > 0])
    plot_lorenz(pop, share, gini)
    stats = {
        "gini_espacial_territorio": round(gini, 3),
        "gini_solo_celdas_con_construcciones": round(gini_ocupadas, 3),
        "celdas_r7_territorio": int(len(x)),
        "celdas_r7_vacias_pct": round(100 * float((x == 0).mean()), 1),
        "zipf": zipf(con),
    }
    (OUT / "p02_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "zipf"}, indent=2, ensure_ascii=False))
    for thr, r in stats["zipf"].items():
        print(f"Zipf umbral {thr}/km²: {r['aglomeraciones']} aglomeraciones · exponente {r['exponente_zipf']} "
              f"(R² {r['r2']}) · primacía {r['primacia_1_sobre_2']} · la mayor tiene {r['pct_construcciones_en_la_mayor']}%")
        print("   top5:", [(t["construcciones"], t["lat"], t["lng"]) for t in r["top10"][:5]])


if __name__ == "__main__":
    main()
