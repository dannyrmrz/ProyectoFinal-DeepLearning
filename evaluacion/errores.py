"""Clasifica cada fallo en las categorías del enunciado comparando la consulta predicha con la de referencia.

Si la consulta no corre, manda el código de error de MySQL. Si corre pero el resultado difiere,
se compara la estructura de ambas consultas en este orden: JOIN, agregación, filtro.
Es una heurística; en el notebook 03 se revisan a mano los casos dudosos.
"""
import re

CATEGORIAS = ["sintaxis", "columna o tabla inexistente", "JOIN", "agregación", "filtro", "resultado distinto"]

POR_CODIGO = {1064: "sintaxis", 1054: "columna o tabla inexistente", 1146: "columna o tabla inexistente",
              1052: "JOIN", 1055: "agregación", 1140: "agregación", 1111: "agregación"}

AGREGADAS = r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\("


def _sin_literales(sql):
    return re.sub(r"'[^']*'", "''", sql)


def _tablas(sql):
    return {t.lower().strip("`") for t in re.findall(r"\b(?:FROM|JOIN)\s+(`?\w+`?)", sql, re.I)} - {"select"}


def _agregacion(sql):
    s = sql.upper()
    return (sorted(re.findall(AGREGADAS, s)), "GROUP BY" in s, "HAVING" in s)


def _filtro(sql):
    """Condiciones del WHERE (y literales) normalizadas, sin alias de tabla."""
    m = re.search(r"\bWHERE\b(.*?)(\bGROUP BY\b|\bORDER BY\b|\bHAVING\b|\bLIMIT\b|\)|$)", sql, re.I | re.S)
    if not m:
        return ""
    condicion = re.sub(r"\b\w+\.", "", m.group(1).lower())
    return re.sub(r"\s+", " ", condicion).strip()


def categoria(error, sql_pred, sql_ref):
    if error:
        codigo = error.split(":")[0]
        return POR_CODIGO.get(int(codigo) if codigo.isdigit() else None, "sintaxis")
    if _tablas(_sin_literales(sql_pred)) != _tablas(_sin_literales(sql_ref)):
        return "JOIN"
    if _agregacion(_sin_literales(sql_pred)) != _agregacion(_sin_literales(sql_ref)):
        return "agregación"
    if _filtro(sql_pred) != _filtro(sql_ref):
        return "filtro"
    return "resultado distinto"
