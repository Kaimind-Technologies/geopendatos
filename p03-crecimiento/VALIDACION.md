# P03 · Validación antes de publicar

Antes de publicar P03 sometimos cada afirmación del [`README`](README.md) a pruebas que podían tumbarla. No buscamos confirmar los hallazgos: buscamos la variante razonable del método o de los datos que los cambia. Este documento complementa las verificaciones de [`PROCESO.md`](PROCESO.md) §3 (dos fuentes de suelo, modelo contra censo, matriz 2×2) con cinco pruebas nuevas y una regla de lenguaje.

## Cómo decidimos qué se publica

| Veredicto | Criterio | Cómo se publica |
|---|---|---|
| ✅ **Se publica** | Se sostiene con las dos fuentes de suelo, con población de modelo y de censo, y en **todas** las variantes razonables del método (escala, umbrales, anillos, ventanas de tiempo) | Como rango o redondeada, nunca con más precisión de la que resiste |
| 🟡 **Se publica con matices** | La **dirección** se sostiene en todas las variantes, pero la magnitud no; o es cierta pero se presta a una lectura exagerada | Sin cifra exacta, o con rango, y con la advertencia al lado |
| ❌ **No se publica** | Alguna variante razonable la invierte o la deja sin lectura | Va a "Lo que descartamos" |

Además, **ninguna afirmación puede decir más que la cifra**: sin causas (crisis, migración, políticas), sin adjetivos ("boom", "explosión", "caos"), sin comparaciones que el dato no hace.

## 0. Reproducibilidad (22 de octubre de 2026)

En una máquina sin datos previos se descargaron de cero el GHSL (0,65 GB) y WSF-Evolution (52 tiles) y se corrió toda la cadena (`prepare.py` → `robustness_matrix.py`, sin `cities.py` para no repetir las consultas a Nominatim).

| Resultado | ¿Igual al publicado? |
|---|---|
| `p03_nacional.json`, `p03_verificacion_wsf.json`, `p03_verificacion_wsf_ciudades.json`, `p03_verificacion_poblacion.json`, `p03_matriz_robustez.json`, `p03_contraste_lei_gistar.json` (incluido el Gi\* con 5 millones de simulaciones) | ✅ idénticos byte a byte |
| `hex_r7_urbanizacion_wsf`, `hex_r8_urbanizacion_wsf`, `hex_r7_mitad_crecimiento` (parquet) | ✅ las mismas filas (los bytes cambian por la versión del escritor de parquet) |

Hallazgo de la prueba: **con DuckDB 2.0 `wsf_layers.py` falla** (cambia el comportamiento de `fetchone()`). Se fijó `duckdb>=1.5.0,<2` en [`requirements.txt`](../requirements.txt); con 1.5.6 todo corre.

## T1. Saltos de un año en la serie anual WSF (`verify_claims.py`)

**Por qué.** WSF-Evolution fecha cada píxel con el primer año en que lo detecta. Si en algunos años hubo pocas imágenes Landsat sin nubes, lo construido en esos años aparece de golpe en el siguiente año con buenas imágenes. El DLR advierte que la calidad varía con la disponibilidad de Landsat (su capa de calidad por año, IDC, no está en el servidor de descarga). La firma de ese artefacto es que **casi todos los estados "saltan" el mismo año**; un auge real de la construcción no ocurre en todo el país a la vez y desaparece al año siguiente.

**Método.** Superficie nueva por estado y año (23 estados con al menos 20 km² de asentamiento). Un año "salta" en un estado si suma al menos el doble de su incremento anual mediano.

| | 1991 | 1992-1995 | 1996 | 1997-1998 | 2000-2015 (máximo de un año) |
|---|---|---|---|---|---|
| Incremento nacional ÷ mediana | **2,29** | 0,41-0,82 | **2,44** | 1,71-1,83 | 0,74-1,29 |
| Estados que saltan a la vez | **14 de 23** | 0-2 | **19 de 23** | 9-10 | 3 |

**Lectura.** Los saltos de 1991 y 1996, precedidos por años anormalmente bajos, tienen la firma de un artefacto de disponibilidad de imágenes. Después de 2000 la serie es estable.

**Consecuencias:**

