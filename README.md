# Text-to-SQL en producción

Servicio que recibe el esquema de una base MySQL 8.4 y una pregunta en español, y devuelve la consulta `SELECT` que la responde.

Modelo: `Qwen/Qwen2.5-Coder-1.5B-Instruct` con el adapter LoRA del Proyecto 3 (`modelo/adapter/`).

## Estructura

```
servicio/      modelo, API (FastAPI), página web, registro de uso
modelo/        adapter LoRA del Proyecto 3
tests/         pruebas de la API con modelo simulado
scripts/       publicación con Cloudflare Tunnel
docs/          secciones del documento técnico
```

Arquitectura, API e instrucciones de ejecución: [docs/arquitectura.md](docs/arquitectura.md).

Modelo y validación (secciones 4 y 5): [docs/modelo_y_validacion.md](docs/modelo_y_validacion.md).
Evaluación reproducible y resultados CPU: [evaluacion/README.md](evaluacion/README.md).
