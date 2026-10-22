import { useState } from "react";
import datos from "../datos/hexmapa.json";
import { useI18n } from "../i18n";

// Venezuela en hexágonos H3 (res. 4), coloreados por quintiles de construcciones.
// Los contornos vienen ya proyectados desde web/scripts/hexmapa.py.
const HEXAGONO = "6,0 11.2,3 11.2,9 6,12 0.8,9 0.8,3";

function Muestra({ clase }) {
  return (
    <svg viewBox="0 0 12 12" className="h-3.5 w-3.5 shrink-0" aria-hidden="true">
      <polygon points={HEXAGONO} className={`hx-${clase}`} />
    </svg>
  );
}

export default function HexMap() {
  const { t, num } = useI18n();
  const [activa, setActiva] = useState(null); // { i, x, y, ancho } celda bajo el puntero

  // Un solo manejador para las 649 celdas: cada path lleva su índice en data-i
  const mover = (e) => {
    const i = e.target.dataset.i;
    if (i === undefined) return setActiva(null);
    const caja = e.currentTarget.getBoundingClientRect();
    setActiva({ i: Number(i), x: e.clientX - caja.left, y: e.clientY - caja.top, ancho: caja.width });
  };

  const celda = activa && datos.celdas[activa.i];

  return (
    <figure className="rounded-2xl border border-line bg-card p-4 sm:p-6">
      <div className="relative">
        <svg
          viewBox={datos.viewBox}
          role="img"
          aria-label={t.mapa.aria}
          className="block h-auto w-full touch-pan-y [&_path]:[vector-effect:non-scaling-stroke]"
          onPointerMove={mover}
          onPointerDown={mover}
          onPointerLeave={() => setActiva(null)}
        >
          {/* Borde del color de la tarjeta: deja una separación de ~1,5 px entre hexágonos */}
          <g stroke="var(--card)" strokeWidth={1.5} strokeLinejoin="round">
            {datos.celdas.map(([clase, , d], i) => (
              <path key={i} d={d} data-i={i} className={`hx-${clase}`} />
            ))}
          </g>
          {celda && <path d={celda[2]} fill="none" stroke="var(--ink)" strokeWidth={2} pointerEvents="none" />}
        </svg>

        {celda && (
          <div
            className="pointer-events-none absolute z-10 whitespace-nowrap rounded-lg border border-line bg-card px-3 py-1.5 text-sm shadow-lg"
            style={{
              left: Math.min(Math.max(activa.x, 80), activa.ancho - 80),
              top: activa.y,
              transform: "translate(-50%, calc(-100% - 14px))",
            }}
          >
            <span className="font-semibold text-ink">{num(celda[1])}</span>{" "}
            <span className="text-ink-muted">{t.mapa.tooltip}</span>
          </div>
        )}
      </div>

      <figcaption className="mt-4 space-y-3 text-xs text-ink-muted">
        <p className="font-medium text-ink">{t.mapa.leyenda(num(datos.km2_celda))}</p>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <span className="flex items-center gap-1.5">
            <Muestra clase={0} />
            {t.mapa.vacio}
          </span>
          <span className="flex items-center gap-1.5">
            {t.mapa.menos}
            {[1, 2, 3, 4, 5].map((c) => (
              <Muestra key={c} clase={c} />
            ))}
            {t.mapa.mas}
          </span>
        </div>
        <p>{t.mapa.fuente}</p>
      </figcaption>
    </figure>
  );
}
