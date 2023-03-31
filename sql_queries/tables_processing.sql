-----------------------------------
---- PROCESAMIENTO INFORMACIÓN ----
-----------------------------------

----------------------------------
-- /* 1. TABLAS REPORTEADOR */ ---
----------------------------------

-----------------------------------------
-- /* 1.1 Concesiones Acuicultura */ ----
-----------------------------------------

/*
CONTEXTO:
- Se genera la capa espacial de centros de cultivo a partir del servicio de mapas ofrecido 
por el IDE SUBPESCA (entradas.concesiones_acuicultura) e información proveniente del reporteador (entradas.centros_psmb)
La tabla generada sirve de base para distintos outputs generados más adelante. 

RESULTADOS ESPERADOS:
- Tabla con geometría [Polygon, SRID: 4326] de los distintos centros de cultivo de la décima región
con estado de trámite otorgado.

SUPUESTOS:
- Los nombres de campos del servicio de mapas del IDE SUBPESCA no son modificados.
- Los atributos de algunos de los campos del servicio de mapas del IDE SUBPESCA (REGION, C_TIPOPORCION, T_ESTADOTRAMITE) 
*/

DROP
	TABLE IF EXISTS capas_estaticas.total_centros;

CREATE TABLE 
	capas_estaticas.total_centros AS (
	SELECT 
	 	shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.N_CODIGOCENTRO" AS codigocentro,
		centros."Código Área" AS codigoarea,
		shp.geom AS geom,
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.TITULAR" AS titular,
		centros."Nombre Sector" AS area_psmb,
		centros."Estado" AS estado_area,
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.ESPECIES" AS especies,
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.TOPONIMIO" AS toponimio,
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.T_ESTADOTRAMITE" AS t_estadotramite,
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.F_RESOLSSP" AS f_resolucion,
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.T_GRUPOESPECIE" AS t_grupoespecie,
		CASE
	 		-- Se interpretan los valores entregados por el servicio de mapas.
			WHEN (shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 0) THEN 'NO ESPECIFICADA'
			WHEN (shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 1) THEN 'AGUA Y FONDO'
			WHEN (shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 2) THEN 'PLAYA'
			WHEN (shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 3) THEN 'ROCA'
			WHEN (shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 4) THEN 'TERRENO DE PLAYA'
			END AS c_tipoporcion,
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.SUPERFICIETOTAL" AS superficie
	FROM 
		entradas.concesiones_acuicultura AS shp
	LEFT JOIN
		-- Se une información del reporteador
		entradas.centros_psmb AS centros
	ON
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.N_CODIGOCENTRO" = centros."Código Centro"::int
	WHERE
		-- Se filtra en base a región y estado de trámite
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.REGION" = 'REGIÓN DE LOS LAGOS' AND
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.T_ESTADOTRAMITE" = 'CONCESION OTORGADA'
);

/* 
CONTEXTO:
- Se añade el estado de concesión PSMB para cada centro de cultivo.
- Si un centro se encuentra dentro de la nómina de centros entregada por el reporteador (entradas.centros_psmb), entonces el centro posee concesión.

RESULTADOS ESPERADOS:
- A la tabla de 'total_centros' se le añade una columna en donde se indica si el centro posee o no concesión PSMB, SÓLO para centros de moluscos y abalones. 

SUPUESTOS:
- Un centro cuya área PSMB se encuentre suspendida o eliminada se considera NO PSMB.
*/

ALTER TABLE 
	capas_estaticas.total_centros ADD COLUMN psmb varchar(5);

UPDATE 
	capas_estaticas.total_centros 
SET 
	psmb = CASE WHEN
	-- condiciones para que un centro sea NO PSMB
	(
		t_grupoespecie = 'MOLUSCOS' OR
		t_grupoespecie = 'ABALONES o EQUINODERMOS'
	) 
	AND (
		(codigoarea is NULL) OR 
		(estado_area = 'Suspendida') OR
		(estado_area = 'Eliminada') OR
		(codigocentro = 0)
		)
		THEN 'No'
	WHEN 
	-- condiciones para que un centro no se incluya dentro del criterio
		t_grupoespecie = 'ALGAS' OR
		t_grupoespecie = 'SALMONES'
		THEN NULL
	ELSE 'Si'
	END;

/* 
CONTEXTO:
- Tanto para resultados toxicológicos como para datos del reporteador se realizan sólo para centros de moluscos y abalones.

RESULTADOS ESPERADOS:
- Tabla 'centros_acuicultura', con los mismos campos que 'total_centros' pero filtrada únicamente para centros de moluscos y abalones.
*/

