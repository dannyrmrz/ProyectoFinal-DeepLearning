**1. Problemática**

En una farmacia, las preguntas sobre ventas y productos suelen requerir consultas a una base MySQL. Cuando la persona encargada no conoce SQL, depende de un analista para obtener esa información. Esta dependencia puede retrasar la revisión de ventas y la preparación de pedidos.

El usuario previsto es una persona encargada de compras o un analista junior que conoce el significado de las tablas, pero necesita apoyo para escribir consultas. El servicio recibe el esquema de la base y una pregunta en español. Devuelve una consulta de lectura que debe revisarse antes de ejecutarla en MySQL.

Un ejemplo es la pregunta «¿Cuántas unidades se han vendido de cada producto de la categoría Vitaminas?». La consulta debe relacionar `productos`, `categorias` y `detalle_venta`, filtrar la categoría y sumar las cantidades por producto. Con el resultado se puede priorizar la revisión de los productos con mayor demanda al preparar el siguiente pedido.

El esquema de ejemplo no incluye existencias, fechas de vencimiento ni niveles mínimos de inventario. Por ello, las ventas sirven como apoyo a la decisión de compra, pero no permiten determinar por sí solas qué productos deben reabastecerse ni en qué cantidad. Esa decisión requiere revisar también el inventario disponible.

El servicio genera SQL y no ejecuta consultas ni toma decisiones de compra. El beneficio esperado es facilitar la preparación de consultas, sujeto a su revisión y a la validación de uso.

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
