**Preguntas de ejemplo para la farmacia**

Se utiliza el esquema de [servicio/ejemplo_farmacia.sql](../servicio/ejemplo_farmacia.sql), disponible también en `/api/ejemplo` y cargado al abrir la interfaz. Contiene siete tablas y no incluye registros de clientes o pacientes. La base de demostración con datos se conserva en [evaluacion/datos/farmacia.sql](../evaluacion/datos/farmacia.sql).

Las preguntas se tomaron de [evaluacion/datos/preguntas.json](../evaluacion/datos/preguntas.json). Sirven para orientar el uso y permitir una revisión con referencias existentes. No forman un conjunto nuevo ni independiente de evaluación.

| Número | Pregunta para copiar | Referencia | Resultado que se debe revisar |
|---|---|---|---|
| 1 | Lista el nombre y el precio de los productos que cuestan más de 100 quetzales, ordenados del más caro al más barato. | Pregunta 2 de la validación | Nombre y precio, filtro mayor que 100 y orden descendente por precio |
| 2 | Muestra el nombre y la ciudad de las sucursales que abrieron de 2019 en adelante. | Pregunta 4 de la validación | Nombre y ciudad, con fecha de apertura desde el 1 de enero de 2019 |
| 3 | ¿Cuántos productos hay en cada categoría? Devuelve el nombre de la categoría y la cantidad de productos. | Pregunta 7 de la validación | Relación entre categorías y productos, con un conteo por categoría |
| 4 | ¿Cuántas unidades se han vendido de cada producto de la categoría Vitaminas? Devuelve el nombre del producto y las unidades. | Pregunta 10 de la validación | Filtro de la categoría Vitaminas y suma de cantidades por producto |
| 5 | ¿Qué productos nunca se han vendido? Devuelve el nombre del producto. | Pregunta 14 de la validación | Productos sin coincidencias en el detalle de ventas |

**Uso**

1. Abrir la dirección pública vigente durante el horario de prueba.
2. Conservar el esquema de ejemplo y copiar una de las preguntas completas.
3. Seleccionar Generar SQL y esperar la respuesta.
4. Revisar que las tablas, columnas, filtros y operaciones correspondan a la pregunta. Si se necesita comprobar el resultado, ejecutar la consulta fuera del servicio sobre la base de demostración y con permisos de lectura.
5. Seleccionar Me sirvió o No me sirvió según la utilidad de la respuesta. Un resultado bloqueado o incorrecto debe recibir una valoración negativa.
6. Comunicar al responsable de la sesión el identificador de la respuesta y la pregunta utilizada, sin enviar datos personales.

**Alcance de la revisión**

Una consulta que comienza con `SELECT` puede contener una columna inexistente o calcular un resultado incorrecto. El voto refleja utilidad percibida. El acierto por ejecución se comprueba aparte con las consultas de referencia y MySQL.

Para la prueba de humo se utilizan las preguntas 1, 3 y 4 de esta guía. Para la carga ligera se repiten las cinco preguntas en cuatro rondas, hasta completar 20 solicitudes.
