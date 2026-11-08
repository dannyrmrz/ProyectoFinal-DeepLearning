**Registro y revisión de valoraciones**

Cada consulta recibe un identificador que permite relacionar el SQL generado con la valoración del usuario. Los eventos se conservan en JSONL y se descargan mediante `/api/registros`.

Los eventos de tipo `consulta` incluyen el identificador, la fecha, la pregunta, el SQL y el tiempo de respuesta. Los eventos de tipo `feedback` utilizan el mismo identificador e incluyen la valoración y un comentario opcional.

**Comprobación del registro**

La revisión relaciona cada evento `feedback` con su evento `consulta` mediante el identificador. Se contrastan las fechas, la pregunta y el voto. Se informa cualquier voto repetido y se conserva una sola valoración final por consulta al resumir una sesión.

El contador de votos resume valoraciones y no identifica personas distintas. Cuando se requiere distinguir participantes, se utilizan códigos anónimos verificados durante la sesión, sin publicar nombres, correos ni otros datos personales.
