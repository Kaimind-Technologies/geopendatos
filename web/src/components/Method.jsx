import { FiCheckCircle, FiRefreshCw, FiUnlock } from "react-icons/fi";
import { useI18n } from "../i18n";
import Section from "./Section";

const ICONOS = [FiUnlock, FiRefreshCw, FiCheckCircle];
const STACK = ["DuckDB", "GeoParquet", "H3", "Overture Maps", "OpenStreetMap", "GHSL (JRC)", "WSF-Evolution (DLR)", "INE", "geoBoundaries", "GeoLibre"];

export default function Method() {
  const { t } = useI18n();
  const s = t.metodo;
  return (
    <Section id={s.id} eyebrow={s.eyebrow} titulo={s.titulo}>
      <div className="grid gap-10 md:grid-cols-3">
        {s.puntos.map((p, i) => {
          const Icono = ICONOS[i];
          return (
            <div key={p.titulo}>
              <Icono className="h-6 w-6 text-accent" aria-hidden="true" />
              <h3 className="mt-4 text-lg font-semibold text-ink">{p.titulo}</h3>
              <p className="mt-2 leading-relaxed text-ink-muted">{p.texto}</p>
            </div>
          );
        })}
      </div>

      <p className="k-eyebrow mt-14">{s.stack}</p>
      <ul className="mt-4 flex flex-wrap gap-2">
        {STACK.map((h) => (
          <li key={h} className="rounded-full border border-line bg-card px-3.5 py-1.5 font-code text-sm text-ink">
            {h}
          </li>
        ))}
      </ul>
    </Section>
  );
}
