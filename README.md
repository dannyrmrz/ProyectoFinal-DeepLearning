# Text-to-SQL en producción

Servicio que recibe el esquema de una base MySQL 8.4 y una pregunta en español, y devuelve la consulta `SELECT` que la responde.

Modelo: `Qwen/Qwen2.5-Coder-1.5B-Instruct` con el adapter LoRA del Proyecto 3 (`modelo/adapter/`).