DROP 
	TABLE IF EXISTS capas_estaticas.centros_acuicultura;

CREATE TABLE capas_estaticas.centros_acuicultura AS (
	SELECT
		*
	FROM
		capas_estaticas.total_centros
	WHERE 
		t_grupoespecie = 'MOLUSCOS' OR
		t_grupoespecie = 'ABALONES o EQUINODERMOS'
);

---------------------------------------
-- /* 1.2 Centros PSMB y no PSMB*/ ----
---------------------------------------

/* 
CONTEXTO:
- A modo de representación en el mapa, interesa separar los centros PSMB y no PSMB en distintas capas

RESULTADOS ESPERADOS:
- Tabla 'centros_psmb' que incluya los centros con concesión PSMB sin la columna de estado PSMB.
- Tabla 'centros_no_psmb' que incluya los centros sin concesión PSMB sin la columna de estado PSMB.

SUPUESTOS:
- Todos los centros corresponden únicamente a concesiones de moluscos y anabalones.
*/

DROP 
	TABLE IF EXISTS capas_estaticas.centros_psmb;
DROP
	TABLE IF EXISTS capas_estaticas.centros_no_psmb;

-- Centros PSMB
CREATE TABLE capas_estaticas.centros_psmb AS (
	SELECT
		* 
	FROM 
		capas_estaticas.centros_acuicultura 
	WHERE 
		psmb = 'Si'
);

-- Centros NO PSMB
CREATE TABLE capas_estaticas.centros_no_psmb AS (
	SELECT 
		* 
	FROM 
		capas_estaticas.centros_acuicultura 
	WHERE 
		psmb = 'No'
);

-- Se eliminan las columnas de estado psmb de estas capas 
ALTER TABLE 
	capas_estaticas.centros_psmb
DROP
	COLUMN psmb;

ALTER TABLE 
	capas_estaticas.centros_no_psmb
DROP 
	COLUMN psmb;

--------------------------------------------
-- /* 1.3 Estado Áreas y Bancos PSMB */ ----
--------------------------------------------

--------------------------------------
---- 1.3.1 Estado en Áreas PSMB ------
--------------------------------------
/*
CONTEXTO:
- La delimitación de un área PSMB está denotada por la envolvente mínima de la geometría de sus centros PSMB.

RESULTADOS ESPERADOS:
- Capa espacial cuya geometría [Polygon, SRC: 4326] representa la mínima envolvente de los centros PSMB
perteneciente a una misma área PSMB, además de la columna de estado_psmb.

SUPUESTOS:
- Las áreas con estado = 'Eliminada' no se muestran.
*/

DROP 
	TABLE IF EXISTS capas_estaticas.areas_psmb;

CREATE TABLE capas_estaticas.areas_psmb AS (
	SELECT
		centros.codigoarea, 
        ST_ConvexHull(ST_Collect(centros.geom)) AS geom,
        areas."Nombre Área" AS nombrearea,
        areas."Delimitación" AS delim, 
        COUNT(DISTINCT centros.codigocentro) AS n_centros,
        centros.estado_area AS estado_psmb, 
        areas."Fecha Estado Área" AS fecha_est
	FROM 
		capas_estaticas.centros_psmb AS centros
	INNER JOIN
		-- tabla de áreas del reporteador
		entradas.areas_psmb AS areas
	ON 
		centros.codigoarea = areas."Código Área"
	WHERE 
		centros.estado_area <> 'Eliminada'
	GROUP BY 
		centros.codigoarea,
		centros.estado_area,
		areas."Nombre Área",
		areas."Delimitación",
		areas."Fecha Estado Área"
);

---------------------------------------
---- 1.3.2 Estado en Bancos PSMB ------
---------------------------------------

/*
CONTEXTO: 
- Los bancos PSMB funcionan con geometrías fijas, que no se encuentran en la capa base de centros extraida del IDE SUBPESCA.
- Cada banco funciona cómo una área PSMB a la cual se le añade el estado de área.

RESULTADOS ESPERADOS: 
- Capa de bancos naturales con su estado y fecha de acuerdo a la información de áreas del reporteador.

SUPUESTOS:
- La capa de bancos naturales tiene un código (cd_psmb) para linkearla con la información del reporteador. 
*/

DROP 
	TABLE IF EXISTS capas_estaticas.bancos_psmb;

