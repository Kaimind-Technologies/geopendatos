import { FiGithub, FiMap } from "react-icons/fi";
import { ENLACES } from "../cifras";
import { useI18n } from "../i18n";
import Button from "./Button";
import HexMap from "./HexMap";

export default function Hero() {
  const { t } = useI18n();
  return (
    <section id="inicio" className="relative overflow-hidden">
      {/* Aura de los colores de marca, como en el hero del sitio principal */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(circle at 12% 0%, var(--glow-a), transparent 45%), radial-gradient(circle at 88% 70%, var(--glow-b), transparent 45%)",
        }}
      />

      <div className="relative mx-auto grid max-w-6xl gap-12 px-4 pb-20 pt-14 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:pb-28 lg:pt-20">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-line bg-card px-3 py-1 font-code text-xs tracking-wider text-ink">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-kgreen opacity-75 motion-safe:animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-kgreen" />
            </span>
            {t.hero.estado}
          </span>

          <h1 className="mt-6 font-display text-4xl leading-[1.05] sm:text-5xl lg:text-6xl">{t.hero.titulo}</h1>
          <p className="mt-6 max-w-xl text-lg text-ink-muted">{t.hero.bajada}</p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button href={ENLACES.repo} icono={FiGithub}>
              {t.hero.ctaGithub}
            </Button>
            <Button href={ENLACES.geolibreP02} variante="secundario" icono={FiMap}>
              {t.hero.ctaMapa}
            </Button>
          </div>

          <p className="mt-6 max-w-xl border-l-2 border-kgreen pl-3 text-sm text-ink-muted">{t.hero.nota}</p>
        </div>

        <HexMap />
      </div>
    </section>
  );
}