1. 🟡 **"Las ciudades crecieron más rápido en los 90 que en 2000-2015" se sostiene en dirección.** Tal cual: 72 km²/año (2,28%/año) frente a 56 km²/año (1,40%/año). Escenario pesimista, en el que los 71 km² de exceso de 1991 ya existían antes de 1990: 65 km²/año (2,03%/año), todavía más que después de 2000. Para que se empataran, **169 km²** fechados en 1991-2000 tendrían que ser anteriores a 1990 (en km²/año), es decir 2,4 veces el exceso de 1991. Coinciden el GHSL (3,28 frente a 1,42%/año) y la población censal (2,20%/año en 1990-2001 frente a 1,66%/año en 2001-2011). Matiz: GHSL y WSF usan el mismo archivo Landsat, así que su acuerdo no descarta un problema del archivo; por eso el escenario pesimista. **Se publica sin cifra exacta para los 90.**
2. ⚠️ **El contador año a año del video y del Time Slider muestra saltos en 1991 y 1996 que no son auges reales.** No se comenta ningún año concreto antes de 2000, y el post debe aclararlo.

## T2. ODS 11.3.1 nacional con población de censos (`verify_claims.py`)

**Por qué.** La versión publicada usaba la población de GHS-POP, un modelo alineado con la ONU. Aquí se usa la población empadronada de los censos del INE (1990: 18.105.265; 2001: 23.054.210; 2011: 27.227.930), con el suelo WSF de los mismos años censales.

| Período | Población (censo) | Suelo WSF | ODS WSF | Suelo GHSL | ODS GHSL |
|---|---|---|---|---|---|
| 1990-2001 | 2,20%/año | 2,22%/año | 1,01 | 3,28%/año (1990-2000) | 1,49 |
| 2001-2011 | 1,66%/año | 1,46%/año | **0,88** | 1,47%/año (2000-2010) | **0,88** |
| 1990-2011 | 1,94%/año | 1,86%/año | 0,96 | 2,38%/año (1990-2010) | 1,22 |

Sensibilidad a la omisión censal: con la población estimada por el INE (corregida por omisión, 1,54%/año en 2001-2011), el ODS 2001-2011 da 0,95 con las dos fuentes.

**Lectura:**

- ✅ **2000-2015: el suelo urbano no creció más rápido que la población.** Seis combinaciones (2 fuentes de suelo × GHS-POP, censo y estimación del INE) dan entre **0,88 y 0,95**.
- 🟡 **Largo plazo: "≈ 1" solo lo sostiene WSF** (0,96 con censos en 1990-2011; 0,97 con GHS-POP en 1985-2015). El GHSL da 1,07 a 1,22 porque arrastra su salto de los 90, que ya habíamos descartado. Se publica atribuido a WSF, no como coincidencia de dos fuentes.

## T3. Línea base de la concentración (`verify_claims.py`)

**Por qué.** "La mitad del crecimiento cayó en menos del 1% del territorio" suena a un hallazgo de concentración extrema. Pero los asentamientos de Venezuela ocupan apenas el **0,48%** del territorio (WSF 2015). La pregunta honesta es si el crecimiento estuvo más concentrado que las ciudades que ya existían.

| Hexágono H3 | La mitad del crecimiento 2000-2015 (WSF / GHSL) | La mitad de lo que ya existía en 2000 (WSF / GHSL) | Crecimiento ÷ existente | Crecimiento en celdas que ya tenían asentamiento en 2000 |
|---|---|---|---|---|
| ~250 km² (res 5) | **1,85% / 1,47%** | 1,16% / 1,18% | 1,24-1,59 | 99,9-100% |
| ~36 km² (res 6) | 0,80% / 0,65% | 0,52% / 0,53% | 1,21-1,53 | 99,7-100% |
| ~5 km² (res 7) | 0,38% / 0,34% | 0,30% / 0,30% | 1,13-1,30 | 98,9-100% |
| ~0,74 km² (res 8) | 0,20% / 0,19% | 0,22% / 0,22% | 0,88-0,89 | 96,5-99,9% |

**Lectura:**

- La cifra es cierta, pero **no es una concentración nueva**: el crecimiento estuvo tan concentrado como las ciudades que ya existían (algo menos en hexágonos grandes y algo más en los pequeños), y prácticamente todo cayó en zonas que ya tenían asentamiento en 2000.
- **"Menos del 1%" depende del tamaño del hexágono**: con hexágonos de ~250 km² es 1,5-1,9%.
- 🟡 **No se usa como titular.** Si se menciona, va con su línea base: "tan concentrado como las ciudades que ya existían". El hallazgo de fondo, que las ciudades crecieron donde ya estaban, lo dice mejor la tipología (T4).

## T4. Sensibilidad de la tipología LEI 2000-2015 (`verify_claims.py`)