CREATE TABLE capas_estaticas.bancos_psmb AS (
	SELECT 
		bancos.*,
		areas."Estado Área" AS estado_psmb,
		areas."Fecha Estado Área" AS fecha_est
	FROM 
		entradas.bancos_psmb AS bancos
	LEFT JOIN 
		entradas.areas_psmb AS areas
	ON 
		bancos.cd_psmb::int = areas."Código Área"
);

---------------------------------------
-- /* 1.4 Existencias Moluscos */ -----
---------------------------------------

-----------------------------------------
---- 1.4.1 Existencias en centros -------
-----------------------------------------

/*
CONTEXTO: 
- Se busca sumar la información de existencias en los distintos centros de moluscos y abalones. 
- La información de existencias de moluscos se extrae del reporteador y requiere dejar únicamente el último registro para cada centro.


RESULTADOS ESPERADOS:
- Tabla temporal de centros de cultivo con la existencia en toneladas del último mes registrado. Si la última existencia registrada
fue hace más de 3 meses, el centro se descarta.

SUPUESTOS:
- Si un centro no registra existencias en los últimos 3 meses se muestra 'Sin Existencia' en el campo 'Exist_3m'
*/

CREATE TEMP TABLE ult_fecha AS (
	SELECT 
		"codigoCentro",
    	MAX("periodoInformado") AS fecha
	FROM
		entradas.existencias_moluscos
	WHERE
		-- filtro de centros que hayan registrado en los últimos 3 meses
		"periodoInformado" > (
			SELECT 
				MAX("periodoInformado") 
			FROM 
				entradas.existencias_moluscos
		) - interval '3 months'
	GROUP BY 
		"codigoCentro"
);

/*
CONTEXTO: 
- Se debe espacializar la tabla de existencias provenientes del reporteador.
- Se une la información de existencias a la capa espacial de centros de cultivo de moluscos y anabalones. 

RESULTADOS ESPERADOS:
- Tabla 'centros_tara', que une la información de existencias a la capa 'centros_acuicultura'
*/

DROP 
	TABLE IF EXISTS capas_estaticas.centros_tara;

CREATE TABLE capas_estaticas.centros_tara AS (
	SELECT 
		centros.*,
		fechas.fecha,
		fechas.ton,
		fechas.fecha_3m
	FROM (
		SELECT 
			ult_fecha."codigoCentro" AS codigocentro,
			ult_fecha.fecha AS fecha,
			existencias."Ton" AS ton,
			existencias."Exist_3m" AS fecha_3m
		FROM 
			ult_fecha
		LEFT JOIN 
			entradas.existencias_moluscos AS existencias
		ON
			-- unión en base a cód. de centro y la última fecha registrada para c/u
			ult_fecha."codigoCentro" = existencias."codigoCentro" AND 
			ult_fecha.fecha = existencias."periodoInformado"
		) AS fechas
	RIGHT JOIN
		-- información espacial
		capas_estaticas.centros_acuicultura AS centros
	ON 
		fechas.codigocentro = centros.codigocentro
);

------------------------------------------------
------ /* 1.4.2 Existencias en Áreas */ --------
------------------------------------------------

/*
CONTEXTO:
- Se generan las mismas áreas que para el estado de áreas PSMB pero se le añade el total de existencia registrada
por sus centros de cultivo.

RESULTADOS ESPERADOS:
- Capa espacial 'areas_tara' cuya geometría [Polygon, SRC: 4326] representa la mínima envolvente de los centros PSMB
pertenecientes a una misma área PSMB, además de la columna ton_total.
*/

DROP 
	TABLE IF EXISTS capas_estaticas.areas_tara;

CREATE TABLE capas_estaticas.areas_tara AS (
	SELECT 
		centros.codigoarea,
		-- mínima envolvente
		ST_ConvexHull(ST_Collect(centros.geom)) AS geom,
		areas."Nombre Área" AS nombre,
		-- suma del tonelaje de los centros
		SUM(DISTINCT centros.ton::FLOAT) AS ton_total,
		MAX(centros.fecha) AS fecha_MAX
	FROM 
		capas_estaticas.centros_tara AS centros
	LEFT JOIN 
		entradas.areas_psmb AS areas
	ON 
		centros.codigoarea = areas."Código Área"
	WHERE 
		centros.codigoarea IS NOT NULL
	GROUP BY centros.codigoarea, areas."Nombre Área"
);

---------------------------------------
-- /* 1.5 Existencias Salmónidos */ ---
---------------------------------------

