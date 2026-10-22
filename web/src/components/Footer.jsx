import { FiGithub } from "react-icons/fi";
import { ENLACES } from "../cifras";
import { useI18n } from "../i18n";
import Logo from "./Logo";

export default function Footer() {
  const { t } = useI18n();
  const f = t.footer;
  return (
    <footer className="border-t border-line">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="flex flex-col justify-between gap-8 md:flex-row md:items-center">
          <div className="space-y-3">
            <Logo />
            <p className="text-sm text-ink-muted">
              {f.proyecto}{" "}
              <a href={ENLACES.kaimind} target="_blank" rel="noopener noreferrer" className="font-medium text-accent hover:underline">
                Kaimind
              </a>
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
            <a href={ENLACES.fuentes} target="_blank" rel="noopener noreferrer" className="text-ink-muted hover:text-ink">
              {f.fuentes}
            </a>
            <a
              href={ENLACES.repo}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-ink-muted hover:text-ink"
            >
              <FiGithub className="h-4 w-4" />
              GitHub
            </a>
          </div>
        </div>
        <div className="mt-10 space-y-1 border-t border-line pt-6 text-xs text-ink-muted">
          <p>{f.datos}</p>
          <p>
            {f.codigo} · © {new Date().getFullYear()} Kaimind
          </p>
        </div>
      </div>
    </footer>
  );
}
