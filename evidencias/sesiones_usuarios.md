**Registro de sesiones con usuarios externos**

Estado al 7 de noviembre de 2026. No se han acreditado sesiones en este registro. La tabla prepara la recopilación y no representa participantes ni votos obtenidos.

Se completa una fila por persona ajena al equipo durante una sesión real. Los códigos anónimos permiten distinguir participantes sin publicar nombres, correos u otros datos personales. El responsable de la sesión comprueba que cada código corresponda a una persona distinta.

| Código reservado | Fecha y hora UTC−06:00 | Pregunta de ejemplo | Identificador de respuesta | Voto registrado | Observación |
|---|---|---|---|---|---|
| U01 | Pendiente | Pendiente | Pendiente | Pendiente | Sin sesión acreditada |
| U02 | Pendiente | Pendiente | Pendiente | Pendiente | Sin sesión acreditada |
| U03 | Pendiente | Pendiente | Pendiente | Pendiente | Sin sesión acreditada |
| U04 | Pendiente | Pendiente | Pendiente | Pendiente | Sin sesión acreditada |
| U05 | Pendiente | Pendiente | Pendiente | Pendiente | Sin sesión acreditada |

**Datos de la sesión**

| Dato | Valor |
|---|---|
| URL pública utilizada | Pendiente de confirmar |
| Commit servido | Pendiente de registrar |
| Inicio y fin de la sesión | Pendiente de registrar |
| Responsable de la verificación | Pendiente de registrar |
| Personas distintas verificadas | 0 acreditadas en este documento |
| Archivo de métricas | Pendiente de descarga |
| Archivo de registros | Pendiente de descarga |

**Comprobación del registro**

Por cada fila completada se localiza el evento `consulta` con el identificador indicado y un evento `feedback` para ese mismo identificador. Se contrasta la fecha, la pregunta y el voto con la sesión observada. Se informa cualquier voto repetido y se conserva una sola valoración final por consulta al resumir la sesión.

Si una persona realiza varias preguntas, se conserva el mismo código y se agregan sus consultas como filas adicionales. El número de personas se calcula con códigos distintos verificados, no con solicitudes ni votos acumulados.