/*
CONTEXTO:
- Se realiza el mismo procedimiento que para la existencia de moluscos pero ahora existencia de salmones.

RESULTADOS ESPERADOS:
- Capa espacial de centros de cultivo de salmones junto a la última exitencia registrada por cada centro.

SUPUESTOS:
- La tabla de existencia de salmones ya incluye la última existencia registrada en cada centro.
*/

DROP 
	TABLE IF EXISTS capas_estaticas.centros_salmonidos;

CREATE TABLE capas_estaticas.centros_salmonidos AS (
  SELECT 
	shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.N_CODIGOCENTRO" AS codigocentro, 
  	shp.geom AS geom, 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.TITULAR" AS titular, 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.ESPECIES" AS especies, 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.TOPONIMIO" AS toponimio, 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.T_ESTADOTRAMITE" AS t_estadotramite, 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.F_RESOLSSP" AS f_resolucion, 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.T_GRUPOESPECIE" AS t_grupoespecie, 
    CASE WHEN (
      shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 0
    ) THEN 'NO ESPECIFICADA' WHEN (
      shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 1
    ) THEN 'AGUA Y FONDO' WHEN (
      shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 2
    ) THEN 'PLAYA' WHEN (
      shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 3
    ) THEN 'ROCA' WHEN (
      shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.C_TIPOPORCION" = 4
    ) THEN 'TERRENO DE PLAYA' END AS c_tipoporcion, 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.SUPERFICIETOTAL" AS superficie, 
    exist."Toneladas" AS ton, 
    exist."Exist_3m" AS exist_3m 
  FROM 
    entradas.concesiones_acuicultura AS shp 
    LEFT JOIN 
		entradas.existencias_salmonidos AS exist 
	ON 
		shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.N_CODIGOCENTRO" = exist."Cd_Centro" 
  WHERE 
    shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.REGION" = 'REGIÓN DE LOS LAGOS' 
    AND (
      shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.T_GRUPOESPECIE" = 'SALMONES' 
      AND shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.T_ESTADOTRAMITE" = 'CONCESION OTORGADA'
    )
);

-------------------------------------
----- /* 2. TABLAS MRSAT */ ---------
-------------------------------------

----------------------------------------------------
-- /* 2.1 Procesamiento tabla toxicológica ---------
----------------------------------------------------

/*
CONTEXTO:
- Para establecer contingencia toxicológica en cada uno de los centros de cultivo es necesario comparar los resultados
muestreados para cada estación con los límites toxicológicos preestablecidos. 

RESULTADOS ESPERADOS:
- Tabla en la cual cada registro representa los distintos análisis realizados en las distintas estaciones.
- Además, cada registro de cada centro posee el alias de la toxina muestreada y sus respectivos límites toxicológicos.

SUPUESTOS:
- Las tablas 'grupos_toxinas' y 'limites_toxicologicos' se encuentran en el esquema de entradas cómo tablas fijas.
- Únicamente sirven los resultados con Estado = 'INFORMADO'
*/

CREATE TEMP TABLE ult_pos AS(
  SELECT 
    tox_grup.*, 
    lim.tipo,
	-- Alias de la toxina muestreada
    lim.nm_toxina,
	-- Límite para que un centro presente valores sub-tóxicos
    lim.lim_cont,
	-- Límite para que un centro presente valores tóxicos
    lim.lim_tox 
  FROM 
    (
      SELECT
		-- Todas las columnas de la tabla del mrSAT.
        mrsat_60days.*, 
        grupos.grupo 
      FROM 
        entradas.mrsat_60days 
        RIGHT JOIN
			-- Tabla que incluye los nombres completos de cada toxina
			entradas.grupos_toxinas AS grupos 
		ON 
			mrsat_60days."DescripcionAnalisis" = grupos.analisis
    ) AS tox_grup 
    LEFT JOIN
		-- Tabla que incluye los limites para establecer contingencia para las distintas toxinas
		entradas.limites_toxicologicos lim 
	ON 
		lim.grupo = tox_grup.grupo 
  WHERE 
    "Estado" = 'INFORMADO'
);

/*
CONTEXTO:
- Para cada registro el valor de 'Resultado' es válido únicamente cuando "Signo" = null, en caso contrario, existen excepciones.

RESULTADOS ESPERADOS:
- La columna de resultado se actualiza de acuerdo a las condiciones señaladas en los supuestos.

SUPUESTOS:
- Si "Signo" = '<' ---> "Resultado" = 0
- Si "Signo" = 'T' AND ("grupo" != 'DTX' AND "grupo" != 'AZA') ---> "Resultado" = 0
- Si "Signo" = 'T' AND ("grupo" = 'DTX' OR "grupo" = 'AZA') ---> "Resultado" = lim_cont
- Si "Signo" IS NULL ---> "Resultado" = "Resultado"
*/

