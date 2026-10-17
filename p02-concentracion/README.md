# P02 · La Venezuela concentrada

**La mitad de las construcciones de Venezuela está en menos del 1% de su territorio** (0,50% medido en celdas de ~5 km²).

> **EN** · *Concentrated Venezuela*: half of Venezuela's 10.9 million structures (rooftops) sit on less than 1% of its land (0.50% on ~5 km² hexagons), and in more than half of the country there isn't a single rooftop at that scale. Spatial Gini = 0.95; statistically significant hot spots (Getis-Ord Gi\*, Monte Carlo p-values, FDR-corrected) cover 0.35% of the land and hold 36.4% of all structures. The video was recorded in [GeoLibre](https://geolibre.app) with its Time Slider, lighting the country up from densest to emptiest. Use **Open in GeoLibre** below to play it yourself.

Parte de las 10.861.395 construcciones de [P01](../p01-edificios-overture/) (contornos de techo de Overture Maps, release 2026-09-23.1). Una casa cuenta como una y una torre también: son techos, no viviendas ni personas.

## Ábrelo tú mismo

**[Abrir en GeoLibre](https://web.geolibre.app/?welcome=0&theme=dark&url=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp02-concentracion%2Fgeolibre%2Fp02_concentracion.geolibre.json)**: Venezuela en hexágonos 3D sobre un mapa oscuro, con el Time Slider listo. Dale ▶ (o avanza con ⏭) para encenderla de lo más denso a lo más vacío.

El slider muestra "años" de 1901 a 2000: cada año es un **porcentaje acumulado de construcciones** (1901 = 1%, 1950 = 50%, 2000 = 100%). Se hizo así porque el Time Slider de GeoLibre solo acepta fechas o años. El campo real está en la capa como `pct_acumulado`.

## Hallazgos

| Hallazgo | Cifra | Robustez |
|---|---|---|
| La mitad de las construcciones está en… | **0,50% del territorio** (celdas de ~5 km²) | Menos del 1% con celdas de hasta ~36 km²: 0,91% (~36 km²), 0,50% (~5 km²), 0,35% (~0,74 km²). Sin techos < 20 m²: 0,50%. Si las zonas densas tuvieran el doble de techos de los reales: 0,93% |
| El 90% de las construcciones está en… | 6,27% del territorio | 10,1% / 6,27% / 3,65% según la escala |
| Territorio sin ninguna construcción | **54,4%** en celdas de ~5 km² | **Depende mucho de la escala**: 34,6% (~36 km²) · 54,4% (~5 km²) · 78,5% (~0,74 km²). Por eso siempre se dice con la escala |
| Todos los techos del país juntos | 1.155,6 km² = 0,13% de Venezuela | Techo mediano: 69 m² |

### Estadística espacial

- **Gini espacial = 0,95** (0 = construcciones repartidas por igual en el territorio; 1 = todas en un solo punto). Calculado con las 192.832 celdas de ~5 km² del país, incluidas las vacías; 0,90 solo entre las celdas con construcciones. Ver [`output/lorenz.png`](output/lorenz.png).
- **Puntos calientes (Getis-Ord Gi\*)**, con la celda y sus 6 vecinas, p-valores por Monte Carlo (5 millones de simulaciones) y corrección por comparaciones múltiples (FDR de Benjamini-Hochberg): **688 celdas son puntos calientes al 99%: el 0,35% del territorio con el 36,4% de las construcciones**. Capa: [`output/hex_r7_gistar.parquet`](output/hex_r7_gistar.parquet); detalle en [`output/p02_gistar.json`](output/p02_gistar.json).
  - Una versión anterior tomaba el p-valor de la curva normal y daba 3.085 celdas (65,7% de las construcciones en el 1,56% del territorio). Con datos tan sesgados (54% de celdas vacías), la normal exagera la significancia: donde ella marca p = 0,00016, la probabilidad simulada es 0,036.
  - Puntos fríos solo al 90%: las grandes zonas sin ningún techo (65.131 celdas, el 34% del territorio). Ninguno al 95% ni al 99%, porque con tantas celdas vacías una vecindad vacía nunca es tan improbable (su p no baja de 0,027).
- **No hay una ciudad dominante.** Las aglomeraciones urbanas se definen con los datos: celdas de ~0,74 km² contiguas por encima de un umbral de densidad. La más grande tiene solo 1,28 veces las construcciones de la segunda (1,31 y 1,36 con umbrales de 150 y 400 construcciones/km²). Ver [`output/aglomeraciones.parquet`](output/aglomeraciones.parquet).
  - Las manchas urbanas continuas más grandes (umbral 250) son **Maracaibo (617 mil)**, Valencia (483 mil), Caracas (399 mil), Barquisimeto (345 mil), Ciudad Guayana (214 mil) y Maracay (197 mil).
  - **Caracas aparece tercera porque el Ávila y los cerros la parten en varios núcleos** (valle principal, Valles del Tuy, Guarenas-Guatire, Los Teques, litoral). Si a todas las ciudades se les suman las manchas a menos de 45 km del centro de la principal, **Caracas (805 mil) queda a la par de Maracaibo (803 mil)**; a 30 km, Maracaibo sigue primera (694 mil contra 549 mil). Ver [`output/p02_aglomeraciones.json`](output/p02_aglomeraciones.json).
  - **Ley de Zipf**: el tamaño de las ciudades cae con su rango de forma parecida a la ley de Zipf, pero el exponente depende de cuántas aglomeraciones entren en el ajuste: 0,77 con las 10 mayores, 0,87 con 50, 1,02 con 100 y 1,12 con 200 (con R² de 0,94 a 0,98 en todos los casos). Por eso no damos un único exponente. Ver [`output/zipf.png`](output/zipf.png) (ajuste con las 50 mayores).

### ¿Dónde hay más techos? Depende de la escala y de quién los dibujó

- Con celdas de **~5 km²**, la celda con más construcciones está en **Barquisimeto** (19.087).
- Con celdas de **~0,1 km²** (casi una manzana), son barrios populares de **Caracas**: Ruperto Lugo y Barrio Obrero (Catia), con 995 construcciones y techos medianos de 37 m².
- **No son necesariamente los lugares más densos del país**, porque cada fuente dibuja los techos distinto. Esas celdas de Catia las trazaron a mano, casa por casa, voluntarios de OpenStreetMap (96-98% de sus techos), mientras que en todo el Distrito Capital OSM es el 22,6%. Entre las celdas compactas de Caracas (≥35% del suelo techado), las de OSM cuentan el doble de techos que las de IA con una cobertura parecida (563 contra 282 por celda): son el 17% de esas celdas, pero el 60% de las 50 con más techos.
- Entre ciudades pasa lo mismo: de las 10 celdas de ~5 km² con más techos, las de Barquisimeto vienen sobre todo de Google (77-98%), las de Maracaibo de Microsoft (59-72%) y las de Caracas mezclan OpenStreetMap y Google. Compararlas es comparar también fuentes. Ver [`output/p02_fuentes.json`](output/p02_fuentes.json).

Ubicaciones verificadas con geocodificación inversa de OpenStreetMap (Nominatim).

## Limitaciones

- Son **techos, no personas**: una torre de apartamentos cuenta como uno. Caracas, que crece en altura, aparece subestimada frente a ciudades de casas bajas.
- **Cada fuente dibuja los techos distinto** (voluntarios de OSM, Google, Microsoft), así que las comparaciones finas entre lugares dependen de qué fuente cubrió cada zona. El titular aguanta: aunque las celdas densas (≥2.000 construcciones en ~5 km²) tuvieran el doble de techos de los reales, la mitad seguiría en el 0,93% del territorio.
- En zonas de selva (Amazonas, Bolívar), la IA puede no detectar techos bajo los árboles, así que parte del "vacío" puede no ser real.
- Cada construcción se asigna a la celda que contiene su centro. Por eso el porcentaje de suelo techado puede superar el 100% en celdas con techos gigantes; esa métrica no se usa aquí.

## Reproducir

```bash
pip install -r ../requirements.txt
python -P ../common/boundaries.py   # límites de Venezuela
# requiere haber corrido P01 (genera p01-edificios-overture/output/ven_edificios.parquet)
python -P analyze.py           # áreas de techo, métricas H3, curva de concentración, tops
python -P stats.py             # Gini + Lorenz, Zipf
python -P robustness.py        # tests de escala y de calidad
python -P layers.py            # capa del Time Slider (pct_acumulado y anio)
python -P gistar.py            # puntos calientes Gi* con p-valores por Monte Carlo
python -P aglomeraciones.py    # áreas metropolitanas con la misma regla y sensibilidad de Zipf
python -P fuentes.py           # cuánto cambia la densidad según la fuente (lee recuadros de Overture)
python -P geolibre_project.py --base <url de esta carpeta>   # proyecto de GeoLibre
```

`gistar.py`, `aglomeraciones.py` y `fuentes.py` parten de las capas publicadas en `output/` (y `fuentes.py`, de la capa de Caracas de P01), así que se pueden correr sin rehacer P01.

### Video

Se grabó dentro de GeoLibre, cuadro a cuadro: [`video/record_slider.py`](video/record_slider.py) abre el proyecto, oculta la barra de años y avanza el Time Slider paso a paso; [`video/steps.py`](video/steps.py) calcula el contador y [`video/edit_slider.py`](video/edit_slider.py) dibuja los textos. Para probar capas locales en GeoLibre hace falta un servidor con lectura por rangos: [`../common/serve_range.py`](../common/serve_range.py).

Fuentes y licencias: [`../DATA_SOURCES.md`](../DATA_SOURCES.md).
