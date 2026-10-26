// Cifras de la portada, leídas de las salidas de cada publicación para que la
// página nunca se desfase de los análisis. Si se re-corre P01 o P02, se actualizan solas.
import { total_edificios } from "../../p01-edificios-overture/output/p01_cifras.json";
import { gini_espacial_territorio } from "../../p02-concentracion/output/p02_stats.json";
import robustez from "../../p02-concentracion/output/p02_robustez.json";

// Titular de P02: celdas H3 de resolución 7 (~5 km²), sin filtrar techos pequeños.
// Ojo: la curva de p02_cifras.json da 0,51 % porque divide entre el área oficial.
const r7 = robustez.find((r) => r.resolucion_h3 === 7 && r.filtro_area_min_m2 === 0);

// P03 y lo descartado salen de la API v0 (api/build_api.py), que a su vez lee los JSON de cada publicación
import indicadores from "../public/api/v0/indicadores.json";
import descartes from "../public/api/v0/descartes.json";

const IND = Object.fromEntries(indicadores.map((i) => [i.id, i]));

export const CIFRAS = {
  construcciones: total_edificios,
  mitadPctTerritorio: r7.A_mitad_pct_territorio,
  vacioPctTerritorio: r7.B_vacio_pct_territorio,
  gini: gini_espacial_territorio,
  // Rangos: dependen del método (18 variantes de la LEI) y de la fuente de población (6 combinaciones)
  pegadoUrbanoPct: IND.crecimiento_pegado_a_lo_urbano_pct.rango,
  ods2000_2015: IND.ods_11_3_1_nacional_2000_2015.rango,
};

export const DESCARTES = descartes;
export const N_INDICADORES = indicadores.length;

export const ENLACES = {
  repo: "https://github.com/Kaimind-Technologies/venezuela-datos-abiertos",
  issues: "https://github.com/Kaimind-Technologies/venezuela-datos-abiertos/issues/new",
  fuentes: "https://github.com/Kaimind-Technologies/venezuela-datos-abiertos/blob/main/DATA_SOURCES.md",
  carpeta: (nombre) => `https://github.com/Kaimind-Technologies/venezuela-datos-abiertos/tree/main/${nombre}`,
  geolibreP02:
    "https://web.geolibre.app/?welcome=0&theme=dark&url=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp02-concentracion%2Fgeolibre%2Fp02_concentracion.geolibre.json",
  geolibreP03:
    "https://web.geolibre.app/?welcome=0&theme=dark&url=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp03-crecimiento%2Fgeolibre%2Fp03_explorar.geolibre.json",
  // Base pública de la API v0 (VITE_SITE_URL la fija el workflow con la URL real del sitio)
  api: `${import.meta.env.VITE_SITE_URL}/api/v0`,
  apiRel: `${import.meta.env.BASE_URL}api/v0`,
  raw: "https://raw.githubusercontent.com/Kaimind-Technologies/venezuela-datos-abiertos/main",
  kaimind: "https://kaimindconsulting.com",
};
