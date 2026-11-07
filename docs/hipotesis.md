# Hipótesis y criterios de éxito

Escrito **antes** de medir en el servicio. Los resultados se reportan en [modelo_y_validacion.md](modelo_y_validacion.md) sin cambiar estos criterios.

## Qué se mide

- **Conjunto:** validación propia del Proyecto 3 (`evaluacion/datos/`): 40 preguntas sobre 2 esquemas que no aparecen en el entrenamiento (`farmacia`, nombres en español con `COMMENT`; `evt_tix`, nombres en inglés abreviados). 12 fáciles, 14 medias y 14 difíciles.
- **Cómo:** `evaluacion/evaluar.py` envía cada pregunta a `POST /api/sql` del servicio corriendo en CPU, exactamente como lo haría un usuario. Se mide lo que está en producción, no un notebook.
- **Métrica de calidad: EX ponderada.** Una predicción es correcta si, al ejecutarla en MySQL 8.4.10, devuelve el mismo resultado que la consulta de referencia (las columnas extra no penalizan; el orden importa solo si la pregunta lo pide). Peso 1 / 2 / 3 para fácil / media / difícil (total 82).
- **Métrica de producción: latencia** por pregunta medida por el servicio (`segundos` de la respuesta), reportada como p50 y p95.
- **Línea base:** `Qwen/Qwen2.5-Coder-1.5B-Instruct` sin adapter, con el mismo prompt y la misma generación greedy (`USAR_ADAPTER=0`).
- **Entorno:** CPU de la PC del equipo, una solicitud a la vez, generación determinista (`do_sample=False`, `max_tokens=256`). El servicio no ejecuta SQL, así que no se usa la autocorrección con `ejecutar` del Proyecto 3; la referencia comparable del Proyecto 3 es la columna *sin `ejecutar`*.

## H1. El adapter LoRA mejora la calidad en producción

El adapter B (LoRA atención + MLP) supera al modelo base en EX ponderada sobre la validación propia, medida a través de la API en CPU.

- **Criterio de éxito:** EX(adapter B) − EX(base) **≥ 0.10**.
- **Por qué 0.10:** en el Proyecto 3 (T4, fp16) la diferencia sin `ejecutar` fue 0.646 − 0.439 = 0.207. Exigir la mitad confirma que el pase a CPU/fp32 y a la API no borró la mejora, con margen para el ruido de 40 preguntas (una pregunta difícil vale 0.037).

## H2. Cuantización int8 reduce la latencia sin perder calidad

Cuantizar dinámicamente a int8 las capas `Linear` del modelo ya fusionado (`merge_and_unload`), activado con `CUANTIZAR=1`, reduce la latencia en CPU sin una pérdida relevante de calidad.

- **Criterio de éxito (se deben cumplir ambos):**
  - latencia p50 de adapter B + int8 **≤ 0.70 ×** la de adapter B (baja ≥ 30 %), y
  - EX(adapter B + int8) **≥ EX(adapter B) − 0.03**.
- **Por qué:** en CPU la generación está limitada por el ancho de banda de memoria; int8 mueve 4 veces menos bytes por peso que fp32. Una baja de 30 % es la mínima que un usuario notaría; 0.03 es menos de una pregunta difícil.
- **Decisión:** si H2 se cumple, el servicio publicado se activa con `CUANTIZAR=1`; si no, se mantiene fp32 y se documenta la hipótesis como rechazada.

## H3. El filtro de solo lectura no bloquea consultas válidas

`es_solo_lectura` no rechaza ninguna de las 40 consultas de referencia ni ninguna predicción que MySQL ejecute sin error.

- **Criterio de éxito:** 0 falsos positivos (100 % de las referencias y de las predicciones ejecutables pasan el filtro).
- **Por qué:** si el filtro bloquea consultas legítimas, la seguridad le cuesta calidad al usuario y la EX medida en el servicio sería menor que la del modelo.
