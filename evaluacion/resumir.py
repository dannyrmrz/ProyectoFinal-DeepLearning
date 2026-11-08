"""Junta los resultados de cada configuración, evalúa H1-H3 y dibuja la comparación.

    python -m evaluacion.resumir

Lee resultados/<config>.csv y resultados/<config>_servicio.json; escribe resumen.csv,
hipotesis_resultado.md y comparacion.png.
"""
import json
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from evaluacion.evaluar import RESULTADOS, cargar_preguntas, ex_ponderada  # noqa: E402
from servicio.sql_util import es_solo_lectura  # noqa: E402

ETIQUETAS = {"base": "Base\n(sin adapter)", "adapter": "Adapter B\n(fp32)", "adapter_int8": "Adapter B\n+ int8 (H2)",
             "adapter_int8_parcial": "Adapter B + int8\nsin down_proj*"}
# Paleta categórica en orden fijo, validada con el script de dataviz (las barras llevan etiqueta directa)
COLORES = {"base": "#2a78d6", "adapter": "#eb6834", "adapter_int8": "#1baf7a", "adapter_int8_parcial": "#eda100"}
SUPERFICIE, TEXTO, TEXTO_2, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"


def resumir_config(nombre):
    df = pd.read_csv(RESULTADOS / f"{nombre}.csv")
    ruta_srv = RESULTADOS / f"{nombre}_servicio.json"
    srv = json.loads(ruta_srv.read_text(encoding="utf-8")) if ruta_srv.exists() else {}
    acierto = df.groupby("nivel")["correcto"].mean()
    seg = df["segundos"].dropna()
    return {
        "config": nombre,
        "EX ponderada": round(ex_ponderada(df), 3),
        "acierto facil": round(acierto.get("facil", float("nan")), 3),
        "acierto media": round(acierto.get("media", float("nan")), 3),
        "acierto dificil": round(acierto.get("dificil", float("nan")), 3),
        "correctas": int(df["correcto"].sum()),
        "preguntas": len(df),
        "latencia p50 (s)": round(seg.quantile(0.5), 2),
        "latencia p95 (s)": round(seg.quantile(0.95), 2),
        "latencia max (s)": round(seg.max(), 2),
        "bloqueadas por filtro": int((df["solo_lectura"] == False).sum()),  # noqa: E712
        "errores API": int(df["error_api"].notna().sum()),
        "carga (s)": srv.get("segundos_carga"),
        "memoria max (GB)": srv.get("memoria_max_gb"),
        "memoria estable (GB)": srv.get("memoria_estable_gb"),
    }


def veredictos(r):
    lineas = ["# Resultado de las hipótesis", "",
              "Generado por `python -m evaluacion.resumir`. Criterios en `docs/hipotesis.md`.", ""]
    if "base" in r and "adapter" in r:
        d = r["adapter"]["EX ponderada"] - r["base"]["EX ponderada"]
        lineas.append(f"- **H1** EX(adapter B) − EX(base) = {r['adapter']['EX ponderada']:.3f} − "
                      f"{r['base']['EX ponderada']:.3f} = **{d:+.3f}** (criterio ≥ +0.10) → "
                      f"**{'se acepta' if d >= 0.10 else 'se rechaza'}**")
    if "adapter" in r and "adapter_int8" in r:
        a, q = r["adapter"], r["adapter_int8"]
        razon = q["latencia p50 (s)"] / a["latencia p50 (s)"]
        dex = q["EX ponderada"] - a["EX ponderada"]
        ok = razon <= 0.70 and dex >= -0.03
        lineas.append(f"- **H2** p50 int8 / p50 fp32 = {q['latencia p50 (s)']:.2f} / {a['latencia p50 (s)']:.2f} = "
                      f"**{razon:.2f}** (criterio ≤ 0.70); ΔEX = **{dex:+.3f}** (criterio ≥ −0.03) → "
                      f"**{'se acepta' if ok else 'se rechaza'}**")
    if "adapter" in r and "adapter_int8_parcial" in r:
        a, q = r["adapter"], r["adapter_int8_parcial"]
        razon = q["latencia p50 (s)"] / a["latencia p50 (s)"]
        dex = q["EX ponderada"] - a["EX ponderada"]
        ok = razon <= 0.70 and dex >= -0.03
        lineas.append(f"- *Exploración posterior (no registrada antes de medir)* int8 sin `down_proj`: "
                      f"p50 {q['latencia p50 (s)']:.2f} / {a['latencia p50 (s)']:.2f} = **{razon:.2f}**; "
                      f"ΔEX = **{dex:+.3f}** → con los criterios de H2 {'cumpliría' if ok else 'tampoco cumpliría'}")
    refs = [p["sql"] for p in cargar_preguntas()]
    refs_ok = sum(es_solo_lectura(s) for s in refs)
    bloqueadas = sum(x["bloqueadas por filtro"] for x in r.values())
    lineas.append(f"- **H3** referencias que pasan el filtro: **{refs_ok}/{len(refs)}**; predicciones bloqueadas "
                  f"en todas las configuraciones: **{bloqueadas}** → "
                  f"**{'se acepta' if refs_ok == len(refs) and bloqueadas == 0 else 'revisar las bloqueadas en resultados/registros/'}**")
    return "\n".join(lineas) + "\n"


