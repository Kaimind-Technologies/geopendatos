# Sitio web

Landing del proyecto, en español (`/`) e inglés (`/en/`), con modo claro y oscuro. React + Vite + Tailwind, publicada en GitHub Pages con [`.github/workflows/web.yml`](../.github/workflows/web.yml).

```bash
cd web
npm install
npm run dev      # http://localhost:5173 y http://localhost:5173/en/
npm run build    # genera dist/
```

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Textos de ambos idiomas | [`src/i18n.jsx`](src/i18n.jsx): mismas claves en `es` y `en` |
| `<title>`, descripción y metadatos para redes | [`index.html`](index.html) y [`en/index.html`](en/index.html) |
| Colores de cada tema | [`src/index.css`](src/index.css) |
| Cifras de la portada | [`src/cifras.js`](src/cifras.js): se leen de los JSON de `p01-*/output/` y `p02-*/output/` |
| Mapa de hexágonos | [`src/datos/hexmapa.json`](src/datos/hexmapa.json), generado por [`scripts/hexmapa.py`](scripts/hexmapa.py) |

Las cifras no se escriben a mano: si se re-corre P01 o P02, la página toma los valores nuevos en el próximo build. El mapa sí hay que regenerarlo (necesita DuckDB, ver `requirements.txt` en la raíz):

```bash
python -P web/scripts/hexmapa.py   # desde la raíz del repo
```

## Colores

El verde (`#4CAE7E`) y el turquesa (`#7FD7C3`) de marca no llegan a 4,5:1 sobre fondo claro. Por eso, en modo claro, el texto usa versiones oscurecidas (`--accent`, `--eyebrow`) y los colores de marca quedan para rellenos y botones. El botón principal es negro sobre verde (7,7:1) en ambos temas.

El mapa usa una escala de un solo tono, validada para que la luminosidad cambie de forma pareja entre clases. En modo claro, más construcciones se ven más oscuras; en modo oscuro, más brillantes.

## Publicación

El workflow construye con la URL que da `actions/configure-pages`, así que funciona igual en `kaimind-technologies.github.io/venezuela-datos-abiertos` y en un dominio propio. Para usar un subdominio de Kaimind:

1. En el DNS de `kaimindconsulting.com`: registro `CNAME` del subdominio → `kaimind-technologies.github.io`.
2. En la org Kaimind-Technologies: Settings → Pages → verificar el dominio, para que nadie más pueda tomar el subdominio.
3. En este repo: Settings → Pages → Custom domain, y activar *Enforce HTTPS*.

La fuente display de marca (Caffie Lofie) se carga desde kaimindconsulting.com y no se copia a este repo, porque no está confirmado que su licencia permita redistribuirla.
