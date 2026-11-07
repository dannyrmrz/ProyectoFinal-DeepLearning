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

_estado = {"modelo": None, "tokenizer": None, "segundos_carga": None}
_candado = threading.Lock()


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
        _estado.update(modelo=modelo.eval(), tokenizer=tokenizer, segundos_carga=round(time.time() - t0, 1))


def info():
    return {
        "listo": _estado["modelo"] is not None,
        "modelo_base": CONFIG["modelo_base"],
        "usar_adapter": CONFIG["usar_adapter"],
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
