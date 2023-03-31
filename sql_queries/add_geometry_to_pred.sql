CREATE TABLE capas_estaticas.mrsat_pred AS
(SELECT pred.area, ST_Centroid(areas.geom) AS geom, TO_DATE(pred.date, 'YYYY-MM-DD') AS date, pred.x, pred.y, pred.analisis
FROM entradas.mrsat_pred as pred
LEFT JOIN capas_estaticas.areas_contingencia as areas
ON pred.area = areas.codigoarea);