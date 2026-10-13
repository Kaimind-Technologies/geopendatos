# P01 · ¿Cuántas construcciones tiene Venezuela?

Venezuela no tiene censo desde 2011, pero los mapas abiertos ya contaron sus construcciones: **10.861.395** (Overture Maps, release 2026-09-23.1).

> **EN** · Venezuela hasn't had a census since 2011, but open maps have already counted its structures: **10,861,395 rooftops** (Overture Maps, release 2026-09-23.1). 92% were traced by AI in satellite imagery (Microsoft 48%, Google 44%) and 8% by OpenStreetMap volunteers. A house counts as one, and so does a 20-storey tower: this is a count of rooftops, not of dwellings. We queried the 277 GB global dataset straight from the cloud with DuckDB, transferring only ~5 GB, and recorded the video in [GeoLibre](https://geolibre.app). Use the **Open in GeoLibre** link below to explore it in your browser.

![Mapa de construcciones de Venezuela](output/mapa_p01.png)

## Resultados

| | |
|---|---|
| Construcciones detectadas | **10.861.395** |
| Detectadas por IA | 92,1% (Microsoft 47,9% · Google 44,2%) |
| Mapeadas por voluntarios (OpenStreetMap) | 7,9% |
| Estado con más construcciones | Zulia (1.554.330) |

Top 5: Zulia 1.554.330 · Lara 824.152 · Carabobo 751.634 · Miranda 738.954 · Anzoátegui 657.925. Detalle completo en [`output/p01_cifras.json`](output/p01_cifras.json).

## ¿Qué cuenta como construcción?

Cada construcción es **el contorno de un techo** (huella o *footprint*): un polígono que marca una construcción vista desde arriba, en el tema `buildings` de Overture Maps (solo el tipo `building`; no se cuentan las partes de edificio). Viene de una de estas fuentes:

- **Dibujada por voluntarios** de OpenStreetMap: 7,9%.
- **Detectada por IA en imágenes satelitales:** Microsoft ML Buildings (47,9%, imágenes de Bing de 2014 a 2024) y Google Open Buildings (44,2%).

**Incluye:** casas, quintas y ranchos (**una casa cuenta como una**); edificios de apartamentos (**una torre también cuenta como una**, sin importar sus pisos); comercios, industrias, galpones, escuelas e iglesias; y anexos con techo propio, como cocinas aparte, depósitos o techos de estacionamiento (el 19% de las detectadas por Google mide menos de 20 m²).

**No es:** un conteo de edificios en altura, de viviendas, de hogares ni de personas, ni una cifra oficial. Solo el 1,4% de las construcciones trae datos de pisos o altura, así que por ahora no se pueden separar casas de edificios.

**Limitaciones:**

- Las imágenes satelitales son de distintos años, así que las construcciones recientes pueden faltar.
- La IA puede unir techos pegados en zonas muy densas (cuenta de menos) o detectar estructuras que no son construcciones (cuenta de más).
- Cada construcción se asigna al estado que contiene el centro de su techo, dentro de los límites de geoBoundaries (sin la Guayana Esequiba).
- No hay duplicados entre fuentes: Overture las fusiona, y en Caracas solo el 0,03% de los techos se solapa con otro.

**Construcción ≠ vivienda.** Frente a las 8.216.443 viviendas del censo 2011 hay 1,32 construcciones por vivienda, con un patrón claro: en el Distrito Capital hay 2,4 viviendas por construcción (torres de apartamentos) y en Apure, 2 construcciones por vivienda (anexos rurales).

## Ábrelo tú mismo

**[Abrir en GeoLibre](https://web.geolibre.app/?welcome=0&theme=dark&data=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp01-edificios-overture%2Foutput%2Fven_h3_r7.parquet&data=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp01-edificios-overture%2Foutput%2Fcaracas_edificios.parquet&style=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp01-edificios-overture%2Fstyles%2Fh3.style.json&style=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp01-edificios-overture%2Fstyles%2Fcaracas.style.json)**: el país en hexágonos 3D y cada construcción de Caracas coloreada por fuente, en [GeoLibre](https://geolibre.app), un SIG que corre en el navegador. Para el 3D, inclina el mapa con clic derecho + arrastrar.

También puedes descargar [`output/ven_h3_r7.parquet`](output/ven_h3_r7.parquet) (país en hexágonos de ~5 km²) o [`output/caracas_edificios.parquet`](output/caracas_edificios.parquet) (cada construcción del Distrito Capital) y abrirlos en cualquier SIG. Los estilos están en [`styles/`](styles/).

## Video

El video del post se grabó dentro de GeoLibre, cuadro a cuadro: [`video/record.py`](video/record.py) maneja la cámara con el mouse (Playwright + Chrome) y [`video/edit.py`](video/edit.py) agrega los textos con ffmpeg.

## Reproducir

```bash
pip install -r ../requirements.txt
python -P ../common/boundaries.py   # límites de Venezuela y estados
python -P extract.py                # Overture (S3) -> GeoParquet local, mide tiempo y red
python -P analyze.py                # asignación por estado + cifras
python -P layers.py                 # hexágonos H3 + mapa
```

La consulta central, en SQL puro: [`query.sql`](query.sql).

## Método

- Extracción con DuckDB directo desde S3, filtrando por el `bbox` de cada construcción: el dataset mundial pesa 276,9 GB (512 archivos) y se transfirieron unos 5 GB.
- Cada construcción se asigna al estado que contiene el centro de su `bbox` (join espacial indexado).
- Validación: correlación 0,87 con las viviendas del censo 2011 por estado; 0,03% de posibles duplicados en Caracas.

Fuentes y licencias: [`../DATA_SOURCES.md`](../DATA_SOURCES.md).
