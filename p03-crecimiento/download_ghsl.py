"""Descarga los tiles del GHSL (JRC, R2023A, 100 m, Mollweide ESRI:54009) que cubren
Venezuela: superficie construida (GHS-BUILT-S) y población (GHS-POP), épocas
1975-2020. Las épocas 2025 y 2030 son proyecciones y no se descargan.

Épocas observadas por satélite según el GHSL Data Package 2023: 1975, 1990, 2000
(Landsat), 2014 (Landsat) y 2018 (Sentinel-2). Las demás épocas de 5 años son
interpolaciones del propio GHSL.

Licencia: CC BY 4.0 (European Commission, Joint Research Centre).

Uso:
    python -P download_ghsl.py
"""

import io
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "ghsl"
BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
EPOCHS = range(1975, 2021, 5)
# Grilla GHSL de 1000 km en Mollweide; tiles que tocan el recuadro de Venezuela (verificado con R8_C12 = Caracas).
TILES = ["R8_C11", "R8_C12", "R8_C13", "R9_C11", "R9_C12", "R9_C13"]
DATASETS = {
    "BUILT_S": "GHS_BUILT_S_GLOBE_R2023A/GHS_BUILT_S_E{e}_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_BUILT_S_E{e}_GLOBE_R2023A_54009_100_V1_0_{t}.zip",
    "POP": "GHS_POP_GLOBE_R2023A/GHS_POP_E{e}_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_POP_E{e}_GLOBE_R2023A_54009_100_V1_0_{t}.zip",
}


def main() -> None:
    for name, pattern in DATASETS.items():
        for e in EPOCHS:
            out_dir = DEST / name / str(e)
            out_dir.mkdir(parents=True, exist_ok=True)
            for t in TILES:
                if any(out_dir.glob(f"*{t}.tif")):
                    continue
                url = f"{BASE}/{pattern.format(e=e, t=t)}"
                try:
                    data = urllib.request.urlopen(url, timeout=120).read()
                except urllib.error.HTTPError as err:
                    print(f"{name} {e} {t}: HTTP {err.code} (tile sin tierra o inexistente)")
                    continue
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for member in z.namelist():
                        if member.endswith(".tif"):
                            (out_dir / Path(member).name).write_bytes(z.read(member))
                print(f"{name} {e} {t}: {len(data) / 1e6:.1f} MB", flush=True)
    total = sum(f.stat().st_size for f in DEST.rglob("*.tif"))
    print(f"listo: {total / 1e9:.2f} GB en {DEST}")


if __name__ == "__main__":
    main()
