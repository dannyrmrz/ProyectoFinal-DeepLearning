**1. Problemática**

En una farmacia, las preguntas sobre ventas y productos suelen requerir consultas a una base MySQL. Cuando la persona encargada no conoce SQL, depende de un analista para obtener esa información. Esta dependencia puede retrasar la revisión de ventas y la preparación de pedidos.

El usuario previsto es una persona encargada de compras o un analista junior que conoce el significado de las tablas, pero necesita apoyo para escribir consultas. El servicio recibe el esquema de la base y una pregunta en español. Devuelve una consulta de lectura que debe revisarse antes de ejecutarla en MySQL.

Un ejemplo es la pregunta «¿Cuántas unidades se han vendido de cada producto de la categoría Vitaminas?». La consulta debe relacionar `productos`, `categorias` y `detalle_venta`, filtrar la categoría y sumar las cantidades por producto. Con el resultado se puede priorizar la revisión de los productos con mayor demanda al preparar el siguiente pedido.

El esquema de ejemplo no incluye existencias, fechas de vencimiento ni niveles mínimos de inventario. Por ello, las ventas sirven como apoyo a la decisión de compra, pero no permiten determinar por sí solas qué productos deben reabastecerse ni en qué cantidad. Esa decisión requiere revisar también el inventario disponible.

El servicio genera SQL y no ejecuta consultas ni toma decisiones de compra. Tampoco se ha medido una reducción del tiempo de trabajo del usuario. El beneficio esperado es facilitar la preparación de consultas, sujeto a su revisión y a la validación de uso.

**2. Planificación**

Las fechas de las etapas terminadas se tomaron del historial de Git, con hora de Guatemala, UTC−06:00. Las actividades futuras se identifican como programadas y no representan resultados obtenidos.

| Etapa | Fecha | Responsable | Evidencia y estado |
|---|---|---|---|
| Incorporación del modelo, inferencia y registro de uso | 7 de noviembre de 2026, 10:55 a 10:59 | Responsable del servicio | Commits `73416a9`, `e5c83e3`, `1131634` y `badbe8b`. Implementación registrada |
| Pruebas de API y alternativa con Docker | 7 de noviembre de 2026, 10:59 a 11:02 | Responsable del servicio | Commits `832a920` y `acc3264`. Pruebas y Dockerfile incorporados |
| Interfaz web y publicación por túnel | 7 de noviembre de 2026, 14:54 a 14:55 | Responsable del despliegue | Commits `89f200d`, `89d1253` y `48c1b85`. Publicación configurada, pendiente de comprobar la URL activa |
| Registro de hipótesis | 7 de noviembre de 2026, 16:52 | Responsable del modelo y la validación | Commit `7fd7062`. La fecha del commit es posterior al cierre registrado de la corrida base |
| Evaluación en CPU y comparación con T4 | 7 de noviembre de 2026, 18:19 a 18:30 | Responsable del modelo y la validación | Commits `5656043`, `0a2271f`, `9ce0766` y `b71503f`. Resultados conservados en `evaluacion/resultados/` |
| Contexto, guía de uso e integración del informe | 7 de noviembre de 2026 | Responsable del contexto y las evidencias | Documentación incorporada en `docs/`, `evidencias/` y `README.md`. Fecha verificable en los commits de estos archivos |
| Prueba de humo y carga ligera por la URL pública | 8 de noviembre de 2026 | Responsable de las evidencias, con apoyo del despliegue | Programada. Requiere el servicio activo y la dirección vigente |
| Uso por al menos cinco personas externas y descarga de registros | 8 de noviembre de 2026 | Responsable de las evidencias | Programado. Requiere participación real y votos de los usuarios |
| Revisión final de la entrega | 9 de noviembre de 2026 | Equipo del proyecto | Programada. Se deben revisar los resultados y los pendientes antes de la exposición |
| Cierre de ajustes | 15 de noviembre de 2026, 23:59 | Equipo del proyecto | Fecha prevista para completar los ajustes de la entrega |

La implementación del túnel y las mediciones de validación no acreditan por sí solas el uso del servicio por personas externas. La prueba de humo, la carga y las sesiones de usuarios requieren evidencias propias.

**3. Supuestos**

**Datos**

- Se recibe un esquema compatible con MySQL 8.4, con nombres de tablas, columnas, relaciones y comentarios `COMMENT` cuando estén disponibles.
- Las preguntas se redactan en español y describen información que existe en el esquema proporcionado.
- Se espera una sola consulta `SELECT` o `WITH ... SELECT`, destinada a lectura.
- El esquema no supera 20 000 caracteres y la pregunta no supera 500 caracteres. La API también exige al menos 10 caracteres en el esquema y 3 en la pregunta.
- Se utilizan esquemas y preguntas de demostración. No se envían credenciales, datos personales, información de pacientes ni información confidencial del negocio.

**Usuario**

- Se conoce el significado del esquema y el resultado que se necesita, aunque no se domine SQL.
- Se revisan las tablas, columnas, filtros y operaciones de la consulta antes de ejecutarla. Cuando se requiera, se solicita una revisión técnica.
- La ejecución se realiza fuera del servicio, con una cuenta de MySQL que tenga permisos de lectura.
- Se registra un voto según la utilidad de la respuesta. Que la API responda sin errores no demuestra que la consulta responda correctamente la pregunta.

**Entorno**

- El modelo se sirve desde una PC con CPU y acceso a Internet. La configuración elegida utiliza el adapter B en fp32, con `USAR_ADAPTER=1` y `CUANTIZAR=0`.
- El acceso público depende de Cloudflare Tunnel. La PC y el proceso deben permanecer encendidos durante los horarios acordados, y la dirección cambia al reiniciar el túnel temporal.
- Se considera aceptable una respuesta en menos de 60 segundos desde el envío hasta la recepción. Este objetivo debe comprobarse por la URL pública y bajo carga, pues los resultados existentes corresponden a solicitudes secuenciales.
- La generación se atiende de una en una. Con dos solicitudes simultáneas puede aumentar el tiempo de espera.
- El servicio registra preguntas, consultas y votos. Aunque no guarda el esquema completo, estos campos también pueden contener información sensible y deben revisarse antes de compartir los registros.
- El filtro de lectura revisa patrones del texto generado. No sustituye la revisión de la consulta ni los permisos de lectura en la base de datos.
