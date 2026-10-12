"""Descarga los límites de Venezuela (país y estados) de geoBoundaries gbOpen.

Fuente: OCHA Venezuela / INE, licencia CC BY 3.0 IGO. El polígono no incluye
la Guayana Esequiba. Se descarga desde el mirror de GitHub de geoBoundaries.

Uso:
    python -P common/boundaries.py
"""

import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parents[1] / "data" / "boundaries"
BASE = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/VEN"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for level in ("ADM0", "ADM1"):
        url = f"{BASE}/{level}/geoBoundaries-VEN-{level}_simplified.geojson"
        target = DEST / f"gb-VEN-{level}.geojson"
        urllib.request.urlretrieve(url, target)
        print(f"{target.name}: {target.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
