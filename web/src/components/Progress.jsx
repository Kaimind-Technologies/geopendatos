import { FiExternalLink, FiFolder } from "react-icons/fi";
import { CIFRAS, ENLACES } from "../cifras";
import { useI18n } from "../i18n";
import Section from "./Section";

export default function Progress() {
  const { t, num, pct } = useI18n();
  const s = t.avances;
  const cifras = [
    [num(CIFRAS.construcciones), s.cifras.construcciones],
    [pct(CIFRAS.mitadPctTerritorio, 2), s.cifras.mitad],
    [pct(CIFRAS.vacioPctTerritorio, 1), s.cifras.vacio],
    [num(CIFRAS.gini, 2), s.cifras.gini],
  ];

  return (
    <Section id={s.id} eyebrow={s.eyebrow} titulo={s.titulo} intro={s.intro}>
      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cifras.map(([valor, etiqueta]) => (
          <div key={etiqueta} className="rounded-2xl border border-line bg-card p-6">
            <dt className="sr-only">{etiqueta}</dt>
            <dd>
              <span className="block font-display text-4xl text-ink">{valor}</span>
              <span className="mt-3 block h-0.5 w-8 rounded-full bg-kgreen" aria-hidden="true" />
              <span className="mt-3 block text-sm leading-relaxed text-ink-muted">{etiqueta}</span>
            </dd>
          </div>
        ))}
      </dl>
      <p className="mt-5 text-sm text-ink-muted">{s.nota}</p>

      <div className="mt-12 grid gap-4 md:grid-cols-2">
        {s.publicaciones.map((p) => (
          <article key={p.codigo} className="flex flex-col rounded-2xl border border-line bg-card p-6 sm:p-8">
            <span className="font-code text-xs font-semibold tracking-widest text-eyebrow">{p.codigo}</span>
            <h3 className="mt-2 text-xl font-semibold text-ink">{p.titulo}</h3>
            <p className="mt-3 flex-1 text-ink-muted">{p.texto}</p>
            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm font-medium">
              <a
                href={ENLACES.carpeta(p.carpeta)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-accent hover:underline"
              >
                <FiFolder className="h-4 w-4" />
                {s.codigo}
              </a>
              {p.geolibre && (
                <a
                  href={ENLACES.geolibreP02}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-accent hover:underline"
                >
                  <FiExternalLink className="h-4 w-4" />
                  {s.geolibre}
                </a>
              )}
            </div>
          </article>
        ))}
      </div>
    </Section>
  );
}
