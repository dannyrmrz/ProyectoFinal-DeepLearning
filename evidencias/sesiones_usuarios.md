**Registro y revisión de valoraciones**

Cada consulta recibe un identificador que permite relacionar el SQL generado con la valoración del usuario. Los eventos se conservan en JSONL y se descargan mediante `/api/registros`.

Los eventos de tipo `consulta` incluyen el identificador, la fecha, la pregunta, el SQL y el tiempo de respuesta. Los eventos de tipo `feedback` utilizan el mismo identificador e incluyen la valoración y un comentario opcional.

**Comprobación del registro**

La revisión relaciona cada evento `feedback` con su evento `consulta` mediante el identificador. Se contrastan las fechas, la pregunta y el voto. Se informa cualquier voto repetido y se conserva una sola valoración final por consulta al resumir una sesión.

El contador de votos resume valoraciones y no identifica personas distintas. Cuando se requiere distinguir participantes, se utilizan códigos anónimos verificados durante la sesión, sin publicar nombres, correos ni otros datos personales.

**Sesión del 8 de noviembre de 2026**

Se registraron cinco valoraciones positivas sobre cinco consultas distintas. La coordinación de la sesión confirmó que correspondían a cinco personas diferentes ajenas al equipo. Se asignaron los códigos U01 a U05 según el orden de las valoraciones guardadas, sin incorporar datos personales.

La sesión utilizó la URL `https://miller-committee-firmware-shortly.trycloudflare.com` y el modelo con adapter B en fp32. El servidor y el túnel se detuvieron a las 16:01:52, hora de Guatemala, UTC−06:00.

| Código | Hora del voto UTC−06:00 | Identificador de consulta | Pregunta utilizada | Valoración |
|---|---|---|---|---|
| U01 | 15:54:57 | `0bad9629ee6b` | ¿Qué sucursal vendió más en total durante 2025? | Me sirvió |
| U02 | 15:55:03 | `84b2055527a4` | ¿Qué sucursal vendió más en total durante 2025? | Me sirvió |
| U03 | 15:56:10 | `a38333fb5ddc` | ¿Qué empleados ganan más que el promedio de su sucursal? | Me sirvió |
| U04 | 15:57:23 | `1dfd8d33d265` | ¿Cuántos productos requieren receta médica? | Me sirvió |
| U05 | 15:58:20 | `8c930b32289c` | ¿Cuál es el precio promedio de los productos por categoría? | Me sirvió |

**Métricas de la sesión**

| Medida | Resultado |
|---|---|
| Participantes externos confirmados | 5 |
| Consultas registradas | 11 |
| Consultas de diagnóstico automático | 2 |
| Otras consultas de interacción durante la sesión | 9 |
| Votos registrados | 5 |
| Consultas distintas con voto | 5 |
| Votos positivos | 5 |
| Votos negativos | 0 |
| Errores de generación registrados | 0 |
| Tasa de solo lectura | 1.0 |
| Latencia p50 del servicio | 72.57 segundos |
| Latencia p95 del servicio | 156.15 segundos |

Las métricas agrupan toda la sesión, incluidos los primeros intentos con conexiones interrumpidas y las consultas posteriores al ajuste de la interfaz. El contador de errores corresponde a la generación registrada y no resume las interrupciones de conexión del navegador.

Las consultas de diagnóstico tienen los identificadores `cc0b7f57b51f` y `57e8ef1ef0e0`. No recibieron votos y no se contabilizaron como participantes. Cada valoración de la tabla se relacionó con su consulta en los registros descargados y no se encontraron votos repetidos sobre un mismo identificador.

**Interpretación de las valoraciones**

Los votos representan utilidad percibida y no equivalen al acierto por ejecución en MySQL. Por ejemplo, la respuesta de U04 utiliza `requires_receta`, mientras que el esquema contiene `requiere_receta`. Las respuestas de U01 y U02 usan `detalle_venta` en el cálculo sin incluir esa tabla entre las tablas consultadas. Se conservaron las consultas y las valoraciones tal como fueron registradas. El 100 % de votos positivos no se interpreta como 100 % de consultas técnicamente correctas.

**Archivos de respaldo**

- [participantes.csv](uso_usuarios_20261108/participantes.csv), códigos, preguntas, identificadores y valoraciones.
- [metricas_inicio.json](uso_usuarios_20261108/metricas_inicio.json), contador inicial con cero consultas y cero votos.
- [metricas.json](uso_usuarios_20261108/metricas.json), métricas finales de la sesión.
- [registros.jsonl](uso_usuarios_20261108/registros.jsonl), once consultas y cinco eventos de valoración.
- [salud.json](uso_usuarios_20261108/salud.json), configuración del modelo antes del cierre.
- [sesion.json](uso_usuarios_20261108/sesion.json), dirección utilizada, consultas de diagnóstico, confirmación de participantes y hora de cierre.
