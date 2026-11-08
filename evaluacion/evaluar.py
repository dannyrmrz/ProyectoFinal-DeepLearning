"""Evalúa el servicio en producción con la validación propia del Proyecto 3.

Cada pregunta se envía a POST /api/sql, igual que lo haría un usuario. Después las predicciones
se ejecutan en MySQL 8.4 y se comparan con la referencia (EX ponderada).

    python -m evaluacion.evaluar --url http://localhost:7860 --nombre adapter
    python -m evaluacion.evaluar --nombre adapter --solo-generar     # sin MySQL
    python -m evaluacion.evaluar --nombre adapter --solo-puntuar     # puntúa un CSV ya generado
"""
import argparse
import datetime
import decimal
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"
RESULTADOS = AQUI / "resultados"
PESOS = {"facil": 1, "media": 2, "dificil": 3}
COLUMNAS_PRED = ["id", "db", "nivel", "pregunta", "sql_ref", "sql_pred", "solo_lectura",
                 "segundos", "segundos_cliente", "error_api"]


def cargar_preguntas():
    return json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8"))


def cargar_esquemas():
    """Esquemas tal como los devuelve SHOW CREATE TABLE en MySQL 8.4 (los mismos del Proyecto 3)."""
    return json.loads((DATOS / "esquemas.json").read_text(encoding="utf-8"))


# ---------- 1. Generación: llama a la API ----------

def _post(url, ruta, datos, timeout):
    req = urllib.request.Request(url.rstrip("/") + ruta, data=json.dumps(datos).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def salud(url, timeout=10):
    with urllib.request.urlopen(url.rstrip("/") + "/api/salud", timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def pedir_sql(url, esquema, pregunta, timeout=600):
    return _post(url, "/api/sql", {"esquema": esquema, "pregunta": pregunta}, timeout)


def generar(url, preguntas, esquemas, pedir=pedir_sql, mostrar=True):
    filas = []
    for i, p in enumerate(preguntas, 1):
        t0 = time.time()
        try:
            r = pedir(url, esquemas[p["db"]], p["pregunta"])
            sql, seguro, seg, error = r["sql"], r["solo_lectura"], r["segundos"], None
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
            sql, seguro, seg, error = "", None, None, repr(e)
        filas.append({"id": p["id"], "db": p["db"], "nivel": p["nivel"], "pregunta": p["pregunta"],
                      "sql_ref": p["sql"], "sql_pred": sql, "solo_lectura": seguro, "segundos": seg,
                      "segundos_cliente": round(time.time() - t0, 2), "error_api": error})
        if mostrar:
            print(f"[{i:2}/{len(preguntas)}] id {p['id']:2} {seg if seg is not None else 'ERROR':>6} s  {sql[:70]!r}",
                  flush=True)
    return pd.DataFrame(filas, columns=COLUMNAS_PRED)


# ---------- 2. Puntuación: ejecuta en MySQL ----------

def normalizar(v):
    if isinstance(v, (float, decimal.Decimal)):
        return round(float(v), 2)
    if isinstance(v, (datetime.date, datetime.datetime, datetime.timedelta)):
        return str(v)
    return v


def coinciden(pred, ref, importa_orden):
    """Cada columna de la referencia debe estar en la predicción; las columnas extra no penalizan."""
    if len(pred) != len(ref):
        return False
    if not ref:
        return True
    cols_pred, cols_ref = list(zip(*pred)), list(zip(*ref))
    clave = (lambda c: list(c)) if importa_orden else (lambda c: Counter(c))
    candidatos = [[j for j, cp in enumerate(cols_pred) if clave(cp) == clave(cr)] for cr in cols_ref]

    def buscar(mapeo):
        k = len(mapeo)
        if k == len(cols_ref):
            return True
        for j in candidatos[k]:
            if j in mapeo:
                continue
            nuevo = [*mapeo, j]
            proyectadas = [tuple(f[c] for c in nuevo) for f in pred]
            referencia = [tuple(f[:k + 1]) for f in ref]
            iguales = proyectadas == referencia if importa_orden else Counter(proyectadas) == Counter(referencia)
            if iguales and buscar(nuevo):
                return True
        return False

    return buscar([])


def preparar_mysql(preguntas, esquemas):
    """Crea las bases de validación y comprueba que las referencias corran."""
    from .mysql_util import conectar, crear_bd, esquema_de, probar

    for ddl in sorted(DATOS.glob("*.sql")):
        errores = crear_bd(ddl.stem, ddl.read_text(encoding="utf-8"))
        if errores:
            raise RuntimeError(f"{ddl.stem}: {errores[:3]}")
        if esquema_de(ddl.stem).strip() != esquemas[ddl.stem].strip():
            print(f"Aviso: SHOW CREATE TABLE de {ddl.stem} difiere de esquemas.json", file=sys.stderr)
    malas = []
    for p in preguntas:
        con = conectar(p["db"])
        error = probar(con, p["sql"])
        con.close()
        if error:
            malas.append(f"id {p['id']}: {error}")
    if malas:
        raise RuntimeError("Referencias con error:\n" + "\n".join(malas))


def puntuar(df, preguntas):
    from .errores import categoria
    from .mysql_util import conectar, motivo, probar

    def consultar(con, sql):
        with con.cursor() as cur:
            cur.execute(sql)
            return [tuple(normalizar(v) for v in f) for f in cur.fetchall()]

    orden = {p["id"]: p.get("importa_orden", False) for p in preguntas}
    filas = []
    for _, f in df.iterrows():
        sql = f["sql_pred"] if isinstance(f["sql_pred"], str) else ""
        correcto, error, cat = False, None, None
        if f["error_api"] and isinstance(f["error_api"], str):
            cat = "error de la API"
        elif not sql:
            cat = "bloqueada por el filtro"
        else:
            con = conectar(f["db"])
            error = probar(con, sql)
            if not error:
                correcto = coinciden(consultar(con, sql), consultar(con, f["sql_ref"]), orden[f["id"]])
            con.close()
            cat = "correcto" if correcto else categoria(error, sql, f["sql_ref"])
        filas.append({"correcto": correcto, "error": error, "error_mysql": motivo(error) if error else None,
                      "categoria": cat})
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(filas)], axis=1)


