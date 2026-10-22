import { FiGithub, FiMessageSquare } from "react-icons/fi";
import { ENLACES } from "../cifras";
import { useI18n } from "../i18n";
import Button from "./Button";

export default function OpenSource() {
  const { t } = useI18n();
  const s = t.openSource;
  return (
    <section id={s.id} className="scroll-mt-16 border-t border-line py-16 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="relative overflow-hidden rounded-3xl border border-line bg-card p-8 sm:p-14">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(circle at 100% 0%, var(--glow-a), transparent 50%), radial-gradient(circle at 0% 100%, var(--glow-b), transparent 50%)",
            }}
          />
          <div className="relative max-w-2xl">
            <p className="k-eyebrow">{s.eyebrow}</p>
            <h2 className="mt-3 font-display text-3xl leading-tight sm:text-4xl">{s.titulo}</h2>
            <p className="mt-5 text-lg leading-relaxed text-ink-muted">{s.texto}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button href={ENLACES.repo} icono={FiGithub}>
                {s.ctaRepo}
              </Button>
              <Button href={ENLACES.issues} variante="secundario" icono={FiMessageSquare}>
                {s.ctaIssue}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
