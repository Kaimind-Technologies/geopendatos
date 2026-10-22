# Fuentes de datos y atribución

| Fuente | Uso | Licencia | Atribución |
|---|---|---|---|
| [Overture Maps](https://overturemaps.org), tema *buildings*, release 2026-09-23.1 | Edificios (P01) | ODbL (incluye OpenStreetMap; también Microsoft ML Buildings y Google Open Buildings) | © OpenStreetMap contributors, Overture Maps Foundation |
| [geoBoundaries](https://www.geoboundaries.org) gbOpen VEN ADM0/ADM1/ADM2 | Límites del país, estados y municipios (sin Guayana Esequiba; ADM2 solo para asignar municipios a ciudades en la validación de P03) | CC BY 3.0 IGO | geoBoundaries (Runfola et al., 2020); fuente: OCHA Venezuela / Instituto Nacional de Estadística |
| INE, XIV Censo Nacional de Población y Vivienda 2011 | Validación (viviendas por estado, Cuadro 6.1, P01; población por estado y por municipio 2001 y 2011, Cuadro 2.2 de cada publicación estatal, P03; totales censales 1990, 2001 y 2011, P03) | Publicación oficial | Instituto Nacional de Estadística de Venezuela |
| INE, estimaciones de población por municipio, vía [citypopulation.de](https://www.citypopulation.de/en/venezuela/admin/) | Sensibilidad a la omisión censal (P03, `VALIDACION.md` T2 y T5) | Publicación oficial (cifras del INE recopiladas por Th. Brinkhoff) | Instituto Nacional de Estadística de Venezuela |
| [GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/datasets.php) (GHSL, JRC) | Superficie construida 1975-2020, 100 m (P03). No se usan las épocas proyectadas 2025 y 2030 | CC BY 4.0 | Pesaresi, M., Politis, P. (2023), European Commission, Joint Research Centre. doi:[10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA](https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA) |
| [GHS-POP R2023A](https://human-settlement.emergency.copernicus.eu/datasets.php) (GHSL, JRC) | Población modelada 1975-2020, 100 m (P03) | CC BY 4.0 | European Commission, Joint Research Centre (2023). doi:[10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE](https://doi.org/10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE) |
| [World Settlement Footprint Evolution](https://geoservice.dlr.de/web/datasets/wsf_evo) (DLR) | Año de primera detección de asentamiento 1985-2015, 30 m (P03) | CC BY 4.0 | © DLR. Marconcini, M., Metz-Marconcini, A., Esch, T., Gorelick, N. (2021), *Understanding Current Trends in Global Urbanisation – The World Settlement Footprint Suite*, GI_Forum 2021 (1), 33-38 |
| [Nominatim](https://nominatim.openstreetmap.org) (OpenStreetMap) | Verificación de nombres de lugares (geocodificación inversa, P02 y P03); no se redistribuyen datos | ODbL | © OpenStreetMap contributors |
| [CARTO](https://carto.com/basemaps) Dark Matter | Mapa base oscuro de los proyectos de GeoLibre (P02, P03) | Términos de CARTO | © CARTO, © OpenStreetMap contributors |

Los datos derivados en `output/` de P01 y P02 (GeoParquet) heredan la licencia ODbL de Overture. Los de P03 derivan de GHSL y WSF-Evolution (CC BY 4.0) y se publican con la misma licencia y atribución.
