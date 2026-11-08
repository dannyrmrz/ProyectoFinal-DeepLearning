**7. Evidencias del servicio**

La evidencia disponible incluye la validación del modelo, la prueba de humo y la carga ligera por la URL pública. Se conservan por separado las mediciones de validación secuencial y las de carga con dos solicitudes simultáneas.

**Estado de las evidencias**

| Evidencia | Ubicación | Estado |
|---|---|---|
| Contexto, planificación y supuestos | [docs/contexto.md](../docs/contexto.md) | Disponible |
| Resultados de calidad y latencia en CPU | [resumen.csv](../evaluacion/resultados/resumen.csv) y [validación](../docs/modelo_y_validacion.md) | Disponibles, con la limitación de cronología documentada |
| Cinco preguntas para usuarios | [preguntas_ejemplo.md](preguntas_ejemplo.md) | Disponibles y vinculadas a las referencias existentes |
| Verificación local del repositorio | [verificacion_local.txt](verificacion_local.txt) | 32 pruebas aprobadas con las versiones fijadas. Python 3.13.2 |
| Prueba de humo por la URL pública | [prueba_humo.txt](prueba_humo.txt) y [humo_resultados.json](humo_resultados.json) | Aprobada. Tres consultas completadas con HTTP 200 y SQL de lectura |
| Carga ligera de 20 solicitudes, dos a la vez | [prueba_carga.csv](prueba_carga.csv) y [resumen_carga.md](resumen_carga.md) | Completada. Cero errores, cero bloqueos y seis respuestas de 60 segundos o más |
| Estado del modelo durante la comprobación | [salud.json](salud.json) | Descargado de la URL pública, con `listo` en verdadero, adapter activo y fp32 |
| Métricas y registro de la comprobación | [metricas_antes.json](metricas_antes.json), [metricas.json](metricas.json) y [registros.jsonl](registros.jsonl) | Descargados. 23 solicitudes, cero errores y cero votos |
| Entorno de la sesión | [entorno.json](entorno.json) | Configuración registrada con el modelo cargado y cuatro hilos de CPU |
| Endpoints públicos y cierre de la sesión | [sesion_publica.json](sesion_publica.json) | Cinco rutas con HTTP 200. Servidor y túnel detenidos al finalizar |

**Comprobación del 7 de noviembre de 2026**

Se levantaron FastAPI, el modelo con adapter B en fp32 y un túnel temporal de Cloudflare. La interfaz, el esquema de ejemplo, salud, métricas y registros respondieron con HTTP 200 por la URL pública. Se utilizó `PRECARGAR=1` y el estado de salud confirmó que el modelo estaba listo antes de enviar consultas.

La prueba de humo completó sus tres consultas en 23.193, 27.847 y 33.844 segundos desde el cliente. La carga completó 20 solicitudes con dos en curso a la vez, sin errores ni bloqueos. Se obtuvo p50 de 50.838 segundos y p95 de 61.596 segundos. Seis respuestas superaron el objetivo de menos de 60 segundos.

Se descargaron 23 eventos de consulta y las métricas finales, con cero votos. El servidor y el túnel se detuvieron a las 23:10:20, UTC−06:00. La URL se conserva como referencia de esta sesión y no se mantiene activa.

**Preparación de la sesión**

Se registra la fecha y hora con zona UTC−06:00, la dirección pública exacta, el commit servido y la configuración del modelo. Se comprueba `/api/salud` antes de enviar consultas. Debe mostrar `listo` en verdadero, `usar_adapter` en verdadero y `cuantizar` en `"0"` para la configuración elegida.

Se descarga una copia de `/api/metricas` antes de cada bloque de pruebas y se separan los bloques de humo, carga y usuarios mediante sus horarios e identificadores de respuesta. Los contadores del servicio acumulan solicitudes de distintos orígenes y no deben atribuirse completos a personas externas.

**Prueba de humo**

Se consulta `/api/salud` y se envían de forma secuencial las preguntas 1, 3 y 4 de [preguntas_ejemplo.md](preguntas_ejemplo.md), con el esquema de farmacia. Cada envío utiliza `POST /api/sql` y un objeto JSON con los campos `esquema` y `pregunta`.

