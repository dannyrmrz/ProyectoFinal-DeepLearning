# Evaluación del servicio en producción

Mide la calidad (EX ponderada) y la latencia del servicio **a través de su API**, con la validación propia del Proyecto 3. Hipótesis y criterios: [docs/hipotesis.md](../docs/hipotesis.md). Resultados e interpretación: [docs/modelo_y_validacion.md](../docs/modelo_y_validacion.md).

```
datos/          farmacia.sql y evt_tix.sql (esquema + datos), preguntas.json (40), esquemas.json (SHOW CREATE TABLE)
evaluar.py      envía cada pregunta a POST /api/sql y puntúa en MySQL
experimento.py  levanta el servicio con cada configuración y llama a evaluar.py
resumir.py      resumen.csv, hipotesis_resultado.md y comparacion.png
resultados/     CSV por pregunta, datos de cada corrida, registros del servicio y resumen
```

## Requisitos

- Entorno del proyecto con `requirements.txt` y `requirements-dev.txt` (~8 GB de RAM libres).
- MySQL 8.4.10 en el puerto 3307:

```bash
docker run -d --name mysql84 -e MYSQL_ROOT_PASSWORD=root -p 3307:3306 mysql:8.4.10
```

Otro servidor: variables `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER` y `MYSQL_PASSWORD`.

## Ejecutar

Experimento completo (las tres configuraciones, unos 30–60 min en CPU):

```bash
python -m evaluacion.experimento
```

| Configuración | Variables del servicio |
|---|---|
| `base` (línea base) | `USAR_ADAPTER=0` |
| `adapter` | `USAR_ADAPTER=1` |
| `adapter_int8` | `USAR_ADAPTER=1 CUANTIZAR=1` |
| `adapter_int8_parcial` (exploración posterior, `--configs adapter_int8_parcial`) | `USAR_ADAPTER=1 CUANTIZAR=parcial` |

Otros modos:

- `python -m evaluacion.experimento --solo-memoria` mide la memoria máxima y la estable de cada configuración.
- `python -m evaluacion.diagnostico_int8` compara token a token fp32 contra las variantes int8 (`resultados/diagnostico_int8.json`). Ejecútalo en un proceso nuevo, sin inferencias concurrentes; comprueba que la referencia no contiene capas int8. Los tiempos son de una pasada por prompt y pueden variar entre corridas.

Evaluar un servicio que ya está corriendo (local o la URL pública):

```bash
python -m evaluacion.evaluar --url http://localhost:7860 --nombre adapter
```

Sin MySQL a mano, generar ahora y puntuar después:

```bash
python -m evaluacion.experimento --solo-generar
python -m evaluacion.evaluar --nombre adapter --solo-puntuar
python -m evaluacion.resumir
```

## Cómo se puntúa

Una predicción es correcta si al ejecutarla en MySQL devuelve el mismo resultado que la referencia: cada columna de la referencia debe aparecer en la predicción (las columnas extra no penalizan), los decimales se redondean a 2 y el orden de las filas solo importa cuando la pregunta lo pide. Pesos 1 / 2 / 3 para fácil / media / difícil.

El puntuador adapta el del Proyecto 3 y busca correspondencias de columnas preservando las filas completas, incluso cuando varias columnas tienen la misma distribución. Las 40 consultas de referencia dan EX = 1.000; al volver a puntuar las 160 predicciones CPU se obtienen los aciertos guardados. Las métricas T4 son históricas y agregadas; sus predicciones no están incluidas.

La cronología disponible no acredita que el commit de hipótesis precediera a la corrida base. Véase la limitación documentada en `docs/modelo_y_validacion.md`; se conservan los criterios y registros originales.
