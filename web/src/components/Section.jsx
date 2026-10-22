// Contenedor común de las secciones: eyebrow tipo código + título + intro opcional
export default function Section({ id, eyebrow, titulo, intro, children }) {
  return (
    <section id={id} className="scroll-mt-16 border-t border-line py-16 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <p className="k-eyebrow">{eyebrow}</p>
        <h2 className="mt-3 max-w-3xl font-display text-3xl leading-tight sm:text-4xl">{titulo}</h2>
        {intro && <p className="mt-4 max-w-2xl text-ink-muted">{intro}</p>}
        <div className="mt-12">{children}</div>
      </div>
    </section>
  );
}
