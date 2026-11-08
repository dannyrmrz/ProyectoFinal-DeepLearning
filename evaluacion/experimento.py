"""Corre el experimento completo: levanta el servicio con cada configuración y lo evalúa por la API.

    python -m evaluacion.experimento                     # las tres configuraciones + resumen
    python -m evaluacion.experimento --configs adapter   # solo una
    python -m evaluacion.experimento --solo-generar      # sin MySQL; puntuar después con --solo-puntuar

Cada configuración arranca su propio uvicorn (puerto 7861) con un registro aparte en
resultados/registros/, así no se mezcla con el registro del servicio publicado.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
from pathlib import Path

import psutil

from . import evaluar

RAIZ = evaluar.AQUI.parent
CONFIGS = {
    "base": {"USAR_ADAPTER": "0", "CUANTIZAR": "0"},
    "adapter": {"USAR_ADAPTER": "1", "CUANTIZAR": "0"},
    "adapter_int8": {"USAR_ADAPTER": "1", "CUANTIZAR": "1"},
    # Exploración posterior (no estaba en docs/hipotesis.md): surge de diagnostico_int8.py
    "adapter_int8_parcial": {"USAR_ADAPTER": "1", "CUANTIZAR": "parcial"},
}
CALENTAMIENTO = ("CREATE TABLE t (id INT PRIMARY KEY, nombre VARCHAR(20));", "¿Cuántas filas tiene t?")


class MedidorMemoria(threading.Thread):
    """Muestrea la memoria residente del servicio y guarda el máximo.

    Suma los procesos hijos: en Windows el python.exe de un venv es un lanzador y el
    intérprete que carga el modelo es su hijo.
    """

    def __init__(self, pid):
        super().__init__(daemon=True)
        self.proceso, self.maximo, self.actual, self.activo = psutil.Process(pid), 0, 0, True

    def run(self):
        while self.activo:
            try:
                procesos = [self.proceso, *self.proceso.children(recursive=True)]
                self.actual = sum(p.memory_info().rss for p in procesos)
                self.maximo = max(self.maximo, self.actual)
            except psutil.Error:
                pass
            time.sleep(0.5)


def esperar_listo(url, proceso, limite=900):
    t0 = time.time()
    while time.time() - t0 < limite:
        if proceso.poll() is not None:
            raise RuntimeError(f"el servicio terminó con código {proceso.returncode}")
        try:
            info = evaluar.salud(url)
            if info["listo"]:
                return info
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(2)
    raise TimeoutError("el modelo no cargó a tiempo")


def medir_memoria(nombre, puerto):
    """Carga el servicio, responde 3 preguntas y guarda la memoria máxima y la estable en <nombre>_servicio.json."""
    url = f"http://127.0.0.1:{puerto}"
    entorno = {**os.environ, **CONFIGS[nombre], "PRECARGAR": "1",
               "DIR_REGISTROS": str(evaluar.RESULTADOS / "registros" / f"{nombre}_memoria")}
    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "servicio.api:app", "--host", "127.0.0.1", "--port", str(puerto),
         "--log-level", "warning"], cwd=RAIZ, env=entorno)
    medidor = MedidorMemoria(proceso.pid)
    medidor.start()
    try:
        esperar_listo(url, proceso)
        esquemas = evaluar.cargar_esquemas()
        for p in evaluar.cargar_preguntas()[:3]:
            evaluar.pedir_sql(url, esquemas[p["db"]], p["pregunta"])
        estable = medidor.actual  # ya cargado y después de responder
    finally:
        medidor.activo = False
        proceso.terminate()
        proceso.wait(timeout=60)
    ruta = evaluar.RESULTADOS / f"{nombre}_servicio.json"
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    datos["memoria_max_gb"] = round(medidor.maximo / 2**30, 2)
    datos["memoria_estable_gb"] = round(estable / 2**30, 2)
    ruta.write_text(json.dumps(datos, indent=1), encoding="utf-8")
    print(f"{nombre}: memoria máx. {datos['memoria_max_gb']} GB, estable {datos['memoria_estable_gb']} GB", flush=True)


def correr(nombre, puerto, solo_generar):
    url = f"http://127.0.0.1:{puerto}"
    registros = evaluar.RESULTADOS / "registros" / nombre
    entorno = {**os.environ, **CONFIGS[nombre], "PRECARGAR": "1", "DIR_REGISTROS": str(registros)}
    (registros / "uso.jsonl").unlink(missing_ok=True)

    print(f"\n=== {nombre}: {CONFIGS[nombre]} ===", flush=True)
    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "servicio.api:app", "--host", "127.0.0.1", "--port", str(puerto),
         "--log-level", "warning"], cwd=RAIZ, env=entorno)
    medidor = MedidorMemoria(proceso.pid)
    medidor.start()
    try:
        info = esperar_listo(url, proceso)
        print(f"Modelo listo en {info['segundos_carga']} s", flush=True)
        evaluar.pedir_sql(url, *CALENTAMIENTO)  # la primera generación paga la inicialización perezosa
        t0 = time.time()
        df = evaluar.generar(url, evaluar.cargar_preguntas(), evaluar.cargar_esquemas())
        minutos = round((time.time() - t0) / 60, 1)
    finally:
        medidor.activo = False
        proceso.terminate()
        proceso.wait(timeout=60)

    df.to_csv(evaluar.RESULTADOS / f"{nombre}_pred.csv", index=False, encoding="utf-8")
    servicio = {**info, "config": CONFIGS[nombre], "memoria_max_gb": round(medidor.maximo / 2**30, 2),
                "minutos_evaluacion": minutos, "hilos_cpu": psutil.cpu_count(), "fecha": time.strftime("%Y-%m-%d %H:%M")}
    (evaluar.RESULTADOS / f"{nombre}_servicio.json").write_text(json.dumps(servicio, indent=1), encoding="utf-8")
    print(f"{nombre}: {minutos} min, memoria máx. {servicio['memoria_max_gb']} GB", flush=True)
    if not solo_generar:
        evaluar.main(["--nombre", nombre, "--solo-puntuar"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--configs", nargs="+", choices=list(CONFIGS), default=list(CONFIGS)[:3],
                        help="por defecto las tres de docs/hipotesis.md")
    parser.add_argument("--puerto", type=int, default=7861)
    parser.add_argument("--solo-generar", action="store_true", help="no puntuar en MySQL")
    parser.add_argument("--solo-memoria", action="store_true", help="solo medir la memoria de cada configuración")
    args = parser.parse_args()
    evaluar.RESULTADOS.mkdir(exist_ok=True)
    if args.solo_memoria:
        for nombre in args.configs:
            medir_memoria(nombre, args.puerto)
        return
    for nombre in args.configs:
        correr(nombre, args.puerto, args.solo_generar)
    if not args.solo_generar:
        from . import resumir

        resumir.main()


if __name__ == "__main__":
    main()