**Por qué.** Los porcentajes de relleno, borde y salto dependen de decisiones de método: el ancho del anillo alrededor de cada mancha nueva, cómo se lleva WSF (~30 m) a la grilla de 100 m y qué umbral define "urbano" en el GHSL. Se corrieron 18 variantes, calculando el índice mancha por mancha (sin la aproximación de `wsf_layers.py`).

| Variante | Anillo 100 m (borde / relleno / salto) | 200 m | 300 m |
|---|---|---|---|
| WSF, cualquier píxel (la publicada) | 51 / 41 / 8 | 60 / 33 / 7 | 66 / 28 / 6 |
| WSF, ≥25% de la celda | 55 / 36 / 8 | 64 / 29 / 7 | 69 / 26 / 6 |
| WSF, ≥50% de la celda | 60 / 32 / 9 | 68 / 26 / 7 | 71 / 23 / 6 |
| GHSL, ≥10% construido | 55 / 39 / 7 | 65 / 30 / 5 | 70 / 26 / 4 |
| GHSL, ≥15% (la publicada) | 58 / 33 / 9 | 68 / 26 / 6 | 72 / 24 / 4 |
| GHSL, ≥20% | 59 / 30 / 11 | 69 / 23 / 8 | 74 / 21 / 6 |

**Lectura:**

- ✅ **La expansión de borde es la forma de crecimiento más común en las 18 variantes** (51-74%).
- ✅ **Relleno + borde, es decir crecimiento pegado a lo ya urbanizado: 89-96% en las 18.** "9 de cada 10 km² nuevos aparecieron junto a zonas que ya eran urbanas."
- 🟡 "Más de la mitad en los bordes" se cumple en las 18, pero en el límite (mínimo 51,4%). Mejor decir "la forma más común".
- ❌ **Los repartos exactos no se publican**: relleno 21-41%, salto 4-11% según el método. El rango del README anterior (relleno 32-38%) subestimaba esa incertidumbre.
- Control: el cálculo exacto difiere a lo sumo 2,2 puntos del aproximado publicado (WSF 51,4/40,6/8,0 frente a 52,8/38,4/8,8; GHSL 58,2/33,2/8,6 frente a 58,1/31,8/10,1).

## T5. Ciudades con el censo de sus municipios (`verify_cities_census.py`)

**Por qué.** La matriz 2×2 usaba el crecimiento censal del **estado** como proxy de la ciudad. El estado incluye pueblos y zonas rurales que crecen a otro ritmo, y la omisión censal cambia entre censos. Ejemplo de cuánto importa: según el censo, Baruta (260.853 → 240.755) y Chacao (64.629 → 61.213) **perdieron** población entre 2001 y 2011, mientras Miranda en conjunto creció 1,4%/año.

**Método.**

- **Municipios de cada ciudad, sin elegirlos a mano:** entra un municipio si al menos el 50% de su población (GHS-POP 2010) vive dentro de la mancha urbana. Esos municipios contienen el 98-100% de la población de cada mancha.
- **Población:** (1) GHS-POP en la mancha, 2000-2015; (2) censo de los estados de esos municipios, 2001-2011; (3) censo de los municipios, 2001-2011 (INE, población empadronada); (4) estimación del INE para los municipios, corregida por omisión, 2001-2011.
- **Suelo:** GHSL 2000-2015, WSF 2000-2015 y WSF 2001-2011 (la misma ventana que los censos).
- **Mancha urbana de 2020:** umbrales de 10, 15 y 20% construido.
- 4 × 3 × 3 = **36 combinaciones por ciudad**, con la regla de siempre: "densificación robusta" solo si las 36 dan ODS < 0,9.
- **Control de los datos:** los municipios transcritos de cada estado suman exactamente el total estatal del censo. El script lo comprueba en cada corrida (`_control_censo_municipal` en la salida).

