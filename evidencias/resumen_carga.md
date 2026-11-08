**Resultado de la prueba de carga ligera**

Se enviaron 20 solicitudes al modelo real mediante la URL pública, con dos solicitudes en curso como máximo. Se utilizó el adapter B en fp32 y el esquema de farmacia. Las cinco preguntas de ejemplo se repitieron cuatro veces.

**Datos de la sesión**

| Dato | Valor |
|---|---|
| Fecha | 7 de noviembre de 2026 |
| Inicio | 23:01:01.893, UTC−06:00 |
| Fin | 23:09:55.151, UTC−06:00 |
| URL | https://willing-thriller-supply-feet.trycloudflare.com |
| Configuración | `USAR_ADAPTER=1`, `CUANTIZAR=0`, `PRECARGAR=1` |
| Hilos de CPU configurados | 4 |
| Solicitudes simultáneas | 2 |
| Tiempo límite por solicitud | 180 segundos |
| Duración total medida | 533.257 segundos |

**Resultados**

| Medida | Resultado |
|---|---|
| Solicitudes enviadas | 20 |
| Respuestas HTTP 200 | 20 |
| Errores de conexión o de API | 0 |
| Respuestas bloqueadas | 0 |
| Respuestas de solo lectura | 20 de 20 |
| Latencia p50 del cliente | 50.838 segundos |
| Latencia p95 del cliente | 61.596 segundos |
| Latencia máxima del cliente | 61.768 segundos |
| Respuestas en menos de 60 segundos | 14 de 20 |
| Respuestas de 60 segundos o más | 6 de 20 |

Los tiempos del cliente incluyen el recorrido por el túnel y la espera hasta recibir la respuesta completa. El servicio atiende una generación a la vez. La prueba mantuvo dos solicitudes en curso, por lo que el tiempo observado también incluye la espera para generar.

Los percentiles se calcularon sobre las 20 respuestas completadas. Se ordenaron los tiempos del cliente y se tomaron las posiciones 10 y 19 para p50 y p95, respectivamente. Se utilizó la regla de redondear la posición hacia arriba, sin interpolación.

La disponibilidad se mantuvo durante las 20 solicitudes y no se observaron errores ni bloqueos. El objetivo de responder en menos de 60 segundos se cumplió en 14 consultas y se superó en seis. Estos resultados describen esta sesión y no garantizan el mismo tiempo para cualquier pregunta o nivel de carga.

**Relación con las métricas del servicio**

Antes de la carga se registraban tres consultas de la prueba de humo. Al finalizar se registraron 23 solicitudes, cero errores, una tasa de solo lectura de 1.0 y cero votos. Las 20 consultas de carga se distinguen mediante sus identificadores.

El endpoint de métricas reportó p50 de 49.43 segundos y p95 de 61.26 segundos. Esos valores corresponden a las 23 consultas y al tiempo medido por la API. El resumen de carga utiliza las 20 solicitudes de esta prueba, el tiempo del cliente y la regla de percentiles indicada arriba.

Las llamadas se realizaron de forma automática y no acreditan participación de personas externas. Tampoco se ejecutó el SQL en MySQL durante esta prueba. La comprobación de lectura no mide acierto por ejecución.

**Archivos de respaldo**

- [prueba_carga.csv](prueba_carga.csv), detalle por solicitud.
- [carga_respuestas.jsonl](carga_respuestas.jsonl), respuestas completas con el SQL generado.
- [carga_resumen.json](carga_resumen.json), medidas de la sesión.
- [metricas_antes_carga.json](metricas_antes_carga.json), estado previo a las 20 solicitudes.
- [metricas.json](metricas.json) y [registros.jsonl](registros.jsonl), estado y eventos al finalizar.
- [entorno.json](entorno.json), configuración del equipo y del modelo.
- [sesion_publica.json](sesion_publica.json), comprobación de endpoints y hora de cierre.

El servidor y el túnel se detuvieron a las 23:10:20, UTC−06:00. La URL corresponde a esta sesión y no se mantiene activa.
