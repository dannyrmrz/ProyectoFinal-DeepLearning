import json
import os
import threading
import time
from pathlib import Path

from .prompt import mensajes
from .sql_util import extraer_sql

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
if os.getenv("USAR_ADAPTER") is not None:
    CONFIG["usar_adapter"] = os.getenv("USAR_ADAPTER") == "1"
CONFIG["adapter"] = os.getenv("ADAPTER", CONFIG["adapter"])
# CUANTIZAR: "0" fp32 (por defecto), "1" int8 en todas las Linear (H2), "parcial" int8 sin down_proj
CONFIG["cuantizar"] = os.getenv("CUANTIZAR", str(CONFIG.get("cuantizar", "0")))
if CONFIG["cuantizar"] not in ("0", "1", "parcial"):
    raise ValueError(f"CUANTIZAR debe ser 0, 1 o parcial, no {CONFIG['cuantizar']!r}")

_estado = {"modelo": None, "tokenizer": None, "segundos_carga": None}
_candado = threading.Lock()


def cuantizar_int8(modelo, parcial=False):
    """Cuantización dinámica int8 de las capas Linear (pesos en int8, activaciones cuantizadas al vuelo).

    Se aplica después de merge_and_unload para que el adapter ya esté dentro de los pesos.
    lm_head se deja en fp32: comparte pesos con los embeddings y es la capa más sensible.
    Con parcial=True también quedan en fp32 las mlp.down_proj: reciben la salida de SwiGLU, con
    outliers de activación que una sola escala int8 por tensor no puede representar
    (ver evaluacion/diagnostico_int8.py).
    """
    import warnings

    import torch
    from torch.ao.quantization import default_dynamic_qconfig, quantize_dynamic

    # Por tipo se cuantizan todas las Linear; por nombre se excluyen capas (el nombre tiene prioridad)
    reglas = {torch.nn.Linear: default_dynamic_qconfig, "lm_head": None}
    if parcial:
        reglas.update({n: None for n, _ in modelo.named_modules() if n.endswith("mlp.down_proj")})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # torch.ao.quantization está marcado como obsoleto desde torch 2.10
        # inplace: sin copia del modelo fp32 (con copia, el pico de memoria se duplica)
        return quantize_dynamic(modelo, reglas, dtype=torch.qint8, inplace=True)


def cargar():
    with _candado:
        if _estado["modelo"] is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        t0 = time.time()
        torch.manual_seed(CONFIG["semilla"])
        tokenizer = AutoTokenizer.from_pretrained(CONFIG["modelo_base"])
        modelo = AutoModelForCausalLM.from_pretrained(CONFIG["modelo_base"], dtype=torch.float32)
        if CONFIG["usar_adapter"]:
            from peft import PeftModel

            modelo = PeftModel.from_pretrained(modelo, str(RAIZ / CONFIG["adapter"])).merge_and_unload()
        if CONFIG["cuantizar"] != "0":
            modelo = cuantizar_int8(modelo, parcial=CONFIG["cuantizar"] == "parcial")
        _estado.update(modelo=modelo.eval(), tokenizer=tokenizer, segundos_carga=round(time.time() - t0, 1))


def info():
    return {
        "listo": _estado["modelo"] is not None,
        "modelo_base": CONFIG["modelo_base"],
        "usar_adapter": CONFIG["usar_adapter"],
        "cuantizar": CONFIG["cuantizar"],
        "segundos_carga": _estado["segundos_carga"],
    }


def generar_sql(esquema: str, pregunta: str) -> str:
    import torch

    cargar()
    tokenizer, modelo = _estado["tokenizer"], _estado["modelo"]
    texto = tokenizer.apply_chat_template(mensajes(esquema, pregunta), tokenize=False, add_generation_prompt=True)
    entrada = tokenizer(texto, return_tensors="pt")
    with _candado, torch.no_grad():
        salida = modelo.generate(
            **entrada, max_new_tokens=CONFIG["max_tokens"], do_sample=False, pad_token_id=tokenizer.eos_token_id
        )
    return extraer_sql(tokenizer.decode(salida[0][entrada["input_ids"].shape[1]:], skip_special_tokens=True))
