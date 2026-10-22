import { FiCompass, FiTarget } from "react-icons/fi";
import { useI18n } from "../i18n";
import Section from "./Section";

export default function Mission() {
  const { t } = useI18n();
  const s = t.mision;
  const bloques = [
    [FiTarget, s.mision],
    [FiCompass, s.vision],
  ];
  return (
    <Section id={s.id} eyebrow={s.eyebrow} titulo={s.titulo}>
      <div className="grid gap-4 md:grid-cols-2">
        {bloques.map(([Icono, b]) => (
          <div key={b.titulo} className="rounded-2xl border border-line bg-card p-6 sm:p-10">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-kgreen/15 text-accent">
              <Icono className="h-5 w-5" />
            </span>
            <h3 className="mt-6 font-display text-2xl text-ink">{b.titulo}</h3>
            <p className="mt-4 text-lg leading-relaxed text-ink-muted">{b.texto}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
