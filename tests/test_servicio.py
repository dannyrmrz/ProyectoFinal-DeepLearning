import os

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
    assert cliente.get("/api/salud").json()["modelo_base"].startswith("Qwen")
    assert cliente.get("/").status_code == 200


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
