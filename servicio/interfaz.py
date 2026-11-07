import gradio as gr

PREGUNTAS = [
    "¿Cuántos productos requieren receta médica?",
    "¿Cuál es el precio promedio de los productos por categoría?",
    "¿Qué sucursal vendió más en total durante 2025?",
    "¿Qué empleados ganan más que el promedio de su sucursal?",
]


def crear_interfaz(consultar, votar, esquema_ejemplo):
    def generar(esquema, pregunta):
        if not esquema.strip() or not pregunta.strip():
            raise gr.Error("Escribe el esquema y la pregunta.")
        r = consultar(esquema, pregunta)
        if not r["solo_lectura"]:
            return "", "⚠️ La consulta generada no era de solo lectura y se bloqueó.", r["id"]
        return r["sql"], f"Generada en {r['segundos']} s · id `{r['id']}`", r["id"]

    def calificar(id_, correcto):
        if not id_:
            raise gr.Error("Primero genera una consulta.")
        votar(id_, correcto)
        return "Gracias, registramos tu respuesta."

    with gr.Blocks(title="Text-to-SQL") as demo:
        gr.Markdown(
            "# Text-to-SQL para MySQL\n"
            "Pega el esquema de tu base (`SHOW CREATE TABLE`) y escribe la pregunta en español. "
            "El modelo devuelve una consulta `SELECT`: revísala antes de ejecutarla."
        )
        id_ = gr.State("")
        with gr.Row():
            esquema = gr.Textbox(esquema_ejemplo, label="Esquema", lines=20, max_lines=30)
            with gr.Column():
                pregunta = gr.Textbox(label="Pregunta", placeholder="¿Cuántos productos hay por categoría?")
                gr.Examples(PREGUNTAS, inputs=pregunta)
                boton = gr.Button("Generar SQL", variant="primary")
                sql = gr.Code(label="Consulta", language="sql")
                estado = gr.Markdown()
                with gr.Row():
                    bien = gr.Button("👍 Me sirvió")
                    mal = gr.Button("👎 No me sirvió")

        boton.click(generar, [esquema, pregunta], [sql, estado, id_])
        bien.click(lambda i: calificar(i, True), id_, estado)
        mal.click(lambda i: calificar(i, False), id_, estado)
    return demo
