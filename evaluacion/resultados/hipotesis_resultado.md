# Resultado de las hipótesis

Generado por `python -m evaluacion.resumir`. Criterios en `docs/hipotesis.md`.

- **H1** EX(adapter B) − EX(base) = 0.585 − 0.439 = **+0.146** (criterio ≥ +0.10) → **se acepta**
- **H2** p50 int8 / p50 fp32 = 8.59 / 27.03 = **0.32** (criterio ≤ 0.70); ΔEX = **-0.585** (criterio ≥ −0.03) → **se rechaza**
- *Exploración posterior (no registrada antes de medir)* int8 sin `down_proj`: p50 16.53 / 27.03 = **0.61**; ΔEX = **-0.122** → con los criterios de H2 tampoco cumpliría
- **H3** referencias que pasan el filtro: **40/40**; predicciones bloqueadas en todas las configuraciones: **0** → **se acepta**