UPDATE 
  ult_pos 
SET 
  "Resultado" = CASE WHEN
  		-- Condición en caso de que se registren trazas Y DTX o AZA
		("Signo" = 'T') 
	AND (
		"grupo" = 'DTX' OR 
	  	"grupo" = 'AZA') 
	THEN lim_cont 
	WHEN 
		"Signo" = '<'
		THEN 0
	WHEN 
		"Signo" = 'T' 
	AND (
		"grupo" != 'DTX' AND 
		"grupo" != 'AZA')
		THEN 0
	ELSE "Resultado"
	END
;

/*
CONTEXTO:
- Para poder realizar el procesamiento de la información toxicológica es necesario separar la información según
su estación, grupo de toxina y análisis específico. Este se diferencia en base a sí el registro corresponde a un 
centro o un banco.

RESULTADOS ESPERADOS:
- Se le añaden las columnas 'cod_estacion', 'cod_estacion_grupo' y 'cod_estacion_analisis' a la tabla temporal ult_pos
*/

-- Se añaden las columnas vacías
ALTER TABLE 
  ult_pos 
ADD 
  COLUMN cod_estacion varchar(50), 
ADD 
  COLUMN cod_estacion_grupo varchar(70), 
ADD 
  COLUMN cod_estacion_analisis varchar(100);

-- Se concatenan los distintos id's en base a si el registro corresponde a un centro o a un banco
UPDATE 
  ult_pos 
SET 
  cod_estacion = (CASE WHEN "CodigoCentro" != 0 THEN ("CodigoCentro" || '-' || "EstacionMonitoreo") ELSE ("CodigoBancoNatural" || '-' || "EstacionMonitoreo") END), 
  cod_estacion_grupo = (CASE WHEN "CodigoCentro" != 0 THEN ("CodigoCentro" || '-' || "EstacionMonitoreo" || '-' || grupo) ELSE ("CodigoBancoNatural" || '-' || "EstacionMonitoreo" || '-' || grupo) END), 
  cod_estacion_analisis = (CASE WHEN "CodigoCentro" != 0 THEN ("CodigoCentro" || '-' || "EstacionMonitoreo" || '-' || "DescripcionAnalisis") ELSE ("CodigoBancoNatural" || '-' || "EstacionMonitoreo" || '-' || "DescripcionAnalisis") END);


------------------------------------------------------------
-- /* 2.2 Información toxicológica en áreas y bancos PSMB --
------------------------------------------------------------

/*
CONTEXTO:
- Interesa únicamente el último registro de cada toxina específica (Análisis) para cada estación.

RESULTADOS ESPERADOS: 
- Tabla que contiene el último registro de cada toxina específica en cada estación, su resultado, nombre de toxina, tipo y limites.
*/

CREATE TEMP TABLE ult_tox AS (
  SELECT 
    fech_tox.*, 
    ult_pos."Resultado" AS resultado_toxina 
  FROM 
    (
      SELECT 
        MAX("FechaExtraccion") AS fechaext, 
        cod_estacion, 
        cod_estacion_grupo, 
        cod_estacion_analisis, 
        "EstacionMonitoreo" AS estacion, 
        grupo, 
        "DescripcionAnalisis" AS analisis, 
        "CodigoArea" AS cod_area, 
        "DescripcionArea" AS n_area, 
        "CodigoCentro" cod_centro, 
        tipo, 
        nm_toxina, 
        lim_cont, 
        lim_tox 
      FROM 
        ult_pos 
      GROUP BY 
        cod_estacion, 
        cod_estacion_grupo, 
        cod_estacion_analisis, 
        "EstacionMonitoreo", 
        grupo, 
        "DescripcionAnalisis", 
        "CodigoArea", 
        "DescripcionArea", 
        "CodigoCentro", 
        tipo, 
        nm_toxina, 
        lim_cont, 
        lim_tox
    ) AS fech_tox 
    LEFT JOIN 
		ult_pos 
	ON 
		ult_pos.cod_estacion_analisis = fech_tox.cod_estacion_analisis AND 
		fech_tox.fechaext = ult_pos."FechaExtraccion"
);

