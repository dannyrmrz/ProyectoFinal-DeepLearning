import os
import threading
import time

import pytest
from fastapi.testclient import TestClient

os.environ["PRECARGAR"] = "0"

from servicio import api, modelo, registro  # noqa: E402
from servicio.sql_util import es_solo_lectura  # noqa: E402

ESQUEMA = "CREATE TABLE t (id INT PRIMARY KEY);"


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(registro, "ARCHIVO", tmp_path / "uso.jsonl")
    monkeypatch.setattr(modelo, "generar_sql", lambda e, p: "DELETE FROM t" if "borra" in p else "SELECT COUNT(*) FROM t")
    with TestClient(api.app) as c:
        yield c


def test_genera_y_registra(cliente):
    r = cliente.post("/api/sql", json={"esquema": ESQUEMA, "pregunta": "¿Cuántas filas hay?"}).json()
    assert r["sql"] == "SELECT COUNT(*) FROM t" and r["solo_lectura"]
    assert registro.leer()[0]["id"] == r["id"]


def test_bloquea_escritura(cliente):
    r = cliente.post("/api/sql", json={"esquema": ESQUEMA, "pregunta": "borra todo"}).json()
    assert r["sql"] == "" and not r["solo_lectura"]


def test_valida_entrada(cliente):
    assert cliente.post("/api/sql", json={"esquema": "", "pregunta": "hola"}).status_code == 422


def test_feedback_y_metricas(cliente):
    id_ = cliente.post("/api/sql", json={"esquema": ESQUEMA, "pregunta": "¿Cuántas filas hay?"}).json()["id"]
    assert cliente.post("/api/feedback", json={"id": id_, "correcto": True}).status_code == 200
    assert cliente.post("/api/feedback", json={"id": "nada", "correcto": True}).status_code == 404
    m = cliente.get("/api/metricas").json()
    assert m["solicitudes"] == 1 and m["votos"] == 1 and m["tasa_correcto"] == 1.0
    assert id_ in cliente.get("/api/registros").text


def test_salud_e_interfaz(cliente):
    assert "CREATE TABLE" in cliente.get("/api/ejemplo").text
    assert cliente.get("/api/salud").json()["modelo_base"].startswith("Qwen")
    assert "Generar SQL" in cliente.get("/").text
    assert cliente.get("/").headers["cache-control"] == "no-store"


def _esperar_tarea(cliente, id_):
    limite = time.monotonic() + 5
    while time.monotonic() < limite:
        tarea = cliente.get(f"/api/tareas/{id_}").json()
        if tarea["estado"] in ("completada", "error"):
            return tarea
        time.sleep(0.01)
    pytest.fail("La tarea no terminó")


def test_tareas_responden_sin_esperar_y_conservan_el_turno(cliente, monkeypatch):
    monkeypatch.setattr(api, "_tareas", {})
    iniciada, continuar = threading.Event(), threading.Event()
    llamadas = []

    def generar(esquema, pregunta):
        llamadas.append(pregunta)
        iniciada.set()
        if not continuar.wait(10):
            raise TimeoutError("La prueba no liberó la generación")
        return "SELECT COUNT(*) FROM t"

    monkeypatch.setattr(modelo, "generar_sql", generar)
    datos = {"esquema": ESQUEMA, "pregunta": "¿Cuántas filas hay?"}
    try:
        primera = cliente.post("/api/tareas", json=datos)
        assert primera.status_code == 202
        assert iniciada.wait(3)
        segunda = cliente.post("/api/tareas", json=datos)
        assert segunda.status_code == 202
        assert cliente.get(f"/api/tareas/{primera.json()['id']}").json()["estado"] == "procesando"
        assert cliente.get(f"/api/tareas/{segunda.json()['id']}").json()["estado"] == "en_cola"
        assert len(llamadas) == 1
        assert registro.leer() == []
    finally:
        continuar.set()
    resultado = _esperar_tarea(cliente, primera.json()["id"])["respuesta"]
    assert resultado["sql"] == "SELECT COUNT(*) FROM t"
    assert _esperar_tarea(cliente, segunda.json()["id"])["estado"] == "completada"
    assert cliente.get(f"/api/tareas/{primera.json()['id']}").json()["respuesta"] == resultado
    assert cliente.post("/api/feedback", json={"id": resultado["id"], "correcto": True}).status_code == 200
    assert len(registro.leer()) == 3


def test_tarea_fallida_permite_procesar_la_siguiente(cliente, monkeypatch):
    monkeypatch.setattr(api, "_tareas", {})

    def fallar(esquema, pregunta):
        raise RuntimeError("detalle interno")

    monkeypatch.setattr(modelo, "generar_sql", fallar)
    datos = {"esquema": ESQUEMA, "pregunta": "¿Cuántas filas hay?"}
    id_ = cliente.post("/api/tareas", json=datos).json()["id"]
    tarea = _esperar_tarea(cliente, id_)
    assert tarea["estado"] == "error"
    assert "detalle interno" not in tarea["error"]
    assert "detalle interno" in registro.leer()[0]["error"]
    monkeypatch.setattr(modelo, "generar_sql", lambda e, p: "SELECT 1")
    id_ = cliente.post("/api/tareas", json=datos).json()["id"]
    assert _esperar_tarea(cliente, id_)["respuesta"]["sql"] == "SELECT 1"
    assert cliente.get("/api/tareas/desconocida").status_code == 404


@pytest.mark.parametrize("sql,esperado", [
    ("SELECT * FROM t;", True),
    ("WITH a AS (SELECT 1) SELECT * FROM a", True),
    ("SELECT 'drop; x' FROM t", True),
    ("SELECT 1; DROP TABLE t", False),
    ("SELECT * INTO OUTFILE 'x' FROM t", False),
    ("UPDATE t SET id = 1", False),
])
def test_solo_lectura(sql, esperado):
    assert es_solo_lectura(sql) == esperado
