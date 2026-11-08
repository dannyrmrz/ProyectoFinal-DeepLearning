**Preguntas frecuentes sobre el servicio**

**1. ¿Qué necesidad atiende el modelo?**

Se facilita la escritura de consultas MySQL a partir de preguntas en español. El usuario previsto conoce el significado de sus datos, pero necesita apoyo para escribir SQL. En la farmacia, una consulta de unidades vendidas por producto puede apoyar la revisión de compras. El esquema no contiene existencias, por lo que no permite calcular por sí solo el reabastecimiento.

**2. ¿Por qué se utiliza el adapter B?**

En la validación del Proyecto 3 obtuvo una EX ponderada de 0.646 frente a 0.439 del modelo base. En el servicio en CPU obtuvo 0.585 frente a 0.439. La mejora en CPU es de 0.146 y cumple el umbral de 0.10 registrado para H1. La selección se apoya en esos resultados y no implica que todas las consultas sean correctas.

**3. ¿Qué significa EX ponderada y cómo se distingue de la cantidad de aciertos?**

EX mide si la consulta generada devuelve el resultado de referencia al ejecutarse en MySQL. Se asigna peso 1 a preguntas fáciles, 2 a medias y 3 a difíciles. El adapter acertó 25 de 40 preguntas y obtuvo una EX ponderada de 0.585. Ese valor no equivale al porcentaje simple de preguntas correctas, porque las difíciles pesan más.

**4. ¿Qué limitaciones tiene la validación?**

Se utilizaron 40 preguntas sobre dos esquemas. El conjunto permite una comparación directa con la base, pero es pequeño y no representa todos los dominios de uso. Además, el commit de hipótesis es posterior al cierre registrado de la corrida base. No se puede acreditar un registro previo en Git con la evidencia disponible. Estas limitaciones se conservan en el informe.

**5. ¿Por qué no se utiliza int8 para responder más rápido?**

La variante int8 redujo la latencia p50 de 27.03 a 8.59 segundos, pero su EX ponderada cayó de 0.585 a 0.000. La variante parcial obtuvo 0.463 y tampoco conservó la calidad requerida. Se rechazó H2 y se mantiene fp32. La memoria estable observada también fue mayor en las variantes int8.

**6. ¿Por qué se sirve en CPU y qué pasa con solicitudes simultáneas?**

Se utiliza una PC disponible para operar el modelo sin depender de una GPU dedicada. En la validación secuencial, el adapter B presentó p50 de 27.03 segundos y p95 de 42.79 segundos medidos por el servicio. Un candado permite una sola generación a la vez. En la carga con dos solicitudes en curso, el tiempo del cliente presentó p50 de 50.838 segundos y p95 de 61.596 segundos.

**7. ¿El servicio ejecuta SQL o modifica la base del usuario?**

El servicio devuelve texto SQL y no se conecta a la base del usuario. Se aplica un filtro que detecta patrones de escritura y varias sentencias. La revisión de patrones no garantiza seguridad completa ni exactitud. Antes de ejecutar la respuesta se revisa su contenido y se utiliza una cuenta con permisos de lectura.

**8. ¿Qué información queda registrada?**

Se conservan fecha, identificador, pregunta, SQL generado, tiempo y resultado del filtro. Los votos incluyen el identificador de consulta, la valoración y un comentario opcional. El esquema completo no se guarda, pero sí su longitud. Las preguntas, consultas y comentarios pueden contener datos sensibles. Por ello, se emplea información de demostración y se revisa cualquier registro antes de compartirlo.

**9. ¿Cómo se relacionan las consultas y sus valoraciones?**

Cada respuesta recibe un identificador que se utiliza al enviar una valoración a `POST /api/feedback`. El mismo identificador aparece en los eventos de consulta y feedback, lo que permite relacionarlos. El contador de votos no identifica personas y puede incluir votos repetidos sobre una consulta.

**10. ¿Qué resultados se obtuvieron en las pruebas públicas?**

Se completaron tres consultas de humo y 20 solicitudes de carga por una URL pública, con el modelo real y sin errores de API. Todas las respuestas fueron de lectura. En la carga, seis respuestas superaron los 60 segundos. La sesión dejó 23 consultas automáticas y cero votos en los registros del servicio.

**Referencias**

*Resultados y limitaciones en [modelo_y_validacion.md](modelo_y_validacion.md). Criterios en [hipotesis.md](hipotesis.md). Cifras en [resumen.csv](../evaluacion/resultados/resumen.csv). Procedimiento de evidencia en [evidencias/README.md](../evidencias/README.md).*