/*
CONTEXTO:
- De acuerdo al grupo al que pertenece cada toxina se deben sumar las 'sub-toxinas' en cada estación.
- La suma de las toxinas por estación debe compararse con los límites toxicológicos del grupo.
- Por ejemplo, para el análisis de Azáspirácidos en una estación, se debe sumar para esa estación: AZA1, AZA2 y AZA3 y ahí comparar con los límites.

RESULTADOS ESPERADOS:
- Registros desagragados a nivel de grupo para cada estacion.
- n_accion para cada estacion-grupo en función del resultado y sus limites toxicologicos
*/


CREATE TEMP TABLE tox_est AS (
  SELECT 
    *, 
    CASE WHEN resultado > lim_tox THEN 3 WHEN (
      resultado > lim_cont 
      AND resultado < lim_tox
    ) THEN 2 ELSE 1 END AS n_accion 
  FROM 
    (
      SELECT 
        MAX(fechaext) AS fechaext, 
        cod_estacion, 
        cod_estacion_grupo, 
        estacion, 
        grupo, 
        cod_area, 
        n_area, 
        cod_centro, 
        tipo, 
        nm_toxina, 
        lim_cont, 
        lim_tox, 
        SUM(resultado_toxina) AS resultado 
      FROM 
        ult_tox 
      GROUP BY 
        cod_estacion, 
        cod_estacion_grupo, 
        estacion, 
        grupo, 
        cod_area, 
        n_area, 
        cod_centro, 
        tipo, 
        nm_toxina, 
        lim_cont, 
        lim_tox
    ) AS tox_est
);

/*
CONTEXTO:
- Para cada área PSMB interesa saber qué toxina está causando la contingencia, en caso de existir. Es por esto que
se calcula para cada toxina perteneciente a cada grupo, la diferencia entre el resultado y el límite toxicológico.

RESULTADOS ESPERADOS:
- Nueva columna a la tabla de estacion-grupo, donde se indica la diferencia señalada en el contexto.

*/

ALTER TABLE 
  tox_est 
ADD 
  COLUMN dif_tox float;

UPDATE 
  tox_est 
SET 
  dif_tox = resultado - lim_tox;


/*
CONTEXTO:
- Se establece cómo toxina causal de cada área la que presenta mayor 'dif_tox'

RESULTADOS ESPERADOS:
- Tabla que contenga todas las áreas PSMB EN CONTINGENCIA junto a su resultado, dif_tox y agente causal de la contingencia.

SUPUESTOS:
- dif_tox está construido en base a la diferencia del resultado y el MÁXIMO límite toxicológico.
- Se considera una área en contingencia aquella que alguna de sus estaciones presenta valores tóxicos o subtóxicos para algún grupo muestreado.
*/

CREATE TEMP TABLE causal_area AS (
  SELECT 
    max_tox.*,
	-- Caso cuando se presentan resultados tóxicos
    CASE WHEN (dif_tox > 0) 
		THEN nm_toxina
	-- Caso cuando se presentan resultados subtóxicos
	WHEN (dif_tox < 0 AND
		resultado > lim_cont) 
		THEN nm_toxina
	-- Caso cuando no hay contingencia
	ELSE ' ' END AS causal 
  FROM 
    (
      SELECT
		-- La selección se hace en base a áreas
        DISTINCT ON (cod_area) cod_area, 
        grupo, 
        nm_toxina, 
        cod_centro, 
        lim_cont, 
        lim_tox, 
        resultado, 
        dif_tox 
      FROM 
        tox_est 
      WHERE
		-- únicamente áreas en contingencia
        n_accion > 1
      ORDER BY 
        cod_area, 
        dif_tox DESC
    ) as max_tox
);


/*
RESULTADOS ESPERADOS:
- Tabla en la que cada registro representa un área o banco en la que se muestra el máximo resultado de cada grupo de toxinas 

*/

