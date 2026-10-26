# Venezuela en datos abiertos

Una serie de **Kaimind** que explora Venezuela con datos abiertos y herramientas open source. Cada carpeta acompaña una publicación y contiene el código para reproducirla.

> **EN** · *Venezuela through open data*: a **Kaimind** series exploring Venezuela with open data and open-source tools. Each folder accompanies a post and contains the code to reproduce it.

| # | Publicación / Post | Carpeta / Folder |
|---|---|---|
| P01 | ¿Cuántas construcciones tiene Venezuela? / How many structures does Venezuela have? | [`p01-edificios-overture/`](p01-edificios-overture/) |
| P02 | La Venezuela concentrada / Concentrated Venezuela | [`p02-concentracion/`](p02-concentracion/) |
| P03 | Así crecieron las ciudades de Venezuela, 1985-2015 / How Venezuela's cities grew, 1985-2015 | [`p03-crecimiento/`](p03-crecimiento/) |

## API abierta v0

Cada cifra verificada de la serie está publicada como JSON estático en el sitio (`/api/v0/`): indicadores, los 25 estados, ciudades, la serie de asentamiento 1985-2015, el catálogo de capas GeoParquet y el registro de lo que descartamos. Cada recurso trae su método, sus fuentes, las pruebas que pasó y su licencia. La genera [`api/build_api.py`](api/build_api.py) a partir de los `output/*.json` de cada publicación, con pruebas de coherencia; el despliegue se detiene si la API publicada no coincide con los datos del repo.

> **EN** · Every verified figure in the series is published as static JSON on the site (`/api/v0/`), each with its method, sources, tests and license.

```bash
python -P api/build_api.py           # regenera web/public/api/v0/
python -P api/build_api.py --check   # comprueba que esté al día
```

## Stack

DuckDB · GeoParquet · H3 · Overture Maps · GHSL · WSF-Evolution · geoBoundaries · rasterio · GeoLibre (Time Slider, 3D) · estadística espacial (Gini, Getis-Ord Gi\*, Zipf, tipología LEI, ODS 11.3.1)

Sitio web del proyecto (ES/EN) en [`web/`](web/).

Utilidades compartidas en [`common/`](common/): límites de Venezuela, un servidor local con lectura por rangos para probar capas en GeoLibre, y un puente para exportar el estado de un proyecto de GeoLibre.

## Requisitos

```bash
pip install -r requirements.txt
python -P common/boundaries.py
```

Fuentes y licencias de datos en [`DATA_SOURCES.md`](DATA_SOURCES.md). Código bajo licencia MIT.


