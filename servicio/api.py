import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from . import modelo, registro
from .sql_util import es_solo_lectura

CARPETA = Path(__file__).parent
_cola = ThreadPoolExecutor(max_workers=1)
_tareas = {}
_candado_tareas = threading.Lock()


class Solicitud(BaseModel):
    esquema: str = Field(min_length=10, max_length=20000)
    pregunta: str = Field(min_length=3, max_length=500)


class Voto(BaseModel):
    id: str
    correcto: bool
    comentario: str = Field("", max_length=500)


def consultar(esquema: str, pregunta: str) -> dict:
    id_ = uuid.uuid4().hex[:12]
    t0 = time.time()
    try:
        sql = modelo.generar_sql(esquema, pregunta)
    except Exception as e:
        registro.registrar("consulta", id=id_, pregunta=pregunta, error=repr(e), segundos=round(time.time() - t0, 2))
        raise
    seguro = es_solo_lectura(sql)
    respuesta = {"id": id_, "sql": sql if seguro else "", "solo_lectura": seguro, "segundos": round(time.time() - t0, 2)}
    registro.registrar("consulta", pregunta=pregunta, sql_generado=sql, largo_esquema=len(esquema), **respuesta)
    return respuesta


def votar(id_: str, correcto: bool, comentario: str = "") -> dict:
    if not any(e.get("id") == id_ for e in registro.leer() if e["tipo"] == "consulta"):
        raise HTTPException(404, "id desconocido")
    return registro.registrar("feedback", id=id_, correcto=correcto, comentario=comentario)


@asynccontextmanager
async def ciclo_de_vida(_):
    if os.getenv("PRECARGAR", "1") == "1":
        threading.Thread(target=modelo.cargar, daemon=True).start()
    yield


app = FastAPI(title="Text-to-SQL", lifespan=ciclo_de_vida)


@app.post("/api/sql")
def api_sql(s: Solicitud):
    return consultar(s.esquema, s.pregunta)


def _procesar_tarea(id_: str, solicitud: Solicitud):
    with _candado_tareas:
        _tareas[id_] = {"estado": "procesando"}
    try:
        respuesta = consultar(solicitud.esquema, solicitud.pregunta)
        resultado = {"estado": "completada", "respuesta": respuesta}
    except Exception:
        resultado = {"estado": "error", "error": "No se pudo generar la consulta. Intenta nuevamente."}
    with _candado_tareas:
        _tareas[id_] = resultado


@app.post("/api/tareas", status_code=202)
def api_crear_tarea(s: Solicitud):
    id_ = uuid.uuid4().hex
    with _candado_tareas:
        activas = sum(t["estado"] in ("en_cola", "procesando") for t in _tareas.values())
        if activas >= 10:
            raise HTTPException(429, "El servicio está ocupado. Intenta en unos minutos.")
        if len(_tareas) >= 100:
            anterior = next(k for k, v in _tareas.items() if v["estado"] in ("completada", "error"))
            del _tareas[anterior]
        _tareas[id_] = {"estado": "en_cola"}
    _cola.submit(_procesar_tarea, id_, s)
    return {"id": id_, "estado": "en_cola"}


@app.get("/api/tareas/{id_}")
def api_obtener_tarea(id_: str):
    with _candado_tareas:
        if id_ not in _tareas:
            raise HTTPException(404, "La solicitud ya no está disponible. Genera la consulta nuevamente.")
        return dict(_tareas[id_])


@app.post("/api/feedback")
def api_feedback(v: Voto):
    return votar(v.id, v.correcto, v.comentario)


@app.get("/api/salud")
def api_salud():
    return modelo.info()


@app.get("/api/metricas")
def api_metricas():
    return registro.metricas()


@app.get("/api/registros", response_class=PlainTextResponse)
def api_registros():
    return registro.ARCHIVO.read_text(encoding="utf-8") if registro.ARCHIVO.exists() else ""


@app.get("/api/ejemplo", response_class=PlainTextResponse)
def api_ejemplo():
    return (CARPETA / "ejemplo_farmacia.sql").read_text(encoding="utf-8")


@app.get("/")
def inicio():
    return FileResponse(CARPETA / "index.html", headers={"Cache-Control": "no-store"})
