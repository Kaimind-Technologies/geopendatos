import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "path";

// En GitHub Actions, BASE_PATH sale de actions/configure-pages:
// "" con dominio propio, "/venezuela-datos-abiertos" mientras se sirva en github.io.
const base = `${process.env.BASE_PATH ?? ""}/`;

export default defineConfig({
  base,
  plugins: [react(), tailwindcss()],
  // Las cifras se leen de los JSON de cada publicación, fuera de web/
  server: { fs: { allow: [".."] } },
  build: {
    rolldownOptions: {
      input: {
        // Español en la raíz, inglés en /en/: cada idioma con su propio HTML
        es: resolve(import.meta.dirname, "index.html"),
        en: resolve(import.meta.dirname, "en/index.html"),
      },
    },
  },
});
