-- ¿Cuántos edificios tiene Venezuela? DuckDB + Overture Maps
INSTALL spatial; LOAD spatial;
INSTALL httpfs;  LOAD httpfs;
SET s3_region = 'us-west-2';

-- 1. Leer solo los edificios del recuadro de Venezuela (277 GB en la nube, ~5 GB transferidos)
CREATE TABLE edificios AS
SELECT id, sources[1].dataset AS fuente, bbox, geometry
FROM read_parquet('s3://overturemaps-us-west-2/release/2026-09-23.1/theme=buildings/type=building/*.parquet')
WHERE bbox.xmin <= -59.82 AND bbox.xmax >= -73.39
  AND bbox.ymin <= 15.70  AND bbox.ymax >= 0.65;

-- 2. Estados de Venezuela (geoBoundaries, sin Esequibo)
CREATE TABLE estados AS
SELECT shapeName AS estado, ST_SetCRS(geom, 'OGC:CRS84') AS geom
FROM ST_Read('data/boundaries/gb-VEN-ADM1.geojson');

-- 3. Edificios por estado (join espacial por el centro de cada edificio)
SELECT e.estado, count(*) AS edificios
FROM edificios b
JOIN estados e
  ON ST_Intersects(e.geom, ST_SetCRS(ST_Point((b.bbox.xmin + b.bbox.xmax) / 2,
                                             (b.bbox.ymin + b.bbox.ymax) / 2), 'OGC:CRS84'))
GROUP BY e.estado
ORDER BY edificios DESC;
