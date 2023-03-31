----------------------------------------------------
-- /* PRE-PROCESAMIENTO INFORMACION DE ENTRADA */ --
----------------------------------------------------

----------------------------------
-- /* TABLAS REPORTEADOR */ ------
----------------------------------

-- Se modifican los valores del tonelaje para las tablas de existencias

UPDATE entradas.existencias_moluscos SET "Ton" = '0' WHERE "Ton" = '';
ALTER TABLE entradas.existencias_moluscos ALTER COLUMN "Ton" TYPE float USING "Ton"::float;

UPDATE entradas.existencias_salmonidos SET "Toneladas" = '0' WHERE "Toneladas" = '';
ALTER TABLE entradas.existencias_salmonidos ALTER COLUMN "Toneladas" TYPE float USING "Toneladas"::float;