CREATE TEMP TABLE pivot_est AS (
  SELECT 
    cod_estacion, 
    estacion, 
    cod_area, 
    cod_centro,
	-- Se selecciona el máximo resultado
    SUM(res_vpm) AS res_vpm, 
    MAX(fecha_vpm) AS fecha_vpm, 
    SUM(res_vam) AS res_vam, 
    MAX(fecha_vam) AS fecha_vam, 
    SUM(res_ytx) AS res_ytx, 
    MAX(fecha_ytx) AS fecha_ytx, 
    SUM(res_ptx_ao) AS res_ptx_ao, 
    MAX(fecha_ptxao) AS fecha_ptxao, 
    SUM(res_dtx) AS res_dtx, 
    MAX(fecha_dtx) AS fecha_dtx, 
    SUM(res_aza) AS res_aza, 
    MAX(fecha_aza) AS fecha_aza, 
    MAX(n_accion) AS n_accion 
  FROM 
    (
	  -- Se añaden las columnas 'res_<toxina>' y 'fecha_<toxina>' para cada estación-grupo
      SELECT 
        *,
        CASE WHEN (grupo = 'VPM') THEN resultado ELSE 0 END AS res_vpm, 
        CASE WHEN (grupo = 'VPM') THEN tox_est.fechaext END AS fecha_vpm, 
        CASE WHEN (grupo = 'VAM') THEN resultado ELSE 0 END AS res_vam, 
        CASE WHEN (grupo = 'VAM') THEN tox_est.fechaext END AS fecha_vam, 
        CASE WHEN (grupo = 'YTX') THEN resultado ELSE 0 END AS res_ytx, 
        CASE WHEN (grupo = 'YTX') THEN tox_est.fechaext END AS fecha_ytx, 
        CASE WHEN (grupo = 'PTX_AO') THEN resultado ELSE 0 END AS res_ptx_ao, 
        CASE WHEN (grupo = 'PTX_AO') THEN tox_est.fechaext END AS fecha_ptxao, 
        CASE WHEN (grupo = 'DTX') THEN resultado ELSE 0 END AS res_dtx, 
        CASE WHEN (grupo = 'DTX') THEN tox_est.fechaext END AS fecha_dtx, 
        CASE WHEN (grupo = 'AZA') THEN resultado ELSE 0 END AS res_aza, 
        CASE WHEN (grupo = 'AZA') THEN tox_est.fechaext END AS fecha_aza 
      FROM
        tox_est
    ) AS pivot 
  GROUP BY 
    cod_estacion, 
    estacion, 
    cod_area, 
    cod_centro
);

-- Se genera tabla de áreas
-- Se agrupan los resultados por área, se une la causal a cada área y se espacializan 


-- Áreas contingencia

DROP 
  TABLE IF EXISTS capas_estaticas.areas_contingencia;

CREATE TABLE capas_estaticas.areas_contingencia AS (
  SELECT 
    shp.geom, 
    shp.codigoarea, 
    shp.nombrearea, 
    areas.*, 
    shp.n_centros, 
    shp.estado_psmb, 
    shp.fecha_est 
  FROM 
    (
      SELECT 
        piv.cod_area, 
        MAX(res_vpm) as res_vpm, 
        MAX(fecha_vpm)::date as fecha_vpm, 
        MAX(res_vam) as res_vam, 
        MAX(fecha_vam)::date as fecha_vam, 
        MAX(res_ytx) as res_ytx, 
        MAX(fecha_ytx)::date as fecha_ytx, 
        MAX(res_ptx_ao) as res_ptx_ao, 
        MAX(fecha_ptxao)::date as fecha_ptxao, 
        MAX(res_dtx) as res_dtx, 
        MAX(fecha_dtx)::date as fecha_dtx, 
        MAX(res_aza) as res_aza, 
        MAX(fecha_aza)::date as fecha_aza, 
        MAX(n_accion) as n_accion, 
        causal.causal 
      FROM 
        pivot_est as piv 
        LEFT JOIN causal_area as causal ON piv.cod_area = causal.cod_area 
      GROUP BY 
        piv.cod_area, 
        causal.causal
    ) as areas 
    RIGHT JOIN capas_estaticas.areas_psmb as shp ON shp.codigoarea = areas.cod_area
);

-- Bancos Contingencia

DROP 
  TABLE IF EXISTS capas_estaticas.bancos_contingencia;

CREATE TABLE capas_estaticas.bancos_contingencia AS (
  SELECT 
    shp.gid, 
    shp.geom,
    areas.*, 
    shp.descriptor,
    shp.cd_psmb, 
    shp.comuna, 
    shp.especies,
	shp.condicion,
	shp.seleccion
  FROM 
    (
      SELECT 
        piv.cod_area, 
        MAX(res_vpm) as res_vpm, 
        MAX(fecha_vpm)::date as fecha_vpm, 
        MAX(res_vam) as res_vam, 
        MAX(fecha_vam)::date as fecha_vam, 
        MAX(res_ytx) as res_ytx, 
        MAX(fecha_ytx)::date as fecha_ytx, 
        MAX(res_ptx_ao) as res_ptx_ao, 
        MAX(fecha_ptxao)::date as fecha_ptxao, 
        MAX(res_dtx) as res_dtx, 
        MAX(fecha_dtx)::date as fecha_dtx, 
        MAX(res_aza) as res_aza, 
        MAX(fecha_aza)::date as fecha_aza, 
        MAX(n_accion) as n_accion, 
        causal.causal 
      FROM 
        pivot_est as piv 
        LEFT JOIN causal_area as causal ON piv.cod_area = causal.cod_area 
      GROUP BY 
        piv.cod_area, 
        causal.causal
    ) as areas 
    RIGHT JOIN entradas.bancos_psmb as shp ON shp.cd_psmb::int = areas.cod_area
);

