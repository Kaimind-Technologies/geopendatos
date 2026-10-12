"""Paso 1 de P01: extrae de Overture Maps (S3 público) los edificios dentro del
recuadro de Venezuela y los guarda en un GeoParquet local. Mide tiempo y datos
transferidos por la red para poder sostener el titular del post.

Uso (desde cualquier carpeta):
    python -P extract.py
"""

import json
import time
from pathlib import Path

import duckdb
import psutil

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "2026-09-23.1"
SOURCE = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=buildings/type=building/*.parquet"
BOUNDARY = ROOT / "data" / "boundaries" / "gb-VEN-ADM0.geojson"
OUT = ROOT / "data" / "overture" / f"ven_buildings_bbox_{RELEASE}.parquet"
METRICS = Path(__file__).resolve().parent / "output" / "extract_metrics.json"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    con.execute("SET s3_region='us-west-2'; SET enable_progress_bar=false;")

    xmin, ymin, xmax, ymax = con.execute(
        f"SELECT ST_XMin(geom), ST_YMin(geom), ST_XMax(geom), ST_YMax(geom) FROM ST_Read('{BOUNDARY.as_posix()}')"
    ).fetchone()

    net_before = psutil.net_io_counters().bytes_recv
    t0 = time.perf_counter()
    con.execute(f"""
        COPY (
            SELECT id, sources, subtype, class, num_floors, height, bbox, geometry
            FROM read_parquet('{SOURCE}')
            WHERE bbox.xmin <= {xmax} AND bbox.xmax >= {xmin}
              AND bbox.ymin <= {ymax} AND bbox.ymax >= {ymin}
        ) TO '{OUT.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
    """)
    elapsed = time.perf_counter() - t0
    net_mb = (psutil.net_io_counters().bytes_recv - net_before) / 1e6

    rows = con.execute(f"SELECT count(*) FROM read_parquet('{OUT.as_posix()}')").fetchone()[0]
    metrics = {
        "release": RELEASE,
        "bbox": [xmin, ymin, xmax, ymax],
        "rows_in_bbox": rows,
        "seconds": round(elapsed, 1),
        "network_mb_received_system_wide": round(net_mb, 1),
        "local_file_mb": round(OUT.stat().st_size / 1e6, 1),
    }
    METRICS.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
