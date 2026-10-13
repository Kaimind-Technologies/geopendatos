# Venezuela en datos abiertos

Una serie de **Kaimind** que explora Venezuela con datos abiertos y herramientas open source. Cada carpeta acompaña una publicación y contiene el código para reproducirla.

> **EN** · *Venezuela through open data*: a **Kaimind** series exploring Venezuela with open data and open-source tools. Each folder accompanies a post and contains the code to reproduce it.

| # | Publicación / Post | Carpeta / Folder |
|---|---|---|
| P01 | ¿Cuántas construcciones tiene Venezuela? / How many structures does Venezuela have? | [`p01-edificios-overture/`](p01-edificios-overture/) |

## Stack

DuckDB · GeoParquet · H3 · Overture Maps · geoBoundaries · GeoLibre

## Requisitos

```bash
pip install -r requirements.txt
python -P common/boundaries.py
```

Fuentes y licencias de datos en [`DATA_SOURCES.md`](DATA_SOURCES.md). Código bajo licencia MIT.
