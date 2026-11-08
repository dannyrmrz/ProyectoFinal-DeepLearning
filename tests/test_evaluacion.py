"""Pruebas de la evaluación y de la cuantización sin cargar el modelo ni MySQL."""
import json
import io

import pandas as pd
import pytest

from evaluacion import evaluar, resumir
from servicio import modelo
from servicio.sql_util import es_solo_lectura


def test_datos_de_validacion_completos():
    preguntas, esquemas = evaluar.cargar_preguntas(), evaluar.cargar_esquemas()
    assert len(preguntas) == 40
    assert {p["db"] for p in preguntas} == set(esquemas) == {"farmacia", "evt_tix"}
    assert sum(evaluar.PESOS[p["nivel"]] for p in preguntas) == 82
    assert all(len(e) <= 20000 for e in esquemas.values())  # límite de la API


def test_referencias_pasan_el_filtro():
    assert all(es_solo_lectura(p["sql"]) for p in evaluar.cargar_preguntas())


@pytest.mark.parametrize("pred,ref,orden,esperado", [
    ([(1, "a"), (2, "b")], [("a",), ("b",)], False, True),         # columna extra no penaliza
    ([(2, "b"), (1, "a")], [("a",), ("b",)], False, True),          # sin orden
    ([(2, "b"), (1, "a")], [("a",), ("b",)], True, False),          # con orden
    ([("a",)], [("a",), ("b",)], False, False),                     # faltan filas
    ([], [], False, True),
    ([(1, 2), (2, 3), (3, 1)], [(2, 1), (3, 2), (1, 3)], False, True),
    ([(1, 2), (2, 3), (3, 1)], [(2, 1), (3, 2), (1, 3)], True, True),
    ([(1, 1), (2, 2), (3, 3)], [(1, 2), (2, 3), (3, 1)], False, False),
    ([(1,), (1,), (2,)], [(1,), (2,), (2,)], False, False),
])
def test_coinciden(pred, ref, orden, esperado):
    assert evaluar.coinciden(pred, ref, orden) == esperado


def test_ex_ponderada():
    df = pd.DataFrame({"nivel": ["facil", "media", "dificil"], "correcto": [True, False, True]})
    assert evaluar.ex_ponderada(df) == pytest.approx(4 / 6)


def test_generar_registra_errores_de_la_api():
    preguntas = evaluar.cargar_preguntas()[:2]

    def pedir(url, esquema, pregunta):
        if "receta" in pregunta:
            return {"sql": "SELECT 1", "solo_lectura": True, "segundos": 1.5}
        raise TimeoutError("lento")

    df = evaluar.generar("http://x", preguntas, evaluar.cargar_esquemas(), pedir=pedir, mostrar=False)
    assert df.loc[0, "sql_pred"] == "SELECT 1" and df.loc[0, "segundos"] == 1.5
    assert df.loc[1, "sql_pred"] == "" and "TimeoutError" in df.loc[1, "error_api"]


def test_puntuar_sin_mysql_para_bloqueadas_y_errores():
    df = pd.DataFrame([
        {"id": 1, "db": "farmacia", "nivel": "facil", "sql_ref": "SELECT 1", "sql_pred": "", "error_api": None},
        {"id": 2, "db": "farmacia", "nivel": "facil", "sql_ref": "SELECT 1", "sql_pred": "", "error_api": "x"},
    ])
    r = evaluar.puntuar(df, evaluar.cargar_preguntas())
    assert list(r["categoria"]) == ["bloqueada por el filtro", "error de la API"]
    assert not r["correcto"].any()


def _resultado(tmp_path, nombre, correctas, segundos):
    preguntas = evaluar.cargar_preguntas()
    pd.DataFrame([{"id": p["id"], "nivel": p["nivel"], "correcto": i < correctas, "segundos": segundos,
                   "solo_lectura": True, "error_api": None} for i, p in enumerate(preguntas)]
                 ).to_csv(tmp_path / f"{nombre}.csv", index=False)
    (tmp_path / f"{nombre}_servicio.json").write_text(json.dumps({"segundos_carga": 10}), encoding="utf-8")


def test_resumir_evalua_hipotesis(tmp_path, monkeypatch):
    monkeypatch.setattr(resumir, "RESULTADOS", tmp_path)
    _resultado(tmp_path, "base", 10, 10.0)
    _resultado(tmp_path, "adapter", 30, 10.0)
    _resultado(tmp_path, "adapter_int8", 30, 5.0)
    resumir.main()
    texto = (tmp_path / "hipotesis_resultado.md").read_text(encoding="utf-8")
    assert texto.count("se acepta") == 3
    assert (tmp_path / "comparacion.png").stat().st_size > 10_000
    assert len(pd.read_csv(tmp_path / "resumen.csv")) == 3


def test_resumir_en_consola_cp1252(tmp_path, monkeypatch):
    monkeypatch.setattr(resumir, "RESULTADOS", tmp_path)
    _resultado(tmp_path, "base", 10, 10.0)
    _resultado(tmp_path, "adapter", 30, 10.0)
    buffer = io.BytesIO()
    salida = io.TextIOWrapper(buffer, encoding="cp1252")
    with monkeypatch.context() as m:
        m.setattr(resumir.sys, "stdout", salida)
        resumir.main()
        salida.flush()
    assert b"H1" in buffer.getvalue()
    assert "≥" in (tmp_path / "hipotesis_resultado.md").read_text(encoding="utf-8")


def test_cuantizar_int8_respeta_lm_head():
    import torch

    class Mini(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.capa = torch.nn.Linear(8, 8)
            self.lm_head = torch.nn.Linear(8, 4)

        def forward(self, x):
            return self.lm_head(self.capa(x))

    from torch.ao.nn.quantized.dynamic import Linear as LinearInt8

    q = modelo.cuantizar_int8(Mini())
    assert isinstance(q.capa, LinearInt8)
    assert type(q.lm_head) is torch.nn.Linear
    assert q(torch.randn(2, 8)).shape == (2, 4)


def test_cuantizar_parcial_deja_down_proj_en_fp32():
    import torch
    from torch.ao.nn.quantized.dynamic import Linear as LinearInt8

    mlp = torch.nn.Module()
    mlp.up_proj, mlp.down_proj = torch.nn.Linear(8, 8), torch.nn.Linear(8, 8)
    m = torch.nn.Module()
    m.mlp = mlp
    q = modelo.cuantizar_int8(m, parcial=True)
    assert isinstance(q.mlp.up_proj, LinearInt8)
    assert type(q.mlp.down_proj) is torch.nn.Linear


def test_salud_informa_cuantizacion():
    assert "cuantizar" in modelo.info()


def test_diagnostico_carga_referencia_fp32(monkeypatch):
    from evaluacion import diagnostico_int8

    monkeypatch.setattr(modelo, "CONFIG", dict(modelo.CONFIG))

    def cargar():
        assert modelo.CONFIG["cuantizar"] == "0"
        assert modelo.CONFIG["usar_adapter"] is True
        raise RuntimeError("referencia comprobada")

    monkeypatch.setattr(modelo, "cargar", cargar)
    with pytest.raises(RuntimeError, match="referencia comprobada"):
        diagnostico_int8.main()
