import { useState } from "react";
import { FiBookOpen, FiDatabase } from "react-icons/fi";
import { ENLACES, N_INDICADORES } from "../cifras";
import { useI18n } from "../i18n";
import Button from "./Button";
import Section from "./Section";

// Ejemplos con la URL pública real de la API (la fija el workflow con VITE_SITE_URL)
const EJEMPLOS = {
  curl: (api) => `curl -s ${api}/estados/zulia.json`,
  Python: (api) => `import json, urllib.request

estados = json.load(urllib.request.urlopen("${api}/estados.json"))
for e in estados[:3]:
    print(e["nombre"], e["construcciones"]["valor"])`,
  DuckDB: (api, raw) => `-- Tabla de estados directo desde la API
SELECT nombre, construcciones.valor AS construcciones
FROM read_json_auto('${api}/estados.json')
ORDER BY construcciones DESC;

-- Capa GeoParquet sin descargarla
INSTALL spatial; LOAD spatial;
SELECT anio, count(*) AS hexagonos
FROM '${raw}/p03-crecimiento/output/hex_r8_urbanizacion_wsf.parquet'
GROUP BY anio ORDER BY anio;`,
};

export default function Api() {
  const { t, num } = useI18n();
  const s = t.api;
  const [tab, setTab] = useState("curl");
  return (
    <Section id={s.id} eyebrow={s.eyebrow} titulo={s.titulo} intro={s.intro}>
      <div className="grid gap-8 lg:grid-cols-[1fr_1.15fr]">
        <ul className="space-y-3">
          {s.recursos.map(([archivo, texto]) => (
            <li key={archivo}>
              <a
                href={`${ENLACES.apiRel}/${archivo}`}
                className="group block rounded-2xl border border-line bg-card p-4 transition-colors hover:border-accent"
              >
                <span className="font-code text-sm font-semibold text-accent group-hover:underline">/{archivo}</span>
                <span className="mt-1 block text-sm text-ink-muted">
                  {texto}
                  {archivo === "indicadores.json" && ` (${num(N_INDICADORES)})`}
                </span>
              </a>
            </li>
          ))}
        </ul>

        <div className="min-w-0">
          <p className="k-eyebrow">{s.ejemplos}</p>
          <div role="tablist" className="mt-3 flex gap-2">
            {Object.keys(EJEMPLOS).map((k) => (
              <button
                key={k}
                role="tab"
                aria-selected={tab === k}
                onClick={() => setTab(k)}
                className={`rounded-lg border px-3 py-1.5 font-code text-xs font-semibold transition-colors ${
                  tab === k ? "border-accent text-accent" : "border-line text-ink-muted hover:text-ink"
                }`}
              >
                {k}
              </button>
            ))}
          </div>
          <pre className="mt-3 overflow-x-auto rounded-2xl border border-line bg-card p-5 font-code text-xs leading-relaxed text-ink sm:text-sm">
            <code>{EJEMPLOS[tab](ENLACES.api, ENLACES.raw)}</code>
          </pre>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button href={`${ENLACES.apiRel}/index.json`} icono={FiDatabase}>
              {s.ctaIndice}
            </Button>
            <Button href={`${ENLACES.apiRel}/openapi.json`} variante="secundario" icono={FiBookOpen}>
              {s.ctaOpenapi}
            </Button>
          </div>
          <p className="mt-6 border-l-2 border-kgreen pl-3 text-sm text-ink-muted">{s.licencia}</p>
        </div>
      </div>
    </Section>
  );
}