| Ciudad | Municipios (umbral 15%) | ODS, mín-máx (36 comb.) | ODS solo con censo municipal | Matriz 2×2 → ahora |
|---|---|---|---|---|
| Barquisimeto | Iribarren, Palavecino | 0,32-0,59 | 0,33-0,48 | ✅ → ✅ densificación robusta |
| Barcelona-Puerto La Cruz | Simón Bolívar, Sotillo, Urbaneja, Guanta | 0,29-0,45 | 0,30-0,38 | ✅ → ✅ densificación robusta |
| Margarita | Mariño, García, Díaz, Maneiro, Arismendi, Antolín del Campo | 0,24-0,36 | 0,24-0,29 | ✅ → ✅ densificación robusta |
| Maracaibo | Maracaibo, San Francisco, Jesús Enrique Lossada | 0,28-0,68 (27 comb.: todas menos el censo municipal) | *pendiente: censo de Zulia* | ✅ → ⏳ |
| Valencia | Valencia, Naguanagua, San Diego, Los Guayos, Guacara, Libertador | 0,52-1,06 | 0,62-0,97 | ❌ → ❌ no concluyente |
| Caracas (valle) | Libertador, Sucre, Baruta, Chacao, El Hatillo | 0,43-3,17 | 0,86-1,71 | ❌ → ❌ no concluyente |
| Caracas metropolitana | 13 municipios de DC, Miranda y La Guaira | 0,69-1,84 | 0,90-1,37 | ❌ → ❌ no concluyente |
| Maturín | Maturín | 0,77-1,59 | 0,82-1,13 | ❌ → ❌ no concluyente |
| Maracay-Turmero · Ciudad Guayana · Costa Oriental del Lago | — | 0,40-2,35 · 0,30-1,13 · 0,60-1,39 (27 comb.) | *sin censo municipal (Aragua, Bolívar, Zulia)* | ❌ → ❌ no concluyente (ya lo es sin el censo municipal) |

**Lectura:**

- ✅ **Barquisimeto, Barcelona-Puerto La Cruz y Margarita resisten las 36 combinaciones.** Según la fuente y el umbral, su población creció entre 1,0 y 2,9%/año y su superficie urbanizada entre 0,4 y 0,9%/año.
- **Caracas sigue sin lectura.** Con el censo de sus municipios la población del valle creció 0,50%/año (Libertador +0,6%/año; Baruta y Chacao perdieron población), y el ODS queda entre 0,86 y 1,71 según la fuente de suelo. "Caracas se expandió" sigue descartado; "Caracas se densificó" tampoco se sostiene.
- **Lenguaje:** "se densificaron" se lee a menudo como "mejoraron". El dato solo dice que **su población creció más rápido que su superficie urbanizada**. No dice si eso fue por edificios más altos, por hacinamiento o por ocupación de lotes vacíos.

## Guía de lenguaje

| Evitar | Usar | Por qué |
|---|---|---|
| "La mitad del crecimiento cayó en menos del 1% del territorio" como titular | "9 de cada 10 km² nuevos aparecieron pegados a zonas que ya eran urbanas" | La primera es casi inevitable en un país cuyos asentamientos ocupan el 0,5% del territorio (T3); la segunda es el hallazgo y resiste 18 variantes (T4) |
| "Lo confirman dos fuentes satelitales independientes" | "Coinciden dos productos satelitales elaborados por equipos distintos (JRC y DLR)" | Los dos se basan sobre todo en imágenes Landsat: son métodos independientes, no observaciones independientes |
| "0,38% del territorio", "4.389,4 km²", "52,8% en bordes" | "menos del 1% en hexágonos de hasta ~36 km²", "unos 4.400 km²", "la forma más común" | El decimal depende del hexágono, del contorno del país (±1,5%) y del método (T3, T4) |
| "Maracaibo, Barquisimeto… se densificaron" | "En Barquisimeto, Barcelona-Puerto La Cruz y Margarita la población creció más rápido que la superficie urbanizada" | Dice lo que mide el ODS, sin connotación |
| "Boom", "explosión", "crecimiento desbordado", "caos urbano" | Tasas y comparaciones | El dato no los respalda: en 2000-2015 el suelo creció *más lento* que la población (T2) |
| Comentar un año concreto antes de 2000 ("en 1996 se disparó…") | Hablar de décadas | Los saltos de 1991 y 1996 son artefactos de las imágenes (T1) |
| Causas: crisis, migración, políticas de vivienda | Nada: P03 no mide causas | Ninguna prueba de aquí las sostiene |
| "Entre 2015 y 2020 la población cayó mientras se seguía construyendo" | No se publica | Solo hay una fuente (modelo) y WSF termina en 2015 |

## Qué se publica

