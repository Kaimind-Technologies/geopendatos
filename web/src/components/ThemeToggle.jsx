import { useEffect, useState } from "react";
import { FiMoon, FiSun } from "react-icons/fi";
import { useI18n } from "../i18n";

// El tema inicial lo pone el script de <head> (preferencia guardada o la del sistema).
// Aquí solo se cambia y se guarda.
const guardado = () => {
  try {
    return localStorage.getItem("theme");
  } catch {
    return null;
  }
};

export default function ThemeToggle() {
  const { t } = useI18n();
  const [tema, setTema] = useState(() => document.documentElement.dataset.theme ?? "light");

  const aplicar = (nuevo) => {
    document.documentElement.dataset.theme = nuevo;
    setTema(nuevo);
  };

  // Mientras la persona no elija, se sigue al sistema si este cambia
  useEffect(() => {
    const mq = matchMedia("(prefers-color-scheme: dark)");
    const seguir = (e) => !guardado() && aplicar(e.matches ? "dark" : "light");
    mq.addEventListener("change", seguir);
    return () => mq.removeEventListener("change", seguir);
  }, []);

  const cambiar = () => {
    const nuevo = tema === "dark" ? "light" : "dark";
    aplicar(nuevo);
    try {
      localStorage.setItem("theme", nuevo);
    } catch {
      // sin almacenamiento (modo privado): el cambio dura lo que dure la página
    }
  };

  const etiqueta = tema === "dark" ? t.tema.aClaro : t.tema.aOscuro;
  return (
    <button
      type="button"
      onClick={cambiar}
      aria-label={etiqueta}
      title={etiqueta}
      className="grid h-10 w-10 place-items-center rounded-lg border border-line text-ink transition-colors hover:border-accent hover:text-accent"
    >
      {tema === "dark" ? <FiSun className="h-[18px] w-[18px]" /> : <FiMoon className="h-[18px] w-[18px]" />}
    </button>
  );
}
