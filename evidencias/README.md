**7. Evidencias del servicio**

La evidencia disponible permite revisar la implementación y la validación del modelo. Todavía no se acredita el pase a producción mediante uso por personas externas. Las mediciones existentes se obtuvieron con solicitudes secuenciales y no sustituyen la prueba de carga con dos solicitudes simultáneas.

**Estado de las evidencias**

| Evidencia | Ubicación | Estado |
|---|---|---|
| Contexto, planificación y supuestos | [docs/contexto.md](../docs/contexto.md) | Disponible |
| Resultados de calidad y latencia en CPU | [resumen.csv](../evaluacion/resultados/resumen.csv) y [validación](../docs/modelo_y_validacion.md) | Disponibles, con la limitación de cronología documentada |
| Cinco preguntas para usuarios | [preguntas_ejemplo.md](preguntas_ejemplo.md) | Disponibles y vinculadas a las referencias existentes |
| Verificación local del repositorio | `verificacion_local.txt` | Se registra por separado de las pruebas del servicio público |
| Prueba de humo por la URL pública | `prueba_humo.txt` | Pendiente de una URL activa y del modelo listo |
| Carga ligera de 20 solicitudes, dos a la vez | `prueba_carga.csv` y `resumen_carga.md` | Pendiente de ejecución contra el servicio |
| Participación externa | [sesiones_usuarios.md](sesiones_usuarios.md) | Registro preparado, sin sesiones acreditadas |
| Estado del modelo publicado | `salud.json` | Pendiente de descarga durante la sesión pública |
| Métricas y registro de uso | `metricas_antes.json`, `metricas.json` y `registros.jsonl` | Pendientes de descarga durante la sesión pública |
| Capturas de funcionamiento e historial | `capturas/` | Pendientes de incorporación |

Los nombres de archivos pendientes indican dónde conservar los resultados cuando se obtengan. Su presencia en esta tabla no acredita una prueba realizada.

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

**Uso externo**

Se solicita la participación de al menos cinco personas ajenas al equipo. Cada una utiliza la URL real con una pregunta de ejemplo y registra un voto sobre su respuesta. Se anota la sesión en [sesiones_usuarios.md](sesiones_usuarios.md) con un código anónimo y el identificador devuelto por la API.

El registro actual no identifica personas y permite más de un voto por consulta. Por ello, cinco votos no demuestran cinco participantes distintos. La cantidad de personas se acredita con el registro de sesiones y los identificadores se contrastan con los eventos `consulta` y `feedback` descargados del servicio. Las llamadas automáticas no se registran como sesiones de personas.

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

**Criterio de cierre**

La evidencia de uso queda completa cuando se conserva la prueba de humo, el detalle y resumen de carga, las cinco sesiones externas con sus votos y las descargas del servicio. La recomendación operativa se revisa con esos resultados. Hasta entonces, se recomienda mantener únicamente una prueba piloto supervisada, con adapter B en fp32, revisión de SQL y horarios de disponibilidad definidos.
