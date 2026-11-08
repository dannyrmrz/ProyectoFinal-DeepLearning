"""Compara pregunta por pregunta las predicciones del servicio (CPU) con las del Proyecto 3 (T4).

    python -m evaluacion.comparar_t4             # sin MySQL: compara SQL y aciertos guardados
    python -m evaluacion.comparar_t4 --puntuar   # además vuelve a puntuar las predicciones T4 en MySQL

resultados/proyecto3_t4/ guarda las predicciones T4 sin autocorrección, copiadas sin cambios de
resultados/val_base_sin_ejecutar.csv y val_todas_sin_ejecutar.csv del repositorio del Proyecto 3
(github.com/dannyrmrz/Proyecto3-TextoaSQL, commit 0eaa760). Escribe resultados/comparacion_t4.md.
"""
import argparse
import sys

import pandas as pd

from .evaluar import RESULTADOS, ex_ponderada

PARES = {"base": "base", "adapter": "adapter_b"}  # config CPU -> archivo T4


def _sql(s):
    return " ".join(str(s).split()) if isinstance(s, str) else ""


def comparar(cpu, t4):
    m = cpu.merge(t4, on="id", suffixes=("_cpu", "_t4"))
    m["sql_igual"] = [_sql(a) == _sql(b) for a, b in zip(m["sql_pred_cpu"], m["sql_pred_t4"])]
    return m


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--puntuar", action="store_true", help="re-puntuar las predicciones T4 en MySQL")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # consolas de Windows en cp1252
        sys.stdout.reconfigure(errors="backslashreplace")

    lineas = ["# Servicio en CPU frente al Proyecto 3 en T4", "",
              "Generado por `python -m evaluacion.comparar_t4`. Ambas sin autocorrección con `ejecutar`.", "",
              "| Modelo | EX T4 | EX CPU | SQL idéntico | Preguntas con resultado distinto |", "|---|---|---|---|---|"]
    detalle = []
    for config, archivo in PARES.items():
        cpu = pd.read_csv(RESULTADOS / f"{config}.csv")
        t4 = pd.read_csv(RESULTADOS / "proyecto3_t4" / f"{archivo}.csv")
        if args.puntuar:
            from .evaluar import cargar_esquemas, cargar_preguntas, preparar_mysql, puntuar

            preguntas = cargar_preguntas()
            preparar_mysql(preguntas, cargar_esquemas())
            pred = t4[["id", "db", "nivel", "pregunta", "sql_ref", "sql_pred"]].assign(
                solo_lectura=True, segundos=t4["segundos"], segundos_cliente=t4["segundos"], error_api=None)
            t4 = puntuar(pred, preguntas)
        m = comparar(cpu, t4)
        distintas = m[m["correcto_cpu"] != m["correcto_t4"]]
        lineas.append(f"| {config} | {ex_ponderada(t4):.3f} | {ex_ponderada(cpu):.3f} | "
                      f"{int(m['sql_igual'].sum())}/{len(m)} | "
                      f"{', '.join(f'{r.id} ({r.nivel_cpu}, acierta {'CPU' if r.correcto_cpu else 'T4'})' for r in distintas.itertuples()) or 'ninguna'} |")
        for r in m[~m["sql_igual"]].itertuples():
            detalle += [f"- **{config}, id {r.id}** ({r.nivel_cpu}; correcto T4 = {r.correcto_t4}, CPU = {r.correcto_cpu})",
                        f"  - T4: `{_sql(r.sql_pred_t4)}`", f"  - CPU: `{_sql(r.sql_pred_cpu)}`"]
    texto = "\n".join(lineas + ["", "## Consultas que difieren", ""] + detalle) + "\n"
    (RESULTADOS / "comparacion_t4.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
