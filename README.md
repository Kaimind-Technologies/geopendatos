# Venezuela en datos abiertos

Una serie de **Kaimind** que explora Venezuela con datos abiertos y herramientas open source. Cada carpeta acompaña una publicación y contiene el código para reproducirla.

| # | Publicación | Carpeta |
|---|---|---|
| P01 | ¿Cuántos edificios tiene Venezuela? | [`p01-edificios-overture/`](p01-edificios-overture/) |

## Stack

DuckDB · GeoParquet · H3 · Overture Maps · geoBoundaries · GeoLibre

## Requisitos

```bash
pip install -r requirements.txt
python -P common/boundaries.py
```

Fuentes y licencias de datos en [`DATA_SOURCES.md`](DATA_SOURCES.md). Código bajo licencia MIT.