| Afirmación | Veredicto | Texto sugerido |
|---|---|---|
| Crecimiento pegado a lo existente, 2000-2015 | ✅ | "9 de cada 10 km² nuevos de asentamiento aparecieron junto a zonas que ya eran urbanas, como relleno o en los bordes. La expansión de borde fue la forma más común." |
| Suelo frente a población, 2000-2015 | ✅ | "Entre 2000 y 2015 el suelo urbano creció algo más lento que la población (ODS 11.3.1 entre 0,88 y 0,95 con dos fuentes satelitales y con censos)." |
| Barquisimeto, Barcelona-Puerto La Cruz, Margarita | ✅ | "En Barquisimeto, Barcelona-Puerto La Cruz y Margarita la población creció más rápido que la superficie urbanizada en las 36 combinaciones de fuentes y métodos que probamos." |
| Maracaibo | ⏳ | Pendiente del censo municipal de Zulia. Las otras 27 combinaciones, incluida la estimación municipal del INE, dan 0,28-0,68 |
| Los 90 crecieron más rápido que 2000-2015 | 🟡 | "En los 90 las ciudades crecieron más rápido que después de 2000, igual que la población." Sin cifra para los 90 |
| Largo plazo, 1990-2011 | 🟡 | "Con WSF y los censos, entre 1990 y 2011 suelo urbano y población crecieron a un ritmo parecido." |
| La mitad del crecimiento en <1% del territorio | 🟡 | Solo con su línea base, nunca como titular |
| Superficie de asentamiento | ✅ | "Unos 2.500 km² en 1985 y unos 4.400 km² en 2015 (WSF-Evolution)." |
| Repartos exactos de relleno y salto | ❌ | — |
| Caracas (se expandió o se densificó) | ❌ | — |
| Años concretos antes de 2000 | ❌ | — |
| 2015-2020 | ❌ | — |

## Pendientes

- **Censo municipal de Zulia, Aragua y Bolívar.** Sus PDF del INE (`ESTADO-ZULIA.pdf`, `ESTADO-ARAGUA-1.pdf`, `ESTADO-BOLIVAR.pdf`) no se pudieron descargar el 22 de octubre de 2026: el servidor del INE rechazaba las conexiones y la copia del Internet Archive limitaba las descargas. Sus municipios ya están en el CSV con las columnas del censo vacías: basta con llenar `censo_2001` y `censo_2011` desde el Cuadro 2.2 y volver a correr `verify_cities_census.py`. El script comprueba que los municipios de cada estado sumen el total estatal y se detiene si no cuadra. Solo Zulia puede cambiar lo publicable (Maracaibo). Si con el censo municipal Maracaibo da < 0,9 en las 36 combinaciones, se suma a las otras tres ciudades; si no, queda "no concluyente".
- ~~**Video.**~~ Resuelto el 22 de octubre: los textos del video siguen esta validación ("9 de cada 10 km² nuevos, pegados a zonas ya urbanas" y "el suelo urbano creció algo más lento que la población", ODS 0,88-0,95), y antes de 2000 avisa que los saltos de 1991 y 1996 son huecos en las imágenes (T1). Los contornos celestes siguen marcando la mitad del crecimiento 2000-2015 (T3, 🟡).
- ~~**Lámina.**~~ Resuelto el 22 de octubre: `output/como_verificamos.png` regenerada con los textos nuevos.

## Fuentes nuevas

- **Censo por municipio:** INE, *Censo Nacional de Población y Vivienda 2011, resultados por entidad federal*, Cuadro 2.2 "Distribución de la población según municipio, censos 2001-2011" (población empadronada). PDF por estado en `ine.gob.ve/wp-content/uploads/2024/09/` (la URL de cada uno está en la columna `fuente_censo` del CSV). Transcrito en [`datos/censo_municipal_2001_2011.csv`](datos/censo_municipal_2001_2011.csv). Control: la suma de los municipios coincide exactamente con el total estatal de [`verify_pop.py`](verify_pop.py). Distrito Capital y La Guaira son un solo municipio y usan el total estatal.
- **Estimación municipal del INE** (corregida por omisión, a mitad de 2001 y 2011): INE vía [citypopulation.de](https://www.citypopulation.de/en/venezuela/admin/), columnas "E 2001-06-30" y "E 2011-06-30". Se usa solo como sensibilidad.
- **Totales censales 1990, 2001 y 2011:** INE (2014), serie histórica de los censos.
- **Municipios:** geoBoundaries VEN ADM2 (CC BY 3.0 IGO), la misma fuente que ADM0 y ADM1.

## Reproducir

```bash
python -P verify_claims.py           # T1-T4 → output/p03_validacion.json
python -P verify_cities_census.py    # T5    → output/p03_validacion_ciudades.json
```

Requieren las salidas intermedias de `prepare.py`, `growth.py` y `wsf_layers.py` (ver el README).
