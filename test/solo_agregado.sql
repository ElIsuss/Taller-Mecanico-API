-- Caso C-14: RN-15 (sólo agregado) y RN-19 (estado del catálogo).
-- Ejecutar con psql después de `python seed.py`:
--   psql "$DATABASE_URL" -f test/solo_agregado.sql
--
-- Los seis primeros comandos deben fallar con el disparador de sólo agregado.
-- El último debe fallar por la clave foránea a estado_orden.

-- 1) UPDATE historial_estado_orden -> ERROR: tabla de sólo agregado
UPDATE historial_estado_orden SET hasta_estado = 'TERMINADA' WHERE id = 1;

-- 2) DELETE historial_estado_orden -> ERROR: tabla de sólo agregado
DELETE FROM historial_estado_orden WHERE id = 1;

-- 3) UPDATE movimiento_stock -> ERROR: tabla de sólo agregado
UPDATE movimiento_stock SET cantidad = 99 WHERE id = 1;

-- 4) DELETE movimiento_stock -> ERROR: tabla de sólo agregado
DELETE FROM movimiento_stock WHERE id = 1;

-- 5) UPDATE historial_precio_repuesto -> ERROR: tabla de sólo agregado
UPDATE historial_precio_repuesto SET precio_nuevo = 1 WHERE id = 1;

-- 6) DELETE historial_precio_repuesto -> ERROR: tabla de sólo agregado
DELETE FROM historial_precio_repuesto WHERE id = 1;

-- 7) Estado fuera del catálogo -> ERROR: violación de clave foránea
UPDATE orden_trabajo SET estado = 'NO_EXISTE' WHERE id = 1;
