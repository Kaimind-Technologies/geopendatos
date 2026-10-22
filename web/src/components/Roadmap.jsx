import { FiArrowRight, FiCheck, FiCircle } from "react-icons/fi";
import { useI18n } from "../i18n";
import Section from "./Section";

// El estado nunca va solo por color: siempre ícono + etiqueta
const ESTADO = {
  hecho: { icono: FiCheck, color: "text-accent", punto: "bg-kgreen" },
  proximo: { icono: FiArrowRight, color: "text-eyebrow", punto: "bg-kturquoise" },
  despues: { icono: FiCircle, color: "text-ink-muted", punto: "bg-line" },
};

export default function Roadmap() {
  const { t } = useI18n();
  const s = t.ruta;
  return (
    <Section id={s.id} eyebrow={s.eyebrow} titulo={s.titulo}>
      <ol className="relative max-w-3xl space-y-8 border-l border-line pl-8">
        {s.items.map((item) => {
          const e = ESTADO[item.estado];
          const Icono = e.icono;
          return (
            <li key={item.titulo} className="relative">
              <span
                aria-hidden="true"
                className={`absolute -left-[37px] top-1.5 h-2.5 w-2.5 rounded-full ring-4 ring-page ${e.punto}`}
              />
              <span className={`inline-flex items-center gap-1.5 font-code text-xs font-semibold uppercase tracking-widest ${e.color}`}>
                <Icono className="h-3.5 w-3.5" aria-hidden="true" />
                {s.estados[item.estado]}
              </span>
              <h3 className="mt-1.5 text-lg font-semibold text-ink">{item.titulo}</h3>
              <p className="mt-1 text-ink-muted">{item.texto}</p>
            </li>
          );
        })}
      </ol>
    </Section>
  );
}
