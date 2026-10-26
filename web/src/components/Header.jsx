import { FiGithub } from "react-icons/fi";
import { ENLACES } from "../cifras";
import { useI18n } from "../i18n";
import Logo from "./Logo";
import ThemeToggle from "./ThemeToggle";

export default function Header() {
  const { t } = useI18n();
  const nav = [
    [t.problema.id, t.nav.problema],
    [t.avances.id, t.nav.avances],
    [t.mision.id, t.nav.mision],
    [t.metodo.id, t.nav.metodo],
    [t.api.id, t.nav.api],
    [t.ruta.id, t.nav.ruta],
  ];
  const idioma = t.otroIdioma;

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-page/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />

        <nav className="hidden items-center gap-7 text-sm text-ink-muted lg:flex">
          {nav.map(([id, label]) => (
            <a key={id} href={`#${id}`} className="transition-colors hover:text-ink">
              {label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <a
            href={import.meta.env.BASE_URL + idioma.ruta}
            hrefLang={idioma.hreflang}
            lang={idioma.hreflang}
            aria-label={idioma.aria}
            title={idioma.aria}
            className="grid h-10 min-w-10 place-items-center rounded-lg border border-line px-2 font-code text-xs font-semibold tracking-widest text-ink transition-colors hover:border-accent hover:text-accent"
          >
            {idioma.etiqueta}
          </a>
          <ThemeToggle />
          <a
            href={ENLACES.repo}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub"
            title="GitHub"
            className="grid h-10 w-10 place-items-center rounded-lg border border-line text-ink transition-colors hover:border-accent hover:text-accent"
          >
            <FiGithub className="h-[18px] w-[18px]" />
          </a>
        </div>
      </div>
    </header>
  );
}
