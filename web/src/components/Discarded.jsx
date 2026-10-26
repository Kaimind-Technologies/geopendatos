import { FiExternalLink, FiXCircle } from "react-icons/fi";
import { DESCARTES } from "../cifras";
import { useI18n } from "../i18n";
import Section from "./Section";

// Lo que no resistió las verificaciones. Sale de la API (descartes.json): mismas cifras que los README.
export default function Discarded() {
  const { t, lang } = useI18n();
  const s = t.descartes;
  return (
    <Section id={s.id} eyebrow={s.eyebrow} titulo={s.titulo} intro={s.intro}>
      <ul className="grid gap-4 md:grid-cols-2">
        {DESCARTES.map((d) => (
          <li key={d.id} className="flex flex-col rounded-2xl border border-line bg-card p-6">
            <div className="flex items-center gap-2">
              <FiXCircle className="h-4 w-4 shrink-0 text-ink-muted" aria-hidden="true" />
              <span className="font-code text-xs font-semibold tracking-widest text-eyebrow">{d.publicacion}</span>
            </div>
            <p className="mt-3 font-semibold text-ink line-through decoration-ink-muted/60">{d.afirmacion[lang]}</p>
            <p className="mt-2 flex-1 text-sm leading-relaxed text-ink-muted">{d.por_que[lang]}</p>
            <a
              href={d.documento}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-accent hover:underline"
            >
              <FiExternalLink className="h-4 w-4" />
              {s.verDocumento}
            </a>
          </li>
        ))}
      </ul>
    </Section>
  );
}
