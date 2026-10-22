// Botón-enlace. "primario": negro sobre Data Green (7,7:1, sirve en ambos temas).
const ESTILOS = {
  primario: "bg-kgreen text-black hover:bg-kturquoise",
  secundario: "border border-line text-ink hover:border-accent hover:text-accent",
};

export default function Button({ href, variante = "primario", icono: Icono, children }) {
  const externo = href.startsWith("http");
  return (
    <a
      href={href}
      {...(externo && { target: "_blank", rel: "noopener noreferrer" })}
      className={`inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold transition-colors ${ESTILOS[variante]}`}
    >
      {Icono && <Icono className="h-4 w-4 shrink-0" />}
      {children}
    </a>
  );
}
