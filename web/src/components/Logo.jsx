import isotipo from "../assets/isotipo-white.svg";
import { useI18n } from "../i18n";

// Isotipo blanco sobre Data Green, igual que en kaimindconsulting.com
export default function Logo() {
  const { t } = useI18n();
  return (
    <a href="#inicio" className="flex items-center gap-3">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[10px] bg-kgreen">
        <img src={isotipo} alt="" className="h-6 w-6" />
      </span>
      <span className="leading-none">
        <span className="block font-display text-xl tracking-wide text-ink">KAIMIND</span>
        <span className="mt-1 block font-code text-[0.6rem] tracking-[0.45em] text-eyebrow">{t.marca}</span>
      </span>
    </a>
  );
}
