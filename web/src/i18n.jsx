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
    },
    hero: {
      estado: "En desarrollo",
      titulo: "Datos geoespaciales abiertos donde el censo no llega",
      bajada:
        "Estamos construyendo una API open source de datos sociodemográficos y territoriales para países donde los datos censales son escasos, viejos o difíciles de conseguir. Empezamos por Venezuela.",
      ctaGithub: "Ver en GitHub",
      ctaMapa: "Explorar el mapa en GeoLibre",
      nota: "La API todavía no está disponible. Mientras tanto publicamos análisis reproducibles y sus datos en GeoParquet.",
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
      },
      nota: "Son techos, no personas ni viviendas: una casa cuenta como una y una torre también.",
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
          texto: "Fuentes abiertas (Overture Maps, OpenStreetMap, geoBoundaries), herramientas open source y código con licencia MIT.",
        },
        {
          titulo: "Reproducible",
          texto: "Cada cifra sale de un script del repositorio. Cualquiera puede correrlo y llegar al mismo resultado.",
        },
        {
          titulo: "Verificable",
          texto: "Contrastamos con fuentes oficiales, probamos la robustez ante la escala y la fuente de los datos, y publicamos las limitaciones junto con los resultados.",
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
        { estado: "proximo", titulo: "API abierta v0", texto: "Acceso programático a las capas de Venezuela." },
        {
          estado: "despues",
          titulo: "Indicadores sociodemográficos",
          texto: "Pasar de techos a estimaciones de población y vivienda, validadas con fuentes oficiales.",
        },
        { estado: "despues", titulo: "Más países", texto: "Llevar el mismo método a otros países sin datos censales a mano." },
      ],
    },
    openSource: {
      id: "open-source",
      eyebrow: "// open_source_",
      titulo: "Construyámoslo en abierto",
      texto:
        "El código es MIT y los datos derivados heredan la licencia ODbL de Overture Maps. Si usas los datos, encuentras un error o quieres proponer un análisis, abre un issue en GitHub.",
      ctaRepo: "Ver el repositorio",
      ctaIssue: "Abrir un issue",
    },
    footer: {
      proyecto: "Un proyecto de",
      datos: "Datos: © OpenStreetMap contributors, Overture Maps Foundation (ODbL) · geoBoundaries (CC BY 3.0 IGO)",
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
    },
    hero: {
      estado: "In development",
      titulo: "Open geospatial data where the census doesn't reach",
      bajada:
        "We're building an open-source API of socio-demographic and territorial data for countries where census data is scarce, outdated or hard to get. We're starting with Venezuela.",
      ctaGithub: "View on GitHub",
      ctaMapa: "Explore the map in GeoLibre",
      nota: "The API isn't available yet. In the meantime we publish reproducible analyses and their data in GeoParquet.",
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
      },
      nota: "These are rooftops, not people or homes: a house counts as one, and so does a tower.",
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
          texto: "Open sources (Overture Maps, OpenStreetMap, geoBoundaries), open-source tools and MIT-licensed code.",
        },
        {
          titulo: "Reproducible",
          texto: "Every figure comes from a script in the repository. Anyone can run it and get the same result.",
        },
        {
          titulo: "Verifiable",
          texto: "We check against official sources, test robustness to scale and data source, and publish limitations alongside the results.",
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
        { estado: "proximo", titulo: "Open API v0", texto: "Programmatic access to the Venezuela layers." },
        {
          estado: "despues",
          titulo: "Socio-demographic indicators",
          texto: "Going from rooftops to population and housing estimates, validated against official sources.",
        },
        { estado: "despues", titulo: "More countries", texto: "Bringing the same method to other countries where census data is hard to get." },
      ],
    },
    openSource: {
      id: "open-source",
      eyebrow: "// open_source_",
      titulo: "Let's build it in the open",
      texto:
        "The code is MIT-licensed and the derived data inherits Overture Maps' ODbL license. If you use the data, find a bug or want to propose an analysis, open an issue on GitHub.",
      ctaRepo: "View the repository",
      ctaIssue: "Open an issue",
    },
    footer: {
      proyecto: "A project by",
      datos: "Data: © OpenStreetMap contributors, Overture Maps Foundation (ODbL) · geoBoundaries (CC BY 3.0 IGO)",
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