def ex_ponderada(df):
    pesos = df["nivel"].map(PESOS)
    return float((pesos * df["correcto"].astype(bool)).sum() / pesos.sum())


def reporte(df):
    lineas = [f"EX ponderada = {ex_ponderada(df):.3f}"]
    lineas += [f"  {n:8} {v:.3f}" for n, v in df.groupby("nivel")["correcto"].mean().items()]
    seg = df["segundos"].dropna()
    if len(seg):
        lineas.append(f"latencia p50 = {seg.quantile(0.5):.2f} s   p95 = {seg.quantile(0.95):.2f} s")
    lineas.append(df["categoria"].value_counts().to_string())
    return "\n".join(lineas)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:7860")
    parser.add_argument("--nombre", required=True, help="configuración; se guarda en resultados/<nombre>.csv")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--solo-generar", action="store_true", help="solo llamar a la API (no requiere MySQL)")
    modo.add_argument("--solo-puntuar", action="store_true", help="puntuar resultados/<nombre>_pred.csv")
    args = parser.parse_args(argv)

    preguntas, esquemas = cargar_preguntas(), cargar_esquemas()
    RESULTADOS.mkdir(exist_ok=True)
    pred_csv = RESULTADOS / f"{args.nombre}_pred.csv"

    if args.solo_puntuar:
        df = pd.read_csv(pred_csv, keep_default_na=True)
    else:
        print(f"Servicio: {salud(args.url)}")
        df = generar(args.url, preguntas, esquemas)
        df.to_csv(pred_csv, index=False, encoding="utf-8")
        print(f"Predicciones en {pred_csv}")
        if args.solo_generar:
            return

    preparar_mysql(preguntas, esquemas)
    df = puntuar(df, preguntas)
    salida = RESULTADOS / f"{args.nombre}.csv"
    df.to_csv(salida, index=False, encoding="utf-8")
    print(f"Resultados en {salida}")
    print(reporte(df))


if __name__ == "__main__":
    main()
