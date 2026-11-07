# Prompt compartido entre entrenamiento (Proyecto 3) e inferencia

SISTEMA = (
    "Eres un experto en MySQL 8.4. Dado el esquema de una base de datos y una pregunta en español, "
    "escribe una sola consulta SELECT (o WITH ... SELECT) que la responda. "
    "Usa solo tablas y columnas del esquema y respeta ONLY_FULL_GROUP_BY. "
    "Responde únicamente con la consulta SQL, sin explicaciones."
)


def mensajes(esquema, pregunta):
    return [
        {"role": "system", "content": SISTEMA},
        {"role": "user", "content": f"Esquema:\n{esquema}\n\nPregunta: {pregunta}"},
    ]


def mensaje_correccion(sql, error):
    return f"La consulta\n{sql}\nfalló con el error: {error}\nCorrígela y responde solo con la consulta SQL."
