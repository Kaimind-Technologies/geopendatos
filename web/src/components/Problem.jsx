import { useI18n } from "../i18n";
import Section from "./Section";

export default function Problem() {
  const { t } = useI18n();
  const s = t.problema;
  return (
    <Section id={s.id} eyebrow={s.eyebrow} titulo={s.titulo}>
      <div className="grid gap-10 md:grid-cols-[minmax(0,16rem)_1fr] md:gap-16">
        <div>
          <p className="font-display text-7xl leading-none text-accent sm:text-8xl">{s.dato}</p>
          <p className="mt-3 text-sm text-ink-muted">{s.datoEtiqueta}</p>
        </div>
        <div className="max-w-2xl space-y-5 text-lg leading-relaxed text-ink-muted">
          {s.parrafos.map((p) => (
            <p key={p}>{p}</p>
          ))}
        </div>
      </div>
    </Section>
  );
}
