"""Extracción de la primera consulta SQL, sin cargar el modelo."""
import re


def _primera_sentencia(sql):
    comilla = None
    comentario = None
    i = 0
    while i < len(sql):
        c = sql[i]
        siguiente = sql[i + 1:i + 2]
        if comentario == "linea":
            if c in "\r\n":
                comentario = None
        elif comentario == "bloque":
            if c == "*" and siguiente == "/":
                comentario = None
                i += 1
        elif comilla:
            if c == "\\" and comilla != "`":
                i += 1
            elif c == comilla:
                if siguiente == comilla:
                    i += 1
                else:
                    comilla = None
        elif c in "'\"`":
            comilla = c
        elif c == "#":
            comentario = "linea"
        elif c == "-" and siguiente == "-" and (i + 2 == len(sql) or sql[i + 2].isspace()):
            comentario = "linea"
            i += 1
        elif c == "/" and siguiente == "*":
            comentario = "bloque"
            i += 1
        elif c == ";":
            return sql[:i].strip()
        i += 1
    return sql.strip()


def extraer_sql(texto):
    bloque = re.search(r"```(?:sql)?\s*(.*?)```", texto, re.S | re.I)
    if bloque:
        texto = bloque.group(1)
    # Evitar tomar un "with" dentro de una explicación como inicio de consulta.
    inicio = re.search(r"^\s*(WITH|SELECT)\b", texto, re.I | re.M) or re.search(r"\bSELECT\b", texto, re.I)
    if not inicio:
        return "SELECT 1"
    return _primera_sentencia(texto[inicio.start():]) or "SELECT 1"
