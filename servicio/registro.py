import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

ARCHIVO = Path(os.getenv("DIR_REGISTROS", "registros")) / "uso.jsonl"
_candado = threading.Lock()


def registrar(tipo: str, **datos):
    evento = {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tipo": tipo, **datos}
    with _candado:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
        with ARCHIVO.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return evento


def leer():
    if not ARCHIVO.exists():
        return []
    return [json.loads(l) for l in ARCHIVO.read_text(encoding="utf-8").splitlines() if l.strip()]


def _percentil(valores, p):
    if not valores:
        return None
    valores = sorted(valores)
    return valores[min(len(valores) - 1, int(round(p * (len(valores) - 1))))]


def metricas():
    eventos = leer()
    consultas = [e for e in eventos if e["tipo"] == "consulta"]
    exitosas = [e for e in consultas if not e.get("error")]
    votos = [e["correcto"] for e in eventos if e["tipo"] == "feedback"]
    tiempos = [e["segundos"] for e in exitosas]
    return {
        "solicitudes": len(consultas),
        "errores": len(consultas) - len(exitosas),
        "latencia_p50": _percentil(tiempos, 0.5),
        "latencia_p95": _percentil(tiempos, 0.95),
        "tasa_solo_lectura": round(sum(e["solo_lectura"] for e in exitosas) / len(exitosas), 3) if exitosas else None,
        "votos": len(votos),
        "tasa_correcto": round(sum(votos) / len(votos), 3) if votos else None,
        "ultima_solicitud": consultas[-1]["fecha"] if consultas else None,
    }