En `prueba_humo.txt` se conservan la URL, la fecha, el estado de salud, las tres preguntas, sus identificadores, el código HTTP, el SQL y el tiempo observado. Se aprueba cada caso solo si la API responde con HTTP 200, `solo_lectura` en verdadero y una consulta no vacía que comience con `SELECT` o `WITH` y supere la revisión de lectura. Se informan los errores sin sustituirlos por respuestas de ejemplo.

La prueba de humo comprueba disponibilidad y formato. No demuestra que el resultado SQL sea correcto. Si el modelo no está listo, la prueba se deja como no ejecutada o fallida y se conserva el motivo.

**Carga ligera**

Se envían 20 solicitudes con el esquema de farmacia y las cinco preguntas de ejemplo repetidas cuatro veces. Se mantienen dos solicitudes en curso como máximo. Al terminar una, se envía la siguiente hasta completar las 20. El modelo serializa la generación, por lo que parte de la latencia puede corresponder a espera.

Se mide el tiempo completo desde el envío hasta la recepción, además del campo `segundos` devuelto por la API. Se utiliza un tiempo límite de 180 segundos para observar demoras, pero una respuesta de 60 segundos o más incumple el objetivo de uso. Una demora no se excluye de los resultados.

El CSV debe contener una fila por solicitud y estas columnas.

```text
numero,inicio,fin,pregunta,id,http,segundos_cliente,segundos_servicio,solo_lectura,error
```

Se incluyen las solicitudes fallidas y se describe el error. Una respuesta bloqueada se informa por separado de un error de conexión o HTTP.

En `resumen_carga.md` se reportan solicitudes enviadas, completadas, errores, bloqueos, respuestas de 60 segundos o más y latencias p50 y p95 del cliente. Para los percentiles se ordenan los tiempos de respuestas completadas y se toma la posición redondeada hacia arriba de 0.50 o 0.95 por el número de respuestas. Con 20 respuestas, corresponden a las posiciones 10 y 19. Se indica cuántas observaciones entraron al cálculo. Los tiempos hasta un fallo se conservan en el CSV y se informan aparte, sin contarlos como respuestas exitosas.

El método del resumen de carga se identifica de forma explícita porque `/api/metricas` usa su propia regla de percentiles y reúne todas las consultas del registro. No se espera que ambos resúmenes coincidan si difieren el conjunto o el método.

**Registro de valoraciones**

La API recibe valoraciones mediante `POST /api/feedback`, con el identificador de la consulta, el campo `correcto` y un comentario opcional. El registro permite relacionar la consulta generada con su valoración. El método de revisión se describe en [sesiones_usuarios.md](sesiones_usuarios.md).

El registro no identifica personas y permite más de un voto por consulta. Los votos acumulados representan eventos de valoración y no una cantidad de usuarios distintos. Los identificadores permiten contrastar los eventos `consulta` y `feedback` descargados del servicio.

**Descarga y revisión de registros**

Con la URL activa, los siguientes comandos se ejecutan desde la raíz del repositorio. Se reemplaza el valor de `$url` por la dirección exacta del túnel vigente.

```powershell
$url = 'https://DIRECCION-VIGENTE.trycloudflare.com'
curl.exe --fail --silent --show-error "$url/api/salud" --output evidencias/salud.json
curl.exe --fail --silent --show-error "$url/api/metricas" --output evidencias/metricas_antes.json
```

La copia inicial de métricas se obtiene antes de la sesión. Al terminar las pruebas y los votos se descargan los archivos finales.

```powershell
curl.exe --fail --silent --show-error "$url/api/metricas" --output evidencias/metricas.json
curl.exe --fail --silent --show-error "$url/api/registros" --output evidencias/registros.jsonl
```

Antes de incorporar archivos a Git, se revisan preguntas, SQL y comentarios para retirar cualquier dato sensible. Toda eliminación de contenido se describe en el informe para conservar el alcance de la evidencia. Se informa el intervalo de la sesión y cualquier tráfico ajeno que afecte los contadores.
