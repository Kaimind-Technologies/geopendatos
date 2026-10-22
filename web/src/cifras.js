// Cifras de la portada, leídas de las salidas de cada publicación para que la
// página nunca se desfase de los análisis. Si se re-corre P01 o P02, se actualizan solas.
import { total_edificios } from "../../p01-edificios-overture/output/p01_cifras.json";
import { gini_espacial_territorio } from "../../p02-concentracion/output/p02_stats.json";
import robustez from "../../p02-concentracion/output/p02_robustez.json";

// Titular de P02: celdas H3 de resolución 7 (~5 km²), sin filtrar techos pequeños.
// Ojo: la curva de p02_cifras.json da 0,51 % porque divide entre el área oficial.
const r7 = robustez.find((r) => r.resolucion_h3 === 7 && r.filtro_area_min_m2 === 0);

export const CIFRAS = {
  construcciones: total_edificios,
  mitadPctTerritorio: r7.A_mitad_pct_territorio,
  vacioPctTerritorio: r7.B_vacio_pct_territorio,
  gini: gini_espacial_territorio,
};

export const ENLACES = {
  repo: "https://github.com/Kaimind-Technologies/venezuela-datos-abiertos",
  issues: "https://github.com/Kaimind-Technologies/venezuela-datos-abiertos/issues/new",
  fuentes: "https://github.com/Kaimind-Technologies/venezuela-datos-abiertos/blob/main/DATA_SOURCES.md",
  carpeta: (nombre) => `https://github.com/Kaimind-Technologies/venezuela-datos-abiertos/tree/main/${nombre}`,
  geolibreP02:
    "https://web.geolibre.app/?welcome=0&theme=dark&url=https%3A%2F%2Fraw.githubusercontent.com%2FKaimind-Technologies%2Fvenezuela-datos-abiertos%2Fmain%2Fp02-concentracion%2Fgeolibre%2Fp02_concentracion.geolibre.json",
  kaimind: "https://kaimindconsulting.com",
};
