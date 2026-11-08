"""Conexión a MySQL 8.4 para puntuar las predicciones (copiado y reducido de scripts/util.py del Proyecto 3)."""
import os
import re

import pymysql

MOTIVOS = {1054: "columna inexistente", 1146: "tabla inexistente", 1055: "ONLY_FULL_GROUP_BY",
           1140: "ONLY_FULL_GROUP_BY", 1064: "sintaxis", 1052: "columna ambigua", 1066: "alias duplicado",
           3065: "ORDER BY fuera de DISTINCT", 1248: "subconsulta sin alias", 1235: "LIMIT en subconsulta IN",
           1525: "valor de fecha inválido"}


def conectar(bd=None):
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=bd,
        autocommit=True,
    )


def crear_bd(nombre, script):
    """Recrea la base a partir de un script .sql; devuelve los errores encontrados."""
    sentencias = [s for s in re.split(r";\s*(?:\r?\n|$)", script) if s.strip()]
    errores = []
    con = conectar()
    with con.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS `{nombre}`")
        cur.execute(f"CREATE DATABASE `{nombre}`")
        cur.execute(f"USE `{nombre}`")
        for s in sentencias:
            try:
                cur.execute(s)
            except pymysql.MySQLError as e:
                errores.append((s[:80], str(e)))
    con.close()
    return errores


def esquema_de(nombre):
    """Esquema como lo devuelve SHOW CREATE TABLE, una tabla tras otra."""
    con = conectar(nombre)
    with con.cursor() as cur:
        cur.execute("SHOW TABLES")
        tablas = [t[0] for t in cur.fetchall()]
        ddl = []
        for t in tablas:
            cur.execute(f"SHOW CREATE TABLE `{t}`")
            ddl.append(cur.fetchone()[1] + ";")
    con.close()
    return "\n\n".join(ddl)


def probar(con, sql):
    """Ejecuta la consulta; devuelve None si corre o el mensaje de error."""
    try:
        with con.cursor() as cur:
            cur.execute(sql)
            cur.fetchall()
        return None
    except pymysql.MySQLError as e:
        return f"{e.args[0]}: {e.args[1]}" if len(e.args) > 1 else str(e)


def motivo(error):
    codigo = error.split(":")[0]
    codigo = int(codigo) if codigo.isdigit() else None
    return MOTIVOS.get(codigo, f"otro ({codigo})")
