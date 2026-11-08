"""Diagnóstico de H2: ¿por qué la cuantización int8 dinámica destruye la calidad?

Compara, sobre los prompts reales de la validación, la predicción del siguiente token del modelo
fp32 (adapter B fusionado) contra variantes cuantizadas. Mide el acuerdo top-1 en todas las
posiciones del prompt, la desviación de los logits y el tiempo de una pasada (prefill).

    python -m evaluacion.diagnostico_int8
"""
import copy
import json
import time
import warnings

import torch
from torch.ao.quantization import QConfig, default_dynamic_qconfig, per_channel_dynamic_qconfig, quantize_dynamic
from torch.ao.quantization.observer import MinMaxObserver, PlaceholderObserver

from servicio import modelo as srv
from servicio.prompt import mensajes

from .evaluar import RESULTADOS, cargar_esquemas, cargar_preguntas

# Activaciones con 7 bits (reduce_range): evita la saturación u8×s8 de AVX2 sin VNNI
QCONFIG_7BITS = QConfig(
    activation=PlaceholderObserver.with_args(dtype=torch.quint8, quant_min=0, quant_max=127, is_dynamic=True),
    weight=MinMaxObserver.with_args(dtype=torch.qint8, qscheme=torch.per_tensor_symmetric),
)
VARIANTES = {
    "int8 por tensor (servicio)": {torch.nn.Linear: default_dynamic_qconfig, "lm_head": None},
    "int8 por canal": {torch.nn.Linear: per_channel_dynamic_qconfig, "lm_head": None},
    "int8 activaciones 7 bits": {torch.nn.Linear: QCONFIG_7BITS, "lm_head": None},
    # down_proj recibe las activaciones con outliers de Qwen (salida de SwiGLU); se deja en fp32
    "int8 sin down_proj": {torch.nn.Linear: default_dynamic_qconfig, "lm_head": None,
                           **{f"model.layers.{i}.mlp.down_proj": None for i in range(28)}},
}


def entradas(tokenizer, n=4):
    esquemas, preguntas = cargar_esquemas(), cargar_preguntas()
    elegidas = [preguntas[0], preguntas[13], preguntas[20], preguntas[33]][:n]
    for p in elegidas:
        texto = tokenizer.apply_chat_template(mensajes(esquemas[p["db"]], p["pregunta"]), tokenize=False,
                                              add_generation_prompt=True)
        yield tokenizer(texto, return_tensors="pt")


@torch.no_grad()
def logits(m, ent):
    t0 = time.time()
    salida = m(**ent).logits[0]
    return salida, time.time() - t0


def main():
    srv.CONFIG.update(usar_adapter=True, cuantizar="0")
    srv.cargar()
    base, tokenizer = srv._estado["modelo"], srv._estado["tokenizer"]
    from torch.ao.nn.quantized.dynamic import Linear as LinearInt8

    if any(isinstance(m, LinearInt8) for m in base.modules()):
        raise RuntimeError("La referencia debe ser fp32; ejecute el diagnóstico en un proceso nuevo")
    ents = list(entradas(tokenizer))
    ref = [logits(base, e) for e in ents]
    filas = [{"variante": "fp32 (referencia)", "acuerdo_top1": 1.0, "error_relativo_logits": 0.0,
              "segundos_prefill": round(sum(s for _, s in ref) / len(ref), 2)}]
    for nombre, reglas in VARIANTES.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            q = quantize_dynamic(copy.deepcopy(base), reglas, dtype=torch.qint8, inplace=True)
        acuerdo, error, tiempos = [], [], []
        for e, (lr, _) in zip(ents, ref):
            lq, s = logits(q, e)
            acuerdo.append((lq.argmax(-1) == lr.argmax(-1)).float().mean().item())
            error.append(((lq - lr).norm() / lr.norm()).item())
            tiempos.append(s)
        filas.append({"variante": nombre, "acuerdo_top1": round(sum(acuerdo) / len(acuerdo), 3),
                      "error_relativo_logits": round(sum(error) / len(error), 3),
                      "segundos_prefill": round(sum(tiempos) / len(tiempos), 2)})
        print(filas[-1], flush=True)
        del q
    RESULTADOS.mkdir(exist_ok=True)
    (RESULTADOS / "diagnostico_int8.json").write_text(json.dumps(filas, indent=1, ensure_ascii=False),
                                                      encoding="utf-8")
    for f in filas:
        print(f"{f['variante']:28} top-1 {f['acuerdo_top1']:.3f}  error {f['error_relativo_logits']:.3f}  "
              f"prefill {f['segundos_prefill']:.1f} s")


if __name__ == "__main__":
    main()
