import { createContext, useContext } from "react";

// Todos los textos de la página. Cada idioma tiene exactamente las mismas claves.
// Las cifras no van aquí: llegan formateadas desde los componentes (ver cifras.js).
export const TEXTOS = {
  es: {
    marca: "DATOS ABIERTOS_",
    otroIdioma: { etiqueta: "EN", aria: "Read in English", ruta: "en/", hreflang: "en" },
    tema: { aClaro: "Cambiar a modo claro", aOscuro: "Cambiar a modo oscuro" },
    nav: {
      problema: "El problema",
      avances: "Avances",
      mision: "Misión",
      metodo: "Método",
      ruta: "Hoja de ruta",
      api: "Datos y API",
    },
    hero: {
      estado: "En desarrollo",
      titulo: "Datos geoespaciales abiertos donde el censo no llega",
      bajada:
        "Estamos construyendo una API open source de datos sociodemográficos y territoriales para países donde los datos censales son escasos, viejos o difíciles de conseguir. Empezamos por Venezuela.",
      ctaGithub: "Ver en GitHub",
      ctaMapa: "Explorar el mapa en GeoLibre",
      nota: "Ya está abierta la API v0: cada cifra en JSON, con su método, sus fuentes y su licencia, más las capas en GeoParquet.",
    },
    mapa: {
      aria: "Mapa de Venezuela en hexágonos coloreados según cuántas construcciones tiene cada uno. Las mayores concentraciones están en el norte del país.",
      leyenda: (km2) => `Construcciones por hexágono de ~${km2} km²`,
      vacio: "Ninguna",
      menos: "Menos",
      mas: "Más",
      tooltip: "construcciones",
      fuente: "Fuente: Overture Maps (P01) · Límites: geoBoundaries, sin Guayana Esequiba",
    },
    problema: {
      id: "problema",
      eyebrow: "// el_vacío_",
      dato: "2011",
      datoEtiqueta: "año del último censo nacional publicado",
      titulo: "Los datos oficiales de Venezuela tienen más de una década",
      parrafos: [
        "Desde el último censo el país cambió mucho, pero los datos oficiales actualizados, a escala fina y en formatos abiertos, son difíciles de conseguir. Quien necesita planificar, investigar o informar termina usando cifras de hace más de diez años. Lo mismo pasa en muchos otros países.",
        "Las imágenes satelitales y los mapas colaborativos, en cambio, se actualizan todo el tiempo. Con ellos se puede medir, de forma abierta y verificable, buena parte de lo que el censo ya no alcanza a contar.",
      ],
    },
    avances: {
      id: "avances",
      eyebrow: "// avances_",
      titulo: "Lo que ya medimos",
      intro: "Las primeras publicaciones de la serie, con el código y los datos para reproducirlas.",
      cifras: {
        construcciones: "construcciones en Venezuela, contadas con los contornos de techos de Overture Maps",
        mitad: "del territorio concentra la mitad de esas construcciones, en celdas de ~5 km²",
        vacio: "del territorio no tiene ni una construcción a esa misma escala",
        gini: "de Gini espacial: lo construido está muy concentrado (1 sería todo en un solo punto)",
        pegado: "del asentamiento nuevo de 2000-2015 apareció pegado a zonas ya urbanas, como relleno o en los bordes (18 variantes del método)",
        ods: "ODS 11.3.1 en 2000-2015: el suelo urbano creció algo más lento que la población (satélites y censos)",
      },
      nota: "Las cifras de P01 y P02 son techos, no personas ni viviendas: una casa cuenta como una y una torre también. Las de P03 son superficie de asentamiento. Casi todos los contornos de techo son de imágenes anteriores al sismo del 24 de junio de 2026: no reflejan los daños.",
      publicaciones: [
        {
          codigo: "P01",
          carpeta: "p01-edificios-overture",
          titulo: "¿Cuántas construcciones tiene Venezuela?",
          texto: "Conteo nacional y por estado con DuckDB y Overture Maps, contrastado con el censo de 2011.",
        },
        {
          codigo: "P02",
          carpeta: "p02-concentracion",
          titulo: "La Venezuela concentrada",
          texto: "Cuánto territorio ocupa lo construido, dónde están los puntos calientes y qué tan robustas son las cifras.",
          geolibre: true,
        },
        {
          codigo: "P03",
          carpeta: "p03-crecimiento",
          titulo: "Así crecieron las ciudades de Venezuela, 1985-2015",
          texto: "Treinta años de crecimiento urbano con dos productos satelitales y los censos del INE, incluido lo que no resistió las pruebas.",
          geolibre: true,
        },
      ],
      codigo: "Código y datos",
      geolibre: "Abrir en GeoLibre",
    },
    mision: {
      id: "mision",
      eyebrow: "// propósito_",
      titulo: "Misión y visión",
      mision: {
        titulo: "Misión",
        texto:
          "Producir y publicar datos geoespaciales sociodemográficos abiertos, reproducibles y verificables para países donde los datos censales son escasos, viejos o difíciles de obtener, empezando por Venezuela.",
      },
      vision: {
        titulo: "Visión",
        texto:
          "Que cualquier persona, sea investigadora, periodista, ONG, gobierno local o empresa, pueda consultar en una API abierta cómo se distribuyen la población y lo construido en un país, con métodos y fuentes a la vista.",
      },
    },
    metodo: {
      id: "metodo",
      eyebrow: "// método_",
      titulo: "Abierto, reproducible y verificable",
      puntos: [
        {
          titulo: "Abierto de punta a punta",
          texto: "Fuentes abiertas (Overture Maps, OpenStreetMap, GHSL, WSF-Evolution, censos del INE, geoBoundaries), herramientas open source y código con licencia MIT.",
        },
        {
          titulo: "Reproducible",
          texto: "Cada cifra sale de un script del repositorio. Cualquiera puede correrlo y llegar al mismo resultado.",
        },
        {
          titulo: "Verificable",
          texto: "Cada cifra se contrasta con una segunda fuente y con los censos, se prueba ante la escala y el método, y se publica con sus limitaciones. Lo que no resiste se descarta, y lo contamos.",
        },
      ],
      stack: "Herramientas y fuentes",
    },
    ruta: {
      id: "hoja-de-ruta",
      eyebrow: "// hoja_de_ruta_",
      titulo: "En qué vamos",
      estados: { hecho: "Listo", proximo: "Próximo", despues: "Después" },
      items: [
        { estado: "hecho", titulo: "P01 · Conteo de construcciones", texto: "Todas las construcciones del país, por estado y en hexágonos H3." },
        { estado: "hecho", titulo: "P02 · Concentración territorial", texto: "Gini espacial, puntos calientes y aglomeraciones urbanas." },
        { estado: "hecho", titulo: "P03 · Crecimiento urbano 1985-2015", texto: "Cómo y dónde crecieron las ciudades, con dos productos satelitales y los censos." },
        { estado: "hecho", titulo: "API abierta v0", texto: "Indicadores, estados, ciudades, series y capas en JSON y GeoParquet, cada uno con su licencia." },
        { estado: "proximo", titulo: "API de consultas", texto: "Preguntar por un punto, un polígono o un hexágono y recibir las métricas de esa zona." },
        {
          estado: "despues",
          titulo: "Indicadores sociodemográficos",
          texto: "Pasar de techos a estimaciones de población y vivienda, validadas con fuentes oficiales.",
        },
        { estado: "despues", titulo: "Más países", texto: "Llevar el mismo método a otros países sin datos censales a mano." },
      ],
    },
    api: {
      id: "datos",
      eyebrow: "// api_v0_",
      titulo: "Usa los datos",
      intro:
        "Cada cifra que publicamos está en una API abierta: archivos JSON estáticos, sin registro ni clave, con su método, sus fuentes, las pruebas que pasó y su licencia. Las capas completas están en GeoParquet, listas para DuckDB, QGIS o GeoLibre.",
      recursos: [
        ["indicadores.json", "Las métricas verificadas de cada publicación, como valor o como rango"],
        ["estados.json", "Los 25 estados: construcciones, asentamiento 1985-2015 y población de censos y modelo"],
        ["ciudades.json", "Lecturas por ciudad del ODS 11.3.1, con su estado de verificación"],
        ["series/asentamiento.json", "Superficie de asentamiento de Venezuela, año a año, 1985-2015"],
        ["capas.json", "Capas GeoParquet descargables, con sus campos, filas y licencia"],
        ["descartes.json", "Lo que no resistió las verificaciones, y por qué"],
      ],
      ejemplos: "Ejemplos",
      ctaIndice: "Ver el catálogo",
      ctaOpenapi: "Especificación OpenAPI",
      licencia:
        "Si usas los datos, cita la fuente y respeta la licencia de cada recurso: ODbL para lo derivado de Overture Maps (P01, P02), CC BY 4.0 para P03.",
    },
    descartes: {
      id: "descartes",
      eyebrow: "// lo_que_descartamos_",
      titulo: "Lo que descartamos",
      intro:
        "Antes de publicar intentamos tumbar cada cifra. Estas no resistieron, así que no las publicamos como hallazgos, y explicamos por qué.",
      verDocumento: "Ver la prueba",
    },
    openSource: {
      id: "open-source",
      eyebrow: "// open_source_",
      titulo: "Construyámoslo en abierto",
      texto:
        "El código es MIT. Los datos derivados de Overture Maps (P01 y P02) heredan su licencia ODbL, y los de P03 (GHSL, WSF-Evolution e INE) se publican con CC BY 4.0. Si usas los datos, encuentras un error o quieres proponer un análisis, abre un issue en GitHub.",
      ctaRepo: "Ver el repositorio",
      ctaIssue: "Abrir un issue",
    },
    footer: {
      proyecto: "Un proyecto de",
      datos: "Datos: © OpenStreetMap contributors, Overture Maps Foundation (ODbL) · GHSL © Comisión Europea, JRC y WSF-Evolution © DLR (CC BY 4.0) · INE · geoBoundaries (CC BY 3.0 IGO)",
      fuentes: "Fuentes y licencias",
      codigo: "Código bajo licencia MIT",
    },
  },

  en: {
    marca: "OPEN DATA_",
    otroIdioma: { etiqueta: "ES", aria: "Leer en español", ruta: "", hreflang: "es" },
    tema: { aClaro: "Switch to light mode", aOscuro: "Switch to dark mode" },
    nav: {
      problema: "The gap",
      avances: "Progress",
      mision: "Mission",
      metodo: "Method",
      ruta: "Roadmap",
      api: "Data & API",
    },
    hero: {
      estado: "In development",
      titulo: "Open geospatial data where the census doesn't reach",
      bajada:
        "We're building an open-source API of socio-demographic and territorial data for countries where census data is scarce, outdated or hard to get. We're starting with Venezuela.",
      ctaGithub: "View on GitHub",
      ctaMapa: "Explore the map in GeoLibre",
      nota: "API v0 is now open: every figure as JSON, with its method, sources and license, plus the layers in GeoParquet.",
    },
    mapa: {
      aria: "Map of Venezuela in hexagons colored by how many structures each one contains. The largest concentrations are in the north of the country.",
      leyenda: (km2) => `Structures per ~${km2} km² hexagon`,
      vacio: "None",
      menos: "Fewer",
      mas: "More",
      tooltip: "structures",
      fuente: "Source: Overture Maps (P01) · Boundaries: geoBoundaries, excluding Guayana Esequiba",
    },
    problema: {
      id: "the-gap",
      eyebrow: "// the_gap_",
      dato: "2011",
      datoEtiqueta: "year of the latest published national census",
      titulo: "Venezuela's official data is more than a decade old",
      parrafos: [
        "The country has changed a lot since the last census, but up-to-date official data, at fine scale and in open formats, is hard to come by. Anyone who needs to plan, research or report ends up working with figures more than ten years old. The same happens in many other countries.",
        "Satellite imagery and collaborative maps, on the other hand, are updated all the time. With them we can measure, openly and verifiably, much of what the census no longer captures.",
      ],
    },
    avances: {
      id: "progress",
      eyebrow: "// progress_",
      titulo: "What we've measured so far",
      intro: "The first posts in the series, with the code and data to reproduce them.",
      cifras: {
        construcciones: "structures in Venezuela, counted from Overture Maps rooftop outlines",
        mitad: "of the land holds half of those structures, on ~5 km² cells",
        vacio: "of the land has not a single structure at that same scale",
        gini: "spatial Gini: the built environment is highly concentrated (1 would be everything in one spot)",
        pegado: "of new settlement in 2000-2015 appeared right next to existing urban areas, as infill or at the edges (18 method variants)",
        ods: "SDG 11.3.1 in 2000-2015: urban land grew slightly slower than the population (satellites and censuses)",
      },
      nota: "P01 and P02 figures are rooftops, not people or homes: a house counts as one, and so does a tower. P03 figures are settlement area. Almost all rooftop footprints come from imagery predating the 24 June 2026 earthquake: they do not reflect the damage.",
      publicaciones: [
        {
          codigo: "P01",
          carpeta: "p01-edificios-overture",
          titulo: "How many structures does Venezuela have?",
          texto: "A national and state-level count with DuckDB and Overture Maps, checked against the 2011 census.",
        },
        {
          codigo: "P02",
          carpeta: "p02-concentracion",
          titulo: "Concentrated Venezuela",
          texto: "How much land the built environment takes up, where the hot spots are, and how robust the figures are.",
          geolibre: true,
        },
        {
          codigo: "P03",
          carpeta: "p03-crecimiento",
          titulo: "How Venezuela's cities grew, 1985-2015",
          texto: "Thirty years of urban growth with two satellite products and the national censuses, including what didn't survive our tests.",
          geolibre: true,
        },
      ],
      codigo: "Code and data",
      geolibre: "Open in GeoLibre",
    },
    mision: {
      id: "mission",
      eyebrow: "// purpose_",
      titulo: "Mission and vision",
      mision: {
        titulo: "Mission",
        texto:
          "To produce and publish open, reproducible and verifiable geospatial socio-demographic data for countries where census data is scarce, outdated or hard to access, starting with Venezuela.",
      },
      vision: {
        titulo: "Vision",
        texto:
          "Anyone, whether a researcher, journalist, NGO, local government or business, can query through one open API how a country's population and built environment are distributed, with methods and sources in plain sight.",
      },
    },
    metodo: {
      id: "method",
      eyebrow: "// method_",
      titulo: "Open, reproducible and verifiable",
      puntos: [
        {
          titulo: "Open end to end",
          texto: "Open sources (Overture Maps, OpenStreetMap, GHSL, WSF-Evolution, national censuses, geoBoundaries), open-source tools and MIT-licensed code.",
        },
        {
          titulo: "Reproducible",
          texto: "Every figure comes from a script in the repository. Anyone can run it and get the same result.",
        },
        {
          titulo: "Verifiable",
          texto: "Every figure is checked against a second source and the censuses, tested against scale and method, and published with its limitations. What doesn't hold is discarded, and we say so.",
        },
      ],
      stack: "Tools and sources",
    },
    ruta: {
      id: "roadmap",
      eyebrow: "// roadmap_",
      titulo: "Where we are",
      estados: { hecho: "Done", proximo: "Next", despues: "Later" },
      items: [
        { estado: "hecho", titulo: "P01 · Structure count", texto: "Every structure in the country, by state and on H3 hexagons." },
        { estado: "hecho", titulo: "P02 · Territorial concentration", texto: "Spatial Gini, hot spots and urban agglomerations." },
        { estado: "hecho", titulo: "P03 · Urban growth 1985-2015", texto: "How and where cities grew, with two satellite products and the censuses." },
        { estado: "hecho", titulo: "Open API v0", texto: "Indicators, states, cities, series and layers as JSON and GeoParquet, each with its license." },
        { estado: "proximo", titulo: "Query API", texto: "Ask about a point, a polygon or a hexagon and get the metrics for that area." },
        {
          estado: "despues",
          titulo: "Socio-demographic indicators",
          texto: "Going from rooftops to population and housing estimates, validated against official sources.",
        },
        { estado: "despues", titulo: "More countries", texto: "Bringing the same method to other countries where census data is hard to get." },
      ],
    },
    api: {
      id: "data",
      eyebrow: "// api_v0_",
      titulo: "Use the data",
      intro:
        "Every figure we publish is in an open API: static JSON files, no sign-up or key, with its method, sources, the tests it passed and its license. The full layers are in GeoParquet, ready for DuckDB, QGIS or GeoLibre.",
      recursos: [
        ["indicadores.json", "The verified metrics from each post, as a value or a range"],
        ["estados.json", "The 25 states: structures, 1985-2015 settlement and census and modelled population"],
        ["ciudades.json", "SDG 11.3.1 readings by city, with their verification status"],
        ["series/asentamiento.json", "Venezuela's settlement area, year by year, 1985-2015"],
        ["capas.json", "Downloadable GeoParquet layers, with their fields, rows and license"],
        ["descartes.json", "What didn't survive verification, and why"],
      ],
      ejemplos: "Examples",
      ctaIndice: "Browse the catalog",
      ctaOpenapi: "OpenAPI specification",
      licencia:
        "If you use the data, cite the source and respect each resource's license: ODbL for data derived from Overture Maps (P01, P02), CC BY 4.0 for P03.",
    },
    descartes: {
      id: "discarded",
      eyebrow: "// what_we_discarded_",
      titulo: "What we discarded",
      intro: "Before publishing, we try to break every figure. These didn't hold, so we don't publish them as findings, and we explain why.",
      verDocumento: "See the test",
    },
    openSource: {
      id: "open-source",
      eyebrow: "// open_source_",
      titulo: "Let's build it in the open",
      texto:
        "The code is MIT-licensed. Data derived from Overture Maps (P01 and P02) inherits its ODbL license, and P03 data (GHSL, WSF-Evolution and national censuses) is published under CC BY 4.0. If you use the data, find a bug or want to propose an analysis, open an issue on GitHub.",
      ctaRepo: "View the repository",
      ctaIssue: "Open an issue",
    },
    footer: {
      proyecto: "A project by",
      datos: "Data: © OpenStreetMap contributors, Overture Maps Foundation (ODbL) · GHSL © European Commission, JRC and WSF-Evolution © DLR (CC BY 4.0) · INE · geoBoundaries (CC BY 3.0 IGO)",
      fuentes: "Sources and licenses",
      codigo: "Code under the MIT license",
    },
  },
};

const LOCALE = { es: "es-VE", en: "en-US" };

const I18n = createContext(null);

export function I18nProvider({ lang, children }) {
  // num(0.5, 2) -> "0,50" en español, "0.50" en inglés
  const num = (x, decimales = 0) =>
    new Intl.NumberFormat(LOCALE[lang], {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
      useGrouping: "always",
    }).format(x);
  // Español separa el signo de porcentaje (0,50 %); inglés no (0.50%)
  const pct = (x, decimales) => num(x, decimales) + (lang === "es" ? " %" : "%");
  return <I18n.Provider value={{ lang, t: TEXTOS[lang], num, pct }}>{children}</I18n.Provider>;
}

export const useI18n = () => useContext(I18n);
