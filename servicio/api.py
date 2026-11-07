import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from . import modelo, registro
from .interfaz import crear_interfaz
from .sql_util import es_solo_lectura

ESQUEMA_EJEMPLO = (Path(__file__).parent / "ejemplo_farmacia.sql").read_text(encoding="utf-8")


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


app = gr.mount_gradio_app(app, crear_interfaz(consultar, votar, ESQUEMA_EJEMPLO), path="/")
