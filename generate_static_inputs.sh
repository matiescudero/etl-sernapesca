#!/bin/bash

# Ruta de los archivos de entrada
PATH_ENTRADAS="/home/usach/sig-backend/entradas"

# Variables de conexión a la BD 
MAPSTORE_PG_DB_SERVER='localhost'
MAPSTORE_PG_DB_PORT='5432'
MAPSTORE_PG_DB_NAME='yoinformo_citiaps'
MAPSTORE_PG_DB_SCHEMA='entradas'
MAPSTORE_PG_DB_USER='citiaps'
export PGPASSWORD='citiaps1234'

# Generar tablas de entrada

psql -U $MAPSTORE_PG_DB_USER -h $MAPSTORE_PG_DB_SERVER -p $MAPSTORE_PG_DB_PORT -d $MAPSTORE_PG_DB_NAME <<EOF
-- Se genera el esquema de entradas
CREATE SCHEMA IF NOT EXISTS entradas;

--Se pobla el esquema con las tablas estaticas que sirven de input para el procesamiento de la información

-- Grupos de toxinas
DROP TABLE IF EXISTS entradas.grupos_toxinas;
CREATE TABLE IF NOT EXISTS entradas.grupos_toxinas(grupo varchar(20), analisis varchar(30));
COPY entradas.grupos_toxinas FROM '${PATH_ENTRADAS}/grupos_toxinas.csv' DELIMITER ';' CSV HEADER NULL 'NA';

-- Límites toxicológicos
DROP TABLE IF EXISTS entradas.limites_toxicologicos;
CREATE TABLE IF NOT EXISTS entradas.limites_toxicologicos(tipo varchar(30), nm_toxina varchar(50), grupo varchar(10), lim_cont float, lim_tox float, unidad varchar(20), detalle varchar(50));
COPY entradas.limites_toxicologicos FROM '${PATH_ENTRADAS}/limites_toxicologicos.csv' DELIMITER ';' CSV HEADER NULL 'NA';
EOF

# Generar tabla espacial de bancos naturales
shp2pgsql -s 4326  -I ${PATH_ENTRADAS}/bancos_psmb.shp ${MAPSTORE_PG_DB_SCHEMA}.bancos_psmb | psql -U $MAPSTORE_PG_DB_USER -h $MAPSTORE_PG_DB_SERVER -p $MAPSTORE_PG_DB_PORT -d $MAPSTORE_PG_DB_NAME 

