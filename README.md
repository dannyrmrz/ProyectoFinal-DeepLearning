**Text-to-SQL para MySQL**

Servicio que recibe un esquema MySQL 8.4 y una pregunta en español, y devuelve una consulta de lectura. Utiliza `Qwen/Qwen2.5-Coder-1.5B-Instruct` con el adapter LoRA B del Proyecto 3. La consulta se revisa y se ejecuta fuera del servicio.

Acceso local al iniciar el servidor: [http://127.0.0.1:7860](http://127.0.0.1:7860).


**1. Problemática**

Una persona encargada de compras de una farmacia puede conocer los productos y sus ventas sin dominar SQL. Para consultar la base MySQL depende de un analista, lo que puede retrasar la preparación de reportes y pedidos.

El servicio ayuda a transformar esa necesidad en una consulta. Por ejemplo, ante «¿Cuántas unidades se han vendido de cada producto de la categoría Vitaminas?», debe relacionar productos, categorías y detalles de venta, y sumar las cantidades por producto. El resultado permite priorizar la revisión de productos con mayor demanda al preparar una compra.


Desarrollo del problema, usuario y decisión: [docs/contexto.md](docs/contexto.md).

**2. Planificación**

El trabajo se organiza en cuatro fases para un equipo de tres integrantes. Las fechas son estimadas y orientan el avance hasta la entrega del 9 de noviembre de 2026.

**Fase 1. Planificación y selección del proyecto**

Del 3 al 4 de noviembre se prevé revisar los proyectos anteriores, seleccionar el modelo que se llevará al servicio y definir el problema, el usuario y el alcance. Los tres integrantes participan en la selección y en la organización inicial.

**Fase 2. División de tareas**

El 5 de noviembre se distribuyen las responsabilidades y se acuerdan los archivos y resultados que debe aportar cada integrante. La ejecución se divide en tres áreas.

- Servicio y despliegue, a cargo de un integrante. Incluye la API, la interfaz, el registro de uso y la publicación con Cloudflare Tunnel.
- Modelo y validación, a cargo de un integrante. Incluye la preparación del modelo, las hipótesis, la comparación con la línea base y el análisis de resultados.
- Contexto y evidencias, a cargo de un integrante. Incluye el problema, los supuestos, la documentación, las preguntas de ejemplo y la recopilación de pruebas de uso.

**Fase 3. Ejecución de las partes individuales**

Del 6 al 7 de noviembre se desarrolla cada área y se revisa el avance entre los tres integrantes. Se prepara el modelo, se implementa el servicio y se redacta la documentación. También se integran los archivos para que la interfaz, la API y la evaluación utilicen la misma configuración.

**Fase 4. Comprobación y pruebas**

Del 8 al 9 de noviembre se prevé comprobar el funcionamiento local y público, ejecutar las pruebas de humo y carga, revisar la comparación con la línea base y recopilar el uso por personas externas. Los tres integrantes revisan los resultados, corrigen los problemas encontrados y verifican la entrega final.

Se reserva del 10 al 15 de noviembre un periodo de ajustes posteriores a la revisión. El estado real de las pruebas se presenta en la sección de evidencias.

Detalle de la planificación: [docs/contexto.md](docs/contexto.md).

**3. Supuestos**

- Se proporciona un esquema MySQL 8.4 con relaciones y comentarios `COMMENT` cuando estén disponibles. Las preguntas se redactan en español y se refieren a información incluida en el esquema.
- Se espera una consulta `SELECT` o `WITH ... SELECT`. La API admite esquemas de 10 a 20 000 caracteres y preguntas de 3 a 500 caracteres.
- El usuario conoce el significado de los datos, revisa el SQL y lo ejecuta fuera del servicio con permisos de lectura.
- La PC con CPU, la conexión a Internet y el túnel permanecen activos durante horarios acordados. La generación se atiende de una en una.
- El objetivo es recibir una respuesta en menos de 60 segundos. Debe comprobarse desde el cliente público y bajo carga.
- No se envían credenciales, información de pacientes ni datos confidenciales. El registro conserva preguntas, SQL y comentarios, por lo que también requiere revisión antes de compartirse.
- El filtro de lectura no garantiza que la consulta sea correcta ni sustituye los permisos de la base de datos.

Detalle de datos, usuario y entorno: [supuestos](docs/contexto.md).

**4. Modelo planteado**

Se reutiliza el modelo Text-to-SQL del Proyecto 3. La base `Qwen/Qwen2.5-Coder-1.5B-Instruct` se adapta mediante LoRA sobre atención y MLP, con rango 16, alfa 32 y dropout 0.05. El adapter B contiene aproximadamente 18.46 millones de parámetros entrenables y se conserva en [modelo/adapter/](modelo/adapter/).

El entrenamiento de origen utilizó 8 058 pares de esquema, pregunta y SQL procedentes de Spider traducido y esquemas propios. La validación usa 40 preguntas sobre farmacia y venta de boletos, con esquemas que no formaron parte del entrenamiento descrito.

Para el servicio, el adapter se fusiona al cargar el modelo y la inferencia se realiza en CPU con fp32. Se conserva el prompt de MySQL 8.4 y la generación determinista, con un máximo de 256 tokens nuevos. El servicio no se conecta a la base del usuario ni aplica autocorrección mediante ejecución de SQL.

La configuración elegida es `USAR_ADAPTER=1` y `CUANTIZAR=0`. Las variantes int8 se conservan para reproducir los experimentos.

Descripción del entrenamiento, selección del adapter y cambios del servicio: [docs/modelo_y_validacion.md](docs/modelo_y_validacion.md).

**5. Validación de hipótesis**

Se enviaron 40 preguntas por la API real de forma secuencial y se compararon los resultados SQL con consultas de referencia en MySQL 8.4.10. El acierto por ejecución ponderado, EX, asigna pesos 1, 2 y 3 a preguntas fáciles, medias y difíciles. La línea base es el mismo modelo sin adapter.

| Configuración | EX ponderada | Correctas | Latencia p50 | Latencia p95 | Memoria estable |
|---|---|---|---|---|---|
| Base sin adapter | 0.439 | 22 de 40 | 28.15 s | 41.63 s | 6.27 GB |
| Adapter B en fp32 | 0.585 | 25 de 40 | 27.03 s | 42.79 s | 6.31 GB |
| Adapter B con int8 | 0.000 | 0 de 40 | 8.59 s | 49.91 s | 8.91 GB |
| Adapter B con int8 parcial | 0.463 | 23 de 40 | 16.53 s | 28.84 s | 8.08 GB |

Fuente: [evaluacion/resultados/resumen.csv](evaluacion/resultados/resumen.csv). Las latencias corresponden al campo `segundos` de la API y no incluyen todo el recorrido del cliente público. La variante parcial fue una exploración posterior.

| Hipótesis | Criterio | Resultado | Veredicto reportado |
|---|---|---|---|
| H1, mejora de calidad con LoRA | Aumento de EX de al menos 0.10 frente a la base | Aumento de 0.146 | Se acepta |
| H2, int8 reduce latencia sin perder calidad | p50 de hasta 0.70 veces la de fp32 y pérdida de EX de hasta 0.03 | p50 de 0.32 veces y pérdida de EX de 0.585 | Se rechaza |
| H3, el filtro no bloquea consultas válidas | Cero falsos positivos en el conjunto evaluado | Pasan las 40 referencias y no se bloquean las 160 predicciones | Se acepta |

Los resultados respaldan el uso del adapter B en fp32 frente a las alternativas medidas. El conjunto es pequeño y la exactitud no es perfecta. H3 comprueba bloqueos en este conjunto, no una garantía general de seguridad. Las mediciones con solicitudes simultáneas se presentan en la sección de evidencias.

Método, análisis y comparación con T4: [validación completa](docs/modelo_y_validacion.md). Criterios conservados: [docs/hipotesis.md](docs/hipotesis.md). Reproducción: [evaluacion/README.md](evaluacion/README.md).

**6. Herramientas y arquitectura**

El usuario abre una página HTML publicada mediante Cloudflare Tunnel. La página envía el esquema y la pregunta a FastAPI y recibe un identificador de tarea. Se consulta su estado mediante peticiones breves hasta obtener el SQL. Así se evita mantener abierta una conexión durante toda la espera cuando coinciden varios usuarios. Se aplica el filtro de lectura y la consulta y el voto se registran en JSONL para calcular las métricas.

| Componente | Función |
|---|---|
| PyTorch, Transformers y PEFT | Cargar el modelo, fusionar el adapter y generar SQL en CPU |
| FastAPI y uvicorn | Servir la API y la interfaz web desde el mismo proceso |
| Cloudflare Tunnel | Dar acceso HTTPS a la instancia local durante la sesión |
| Filtro `es_solo_lectura` | Detectar patrones de escritura y salidas con varias sentencias |
| JSONL y métricas | Conservar solicitudes, errores, tiempos y votos |
| Dockerfile | Preparar una alternativa de ejecución con Python 3.11 y modelo base descargado |

| Método | Ruta | Uso |
|---|---|---|
| GET | `/` | Interfaz web |
| GET | `/api/ejemplo` | Esquema de farmacia |
| POST | `/api/sql` | Recibir `esquema` y `pregunta`, devolver `id`, `sql`, `solo_lectura` y `segundos` |
| POST | `/api/tareas` | Recibir el esquema y la pregunta de la interfaz, devolver un identificador con HTTP 202 |
| GET | `/api/tareas/{id}` | Consultar el estado de la tarea y recuperar su respuesta al terminar |
| POST | `/api/feedback` | Registrar `id`, `correcto` y un `comentario` opcional |
| GET | `/api/salud` | Consultar carga y configuración del modelo |
| GET | `/api/metricas` | Consultar solicitudes, errores, latencias, bloqueos y votos acumulados |
| GET | `/api/registros` | Descargar los eventos de uso en JSONL |

Diagrama y decisiones de implementación: [docs/arquitectura.md](docs/arquitectura.md).

**7. Evidencias**

| Evidencia | Estado |
|---|---|
| Validación del modelo por API en CPU | Disponible en [evaluacion/resultados/](evaluacion/resultados/) |
| Esquema y cinco preguntas de uso | Disponibles en [preguntas_ejemplo.md](evidencias/preguntas_ejemplo.md) |
| Pruebas locales con las dependencias fijadas | 34 aprobadas. Registro en [verificacion_local.txt](evidencias/verificacion_local.txt) |
| Prueba de humo con tres preguntas por la URL pública | Aprobada, tres respuestas HTTP 200 y consultas de lectura. Detalle en [prueba_humo.txt](evidencias/prueba_humo.txt) |
| Carga ligera de 20 solicitudes, dos a la vez | Completada sin errores ni bloqueos. Detalle en [resumen_carga.md](evidencias/resumen_carga.md) y [prueba_carga.csv](evidencias/prueba_carga.csv) |
| Descarga de salud, métricas y registros públicos | Disponible en [evidencias/](evidencias/), con `listo` en verdadero, 23 solicitudes, cero errores y cero votos |

El método y los archivos de respaldo están en [evidencias/README.md](evidencias/README.md). Las mediciones de esta sección corresponden a solicitudes automáticas por la API.

Las tres respuestas de humo llegaron en 23.193, 27.847 y 33.844 segundos desde el cliente. En la carga, la latencia p50 fue de 50.838 segundos y la p95 fue de 61.596 segundos. Seis de las 20 respuestas superaron el objetivo de menos de 60 segundos.

Se utilizó el modelo con el adapter B en fp32 y `PRECARGAR=1`. La sesión registró 23 consultas automáticas de lectura y ningún voto. Estas pruebas acreditan funcionamiento público y generación de SQL. El entorno y el cierre de los procesos quedaron registrados en [entorno.json](evidencias/entorno.json) y [sesion_publica.json](evidencias/sesion_publica.json).

**Instrucciones de ejecución local**

Desde la raíz del repositorio, en PowerShell, se crea el entorno y se instalan las dependencias. La descarga del modelo requiere Internet, espacio en disco y memoria suficiente para el modelo y el sistema operativo. La corrida registrada utilizó alrededor de 6.31 GB de memoria estable para el servicio con adapter.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
$env:HF_HOME = Join-Path (Get-Location) 'registros/cache_hf'
$env:USAR_ADAPTER = '1'
$env:CUANTIZAR = '0'
.\.venv\Scripts\python.exe -m uvicorn servicio.api:app --host 127.0.0.1 --port 7860
```

Se abre [http://127.0.0.1:7860](http://127.0.0.1:7860). En `/api/salud`, `listo` debe cambiar a verdadero al terminar la carga. La primera ejecución descarga los pesos y puede tardar más. La caché local queda en `registros/cache_hf`, lo que permite reutilizar los pesos en los siguientes arranques.

Para publicar con el script existente, `cloudflared` debe estar instalado y disponible en `PATH`. Se detiene primero cualquier servidor que ocupe el puerto 7860. El script inicia su propia instancia de uvicorn y mantiene el túnel hasta que se interrumpe la ejecución.

```powershell
$env:HF_HOME = Join-Path (Get-Location) 'registros/cache_hf'
.\scripts\publicar.ps1
```

La dirección HTTPS que imprime Cloudflare se utiliza para acceder a la interfaz y a la API durante esa sesión. Como alternativa, con el servidor local ya iniciado, se abre otra terminal y se ejecuta el túnel directamente.

```powershell
cloudflared tunnel --no-autoupdate --url http://127.0.0.1:7860
```

En el entorno local preparado también se encuentra el ejecutable en `.venv/Scripts/cloudflared.exe`. Se puede utilizar esa ruta completa en lugar de `cloudflared`. El entorno virtual y el ejecutable no se distribuyen en Git.

**Ejecución con Docker**

```powershell
docker build -t texto-sql .
New-Item -ItemType Directory -Force registros | Out-Null
docker run --rm -p 127.0.0.1:7860:7860 --mount "type=bind,source=$PWD\registros,target=/home/user/app/registros" -e USAR_ADAPTER=1 -e CUANTIZAR=0 texto-sql
```

La construcción descarga el modelo base. El volumen conserva `uso.jsonl` al detener el contenedor. La interfaz queda en la misma dirección local y puede publicarse con el comando de túnel anterior.

| Variable | Uso |
|---|---|
| `USAR_ADAPTER` | `1` utiliza LoRA y `0` utiliza la línea base |
| `CUANTIZAR` | `0` conserva fp32. `1` y `parcial` se reservan para experimentos |
| `ADAPTER` | Cambia la ruta del adapter, por defecto `modelo/adapter` |
| `DIR_REGISTROS` | Cambia el directorio de `uso.jsonl` |
| `PRECARGAR` | `1` carga el modelo al iniciar y `0` espera hasta la primera generación |

**Uso y verificación**

Se conserva el esquema de farmacia al abrir la página, se escribe una pregunta en español y se selecciona Generar SQL. La respuesta debe revisarse antes de ejecutarse en MySQL. Los botones Me sirvió y No me sirvió registran la utilidad percibida.

Las pruebas existentes se ejecutan con el siguiente comando. 

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Se encuentran diez respuestas sobre el alcance y los resultados en [docs/preguntas_frecuentes.md](docs/preguntas_frecuentes.md).

**Estructura del repositorio**

```text
servicio/      modelo, API, interfaz web y registro de uso
modelo/        adapter LoRA del Proyecto 3
evaluacion/    datos, evaluación reproducible y resultados
tests/         pruebas de API y evaluación
scripts/       publicación con Cloudflare Tunnel
docs/          contexto, modelo, hipótesis y arquitectura
evidencias/    preguntas, seguimiento de sesiones y pruebas de operación
```

**Declaración de uso de IA**

Se utilizaron asistentes de IA para resolver preguntas conceptuales sobre LoRA y despliegue, orientar la organización del trabajo y apoyar la generación y revisión de algunas partes del código y de la documentación.El uso de estas herramientas no sustituye la validación de las consultas ni la revisión de la entrega.
