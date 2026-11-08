# Servicio en CPU frente al Proyecto 3 en T4

Generado por `python -m evaluacion.comparar_t4`. Ambas sin autocorrección con `ejecutar`.

| Modelo | EX T4 | EX CPU | SQL idéntico | Preguntas con resultado distinto |
|---|---|---|---|---|
| base | 0.439 | 0.439 | 40/40 | ninguna |
| adapter | 0.646 | 0.585 | 37/40 | 18 (dificil, acierta T4), 28 (media, acierta T4) |

## Consultas que difieren

- **adapter, id 18** (dificil; correcto T4 = True, CPU = False)
  - T4: `WITH v AS (SELECT s.nombre, SUM(d.cantidad * d.precio_unitario) AS total FROM ventas v JOIN detalle_venta d ON d.id_venta = v.id_venta JOIN productos p ON p.id_producto = d.id_producto JOIN sucursales s ON s.id_sucursal = v.id_sucursal WHERE YEAR(v.fecha) = 2026 GROUP BY s.id_sucursal, s.nombre) SELECT nombre, total, ROW_NUMBER() OVER (ORDER BY total DESC) AS posicion FROM v`
  - CPU: `WITH v AS (SELECT s.nombre, SUM(d.cantidad * p.precio) AS total FROM ventas v JOIN sucursales s ON s.id_sucursal = v.id_sucursal JOIN detalle_venta d ON d.id_venta = v.id_venta JOIN productos p ON p.id_producto = d.id_producto WHERE YEAR(v.fecha) = 2026 GROUP BY s.id_sucursal, s.nombre) SELECT nombre, total, ROW_NUMBER() OVER (ORDER BY total DESC) AS posicion FROM v`
- **adapter, id 28** (media; correcto T4 = True, CPU = False)
  - T4: `SELECT a.artst_nm, SUM(t.prc) AS total FROM artst a JOIN evt e ON e.artst_id = a.artst_id JOIN tkt t ON t.evt_id = e.evt_id WHERE t.ord_id IN (SELECT ord_id FROM tkt_ord WHERE sts = 'PAID') GROUP BY a.artst_id, a.artst_nm`
  - CPU: `SELECT a.artst_nm, SUM(t.prc) AS total FROM artst a JOIN evt e ON e.artst_id = a.artst_id JOIN tkt_ord to ON to.ord_id = t.ord_id WHERE to.sts = 'PAID' GROUP BY a.artst_id, a.artst_nm`
- **adapter, id 35** (dificil; correcto T4 = False, CPU = False)
  - T4: `SELECT e.evt_nm, ROUND(100 * SUM(t.tot) / v.cap, 2) AS pct FROM evt e JOIN tkt_ord t ON t.ord_id = tkt.ord_id JOIN vnu v ON v.vnu_id = e.vnu_id WHERE t.prc IS NOT NULL GROUP BY e.evt_id, e.evt_nm HAVING COUNT(*) > 0`
  - CPU: `SELECT e.evt_nm, ROUND(100 * SUM(t.tkt_id IS NOT NULL) / v.cap, 2) AS pct FROM evt e JOIN tkt_ord o ON o.ord_id = t.ord_id JOIN tkt t ON t.evt_id = e.evt_id JOIN vnu v ON v.vnu_id = e.vnu_id GROUP BY e.evt_id, e.evt_nm HAVING COUNT(*) > 0`