-- Se generan campos para determinar la acción y un msje para la capa de centros

ALTER TABLE 
  capas_estaticas.areas_contingencia 
ADD 
  COLUMN accion varchar(80), 
ADD 
  COLUMN msje varchar(100), 
ADD 
  COLUMN pre_causal varchar(100);

UPDATE 
	capas_estaticas.areas_contingencia 
SET 
	accion = CASE WHEN n_accion = 3 THEN 'valores tóxicos' WHEN n_accion = 2 THEN 'valores subtóxicos' ELSE 'sin presencia de toxinas' END, 
	msje = CASE WHEN n_accion = 3 THEN 'registra presencia de' WHEN n_accion = 2 THEN 'registra presencia de' ELSE 'se encuentra' END, 
	pre_causal = CASE WHEN n_accion = 3 THEN 'de' WHEN n_accion = 2 THEN 'de' ELSE '' END;


-- Se generan campos para determinar la acción y un msje para la capa de bancos

ALTER TABLE 
  capas_estaticas.bancos_contingencia 
ADD 
  COLUMN accion varchar(80), 
ADD 
  COLUMN msje varchar(100), 
ADD 
  COLUMN pre_causal varchar(100);

UPDATE 
	capas_estaticas.bancos_contingencia 
SET 
	accion = CASE WHEN n_accion = 3 THEN 'valores tóxicos' WHEN n_accion = 2 THEN 'valores subtóxicos' ELSE 'sin presencia de toxinas' END, 
	msje = CASE WHEN n_accion = 3 THEN 'registra presencia de' WHEN n_accion = 2 THEN 'registra presencia de' ELSE 'se encuentra' END, 
	pre_causal = CASE WHEN n_accion = 3 THEN 'de' WHEN n_accion = 2 THEN 'de' ELSE '' END;
  


-- Se eliminan las columnas que no sirven
ALTER TABLE 
  capas_estaticas.areas_contingencia 
DROP 
  COLUMN cod_area, 
DROP 
  COLUMN n_accion;
 
ALTER TABLE 
  capas_estaticas.bancos_contingencia 
DROP 
  COLUMN cod_area, 
DROP 
  COLUMN n_accion;

-- Capa que incluye el centroide del centro de la estación que registra valores toxicológicos elevados 

DROP 
  TABLE IF EXISTS capas_estaticas.centro_causal;
CREATE TABLE capas_estaticas.centro_causal AS (
  SELECT 
    causal.cod_centro, 
    ST_CENTROID(shp.geom) as geom, 
    causal.resultado, 
    causal.causal 
  FROM 
    causal_area AS causal 
    JOIN entradas.concesiones_acuicultura AS shp ON shp."REP_SUBPESCA2.ADM_UOT.PULLINQUE4_T_ACUICULTURA.N_CODIGOCENTRO" = causal.cod_centro
    WHERE causal.cod_centro != 0
);

-- Se generan índices espaciales para las capas espaciales de salida

CREATE INDEX IF NOT EXISTS geom_id ON capas_estaticas.areas_contingencia USING GIST(geom);
CREATE INDEX IF NOT EXISTS geom_id ON capas_estaticas.areas_psmb USING GIST(geom);
CREATE INDEX IF NOT EXISTS geom_id ON capas_estaticas.areas_tara USING GIST(geom);
CREATE INDEX IF NOT EXISTS geom_id ON capas_estaticas.centros_acuicultura USING GIST(geom);
CREATE INDEX IF NOT EXISTS geom_id ON capas_estaticas.centros_no_psmb USING GIST(geom);
CREATE INDEX IF NOT EXISTS geom_id ON capas_estaticas.centros_psmb USING GIST(geom);
CREATE INDEX IF NOT EXISTS geom_id ON capas_estaticas.centros_tara USING GIST(geom);


