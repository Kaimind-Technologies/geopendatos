import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Solo el subconjunto latino: cubre español e inglés (á, ñ, ¿, ², ©)
import "@fontsource/poppins/latin-400.css";
import "@fontsource/poppins/latin-500.css";
import "@fontsource/poppins/latin-600.css";
import "@fontsource/poppins/latin-700.css";
import "@fontsource-variable/source-code-pro";
import "./index.css";
import App from "./App";

// El idioma lo fija cada HTML: index.html (es) y en/index.html (en)
const lang = document.documentElement.lang === "en" ? "en" : "es";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App lang={lang} />
  </StrictMode>,
);
