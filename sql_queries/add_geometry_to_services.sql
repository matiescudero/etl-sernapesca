-----------------------------------------------------------------------
-- /* Se crea el campo geom para las tablas provenientes del IDE */ --
-----------------------------------------------------------------------

/* 1. Centros de Acuicultura */

-- Se crea una nueva columna

ALTER TABLE entradas.concesiones_acuicultura
ADD COLUMN geom geometry(Geometry, 4326);

-- Se pobla la nueva columna con la geometria basada en el campo 'geometry'

UPDATE entradas.concesiones_acuicultura
SET geom = ST_PolygonFromText(geometry, 4326);

-- Se elimina la columna que contiene la geometria como texto

ALTER TABLE entradas.concesiones_acuicultura
DROP COLUMN geometry;

/* 2. Areas de Colecta */

-- Se crea una nueva columna

ALTER TABLE entradas.areas_colecta
ADD COLUMN geom geometry(Geometry, 4326);

-- Se pobla la nueva columna con la geometria basada en el campo 'geometry'

UPDATE entradas.areas_colecta
SET geom = ST_PolygonFromText(geometry, 4326);

-- Se elimina la columna que contiene la geometria como texto

ALTER TABLE entradas.areas_colecta
DROP COLUMN geometry;

/* 3. ECMPO */

-- Se crea una nueva columna

ALTER TABLE entradas.ecmpo
ADD COLUMN geom geometry(Geometry, 4326);

-- Se pobla la nueva columna con la geometria basada en el campo 'geometry'

UPDATE entradas.ecmpo
SET geom = ST_PolygonFromText(geometry, 4326);

-- Se elimina la columna que contiene la geometria como texto

ALTER TABLE entradas.ecmpo
DROP COLUMN geometry;

/* 4. AMERB */

-- Se crea una nueva columna

ALTER TABLE entradas.amerb
ADD COLUMN geom geometry(Geometry, 4326);

-- Se pobla la nueva columna con la geometria basada en el campo 'geometry'

UPDATE entradas.amerb
SET geom = ST_PolygonFromText(geometry, 4326);

-- Se elimina la columna que contiene la geometria como texto

ALTER TABLE entradas.amerb
DROP COLUMN geometry;

/* 5. Acuicultura en AMERB */

-- Se crea una nueva columna

ALTER TABLE entradas.acuiamerb
ADD COLUMN geom geometry(Geometry, 4326);

-- Se pobla la nueva columna con la geometria basada en el campo 'geometry'

UPDATE entradas.acuiamerb
SET geom = ST_PolygonFromText(geometry, 4326);

-- Se elimina la columna que contiene la geometria como texto

ALTER TABLE entradas.acuiamerb
DROP COLUMN geometry;


