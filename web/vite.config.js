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
      // Nombres fijos (sin hash): GitHub Pages guarda el HTML en caché varios minutos y, con
      // hashes, una página vieja pedía un JS que el despliegue nuevo ya había borrado (pantalla
      // en negro). Con nombres fijos el archivo siempre existe.
      output: {
        entryFileNames: "assets/[name].js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
});
