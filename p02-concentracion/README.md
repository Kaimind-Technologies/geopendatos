# P02 · La Venezuela concentrada

**La mitad de las construcciones de Venezuela está en menos del 1% de su territorio** (0,50% medido en celdas de ~5 km²).

> **EN** · *Concentrated Venezuela*: half of Venezuela's 10.9 million structures (rooftops) sit on less than 1% of its land (0.50% on ~5 km² hexagons), and in more than half of the country there isn't a single rooftop at that scale. Spatial Gini = 0.95; statistically significant hot spots (Getis-Ord Gi\*, FDR-corrected) cover 1.56% of the land and hold 65.7% of all structures. The video was recorded in [GeoLibre](https://geolibre.app) with its Time Slider, lighting the country up from densest to emptiest. Use **Open in GeoLibre** below to play it yourself.

Parte de las 10.861.395 construcciones de [P01](../p01-edificios-overture/) (contornos de techo de Overture Maps, release 2026-09-23.1). Una casa cuenta como una y una torre también: son techos, no viviendas ni personas.

## Ábrelo tú mismo

**[Abrir en GeoLibre](https://web.geolibre.app/?welcome=0&theme=dark&url=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp02-concentracion%2Fgeolibre%2Fp02_concentracion.geolibre.json)**: Venezuela en hexágonos 3D sobre un mapa oscuro, con el Time Slider listo. Dale ▶ (o avanza con ⏭) para encenderla de lo más denso a lo más vacío.

El slider muestra "años" de 1901 a 2000: cada año es un **porcentaje acumulado de construcciones** (1901 = 1%, 1950 = 50%, 2000 = 100%). Se hizo así porque el Time Slider de GeoLibre solo acepta fechas o años. El campo real está en la capa como `pct_acumulado`.

## Hallazgos

| Hallazgo | Cifra | Robustez |
|---|---|---|
| La mitad de las construcciones está en… | **0,50% del territorio** (celdas de ~5 km²) | Menos del 1% con cualquier escala probada: 0,91% (~36 km²), 0,50% (~5 km²), 0,35% (~0,74 km²). Sin techos < 20 m²: 0,50% |
| El 90% de las construcciones está en… | 6,27% del territorio | 10,1% / 6,27% / 3,65% según la escala |
| Territorio sin ninguna construcción | **54,4%** en celdas de ~5 km² | **Depende mucho de la escala**: 34,6% (~36 km²) · 54,4% (~5 km²) · 78,5% (~0,74 km²). Por eso siempre se dice con la escala |
| Todos los techos del país juntos | 1.155,6 km² = 0,13% de Venezuela | Techo mediano: 69 m² |

### Estadística espacial

- **Gini espacial = 0,95** (0 = construcciones repartidas por igual en el territorio; 1 = todas en un solo punto). Calculado con las 192.832 celdas de ~5 km² del país, incluidas las vacías; 0,90 solo entre las celdas con construcciones. Ver [`output/lorenz.png`](output/lorenz.png).
- **Puntos calientes (Getis-Ord Gi\*)**, con la celda y sus 6 vecinas y corrección por comparaciones múltiples (FDR de Benjamini-Hochberg): **3.085 celdas son puntos calientes al 99%: el 1,56% del territorio con el 65,7% de las construcciones**. No hay puntos fríos significativos, algo esperable en una distribución tan sesgada. Capa: [`output/hex_r7_gistar.parquet`](output/hex_r7_gistar.parquet).
- **Ley de Zipf**: aglomeraciones urbanas definidas por los datos (celdas de ~0,74 km² contiguas por encima de un umbral de densidad). El exponente es 0,88 / 0,87 / 0,90 con umbrales de 150 / 250 / 400 construcciones/km² (R² 0,96-0,98). Ver [`output/zipf.png`](output/zipf.png) y [`output/aglomeraciones.parquet`](output/aglomeraciones.parquet).
  - Las manchas urbanas continuas más grandes (umbral 250) son **Maracaibo (617 mil)**, Valencia (483 mil), Caracas (399 mil), Barquisimeto (345 mil), Ciudad Guayana (214 mil) y Maracay (197 mil).
  - **Caracas aparece tercera porque el Ávila y los cerros la parten en 8 núcleos** (valle principal, Valles del Tuy, Guarenas-Guatire, Los Teques, litoral y otros). Su área metropolitana suma **701 mil** construcciones, más que Maracaibo.

### La zona más construida depende de la escala

- Con celdas de **~5 km²**, la más densa está en **Barquisimeto** (19.087 construcciones).
- Con celdas de **~0,1 km²** (casi una manzana), las más densas son barrios populares de **Caracas**: Ruperto Lugo y Barrio Obrero (Catia), con 995 construcciones y techos medianos de 37 m², seguidos por El Cementerio, Petare Norte y Antímano.

Ubicaciones verificadas con geocodificación inversa de OpenStreetMap (Nominatim).

## Limitaciones

- Son **techos, no personas**: una torre de apartamentos cuenta como uno. Caracas, que crece en altura, aparece subestimada frente a ciudades de casas bajas.
- En zonas de selva (Amazonas, Bolívar), la IA puede no detectar techos bajo los árboles, así que parte del "vacío" puede no ser real.
- Cada construcción se asigna a la celda que contiene su centro. Por eso el porcentaje de suelo techado puede superar el 100% en celdas con techos gigantes; esa métrica no se usa aquí.

## Reproducir

```bash
pip install -r ../requirements.txt
# requiere haber corrido P01 (genera p01-edificios-overture/output/ven_edificios.parquet)
python -P analyze.py           # áreas de techo, métricas H3, curva de concentración, tops
python -P stats.py             # Gini + Lorenz, Getis-Ord Gi*, Zipf
python -P robustness.py        # tests de escala y de calidad
python -P layers.py            # capa del Time Slider (pct_acumulado y anio)
python -P geolibre_project.py --base <url de esta carpeta>   # proyecto de GeoLibre
```

### Video

Se grabó dentro de GeoLibre, cuadro a cuadro: [`video/record_slider.py`](video/record_slider.py) abre el proyecto, oculta la barra de años y avanza el Time Slider paso a paso; [`video/steps.py`](video/steps.py) calcula el contador y [`video/edit_slider.py`](video/edit_slider.py) dibuja los textos. Para probar capas locales en GeoLibre hace falta un servidor con lectura por rangos: [`../common/serve_range.py`](../common/serve_range.py).

Fuentes y licencias: [`../DATA_SOURCES.md`](../DATA_SOURCES.md).