def graficar(resumen, ruta):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "sans-serif", "font.size": 11, "text.color": TEXTO,
                         "axes.labelcolor": TEXTO_2, "xtick.color": TEXTO_2, "ytick.color": TEXTO_2})
    nombres = list(resumen["config"])
    x = range(len(nombres))
    colores = [COLORES[n] for n in nombres]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor=SUPERFICIE)

    paneles = [
        (ax1, resumen["EX ponderada"], "EX ponderada (más es mejor)", "{:.3f}", (0, 1)),
        (ax2, resumen["latencia p50 (s)"], "Latencia por pregunta en CPU (menos es mejor)", "{:.1f} s", None),
    ]
    for ax, valores, titulo, fmt, lim in paneles:
        ax.set_facecolor(SUPERFICIE)
        ax.bar(x, valores, width=0.55, color=colores, edgecolor=SUPERFICIE, linewidth=2, zorder=2)
        for i, v in zip(x, valores):
            ax.annotate(fmt.format(v), (i, v), xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=11, color=TEXTO)
        ax.set_xticks(list(x), [ETIQUETAS[n] for n in nombres])
        ax.set_title(titulo, loc="left", fontsize=12, color=TEXTO, pad=12)
        ax.grid(axis="y", color=REJILLA, linewidth=0.8, zorder=0)
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        ax.spines["bottom"].set_color(REJILLA)
        ax.tick_params(axis="both", length=0)
        if lim:
            ax.set_ylim(*lim)

    # p95 como marca fina sobre la barra de p50
    p95 = resumen["latencia p95 (s)"]
    ax2.scatter(list(x), p95, marker="_", s=600, linewidths=2, color=TEXTO_2, zorder=3, label="p95")
    for i, v in zip(x, p95):
        ax2.annotate(f"p95 {v:.1f} s", (i, v), xytext=(0, 4), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9, color=TEXTO_2)
    ax2.set_ylim(0, max(p95) * 1.18)
    ax2.set_ylabel("segundos (barra = p50)")

    fig.suptitle("Validación propia (40 preguntas) a través de la API, CPU", x=0.01, ha="left",
                 fontsize=13, fontweight="bold", color=TEXTO)
    if "adapter_int8_parcial" in nombres:
        fig.text(0.01, 0.01, "* exploración posterior al rechazo de H2; no estaba en las hipótesis registradas",
                 fontsize=9, color=TEXTO_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ruta, dpi=160, facecolor=SUPERFICIE)
    plt.close(fig)


def main():
    # Algunas consolas de Windows usan cp1252; los archivos conservan UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    nombres = [n for n in ETIQUETAS if (RESULTADOS / f"{n}.csv").exists()]
    if not nombres:
        raise SystemExit("No hay resultados puntuados en evaluacion/resultados/")
    r = {n: resumir_config(n) for n in nombres}
    resumen = pd.DataFrame(r.values())
    resumen.to_csv(RESULTADOS / "resumen.csv", index=False, encoding="utf-8")
    texto = veredictos(r)
    (RESULTADOS / "hipotesis_resultado.md").write_text(texto, encoding="utf-8")
    graficar(resumen, RESULTADOS / "comparacion.png")
    print(resumen.to_string(index=False))
    print()
    print(texto)


if __name__ == "__main__":
    main()
