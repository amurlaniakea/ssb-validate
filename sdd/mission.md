# Mission — ssb-validate

**Autor:** Pedro Sordo Martínez (amurlaniakea@gmail.com)
**Licencia:** AGPL-3.0-or-later
**Creado:** 2026-07-13

## Qué construimos
`ssb-validate` es un **validador de coherencia** para electrolitos sólidos (solid-state electrolytes, SSE) destinado a priorizar síntesis experimental. NO predice propiedades desde cero: toma un candidato (estructura CIF o valores aportados por el usuario / un modelo generativo tipo MLIP) y valida su coherencia contra (a) el convex hull termodinámico de Materials Project y (b) un benchmark público de conductividad iónica.

## Para quién
- **Usuario principal:** investigadores de baterías sólidas en empresas (CATL, Tesla, QuantumScape, Toyota, Samsung SDI) y grupos académicos; ingenieros de materials informatics.
- **Stakeholders:** equipos de descubrimiento de materiales que necesitan filtrar candidatos antes de síntesis costosa.

## Problema que resuelve
El descubrimiento de electrolitos sólidos sufre de: modelos generativos que producen candidatos sin validación de estabilidad/transporte; falta de una **capa de confianza reutilizable** que las empresas necesitan para decidir qué sintetizar. Predecir conductividad/interfaz de verdad requiere simulación cara (NEB/MD de barreras de migración). Este proyecto aporta la capa de validación ligera y honesta, no otro modelo.

## Valor diferencial
- Se apoya en ground truth **INDEPENDIENTE** (Materials Project convex hull) verificado empíricamente el 2026-07-13 (LLZO `energy_above_hull` = 0.0068 eV/átomo).
- Declara **explícitamente fuera de alcance** la interfaz Li/electrolito (sin dataset público ni heurística barata conocida) — evita la trampa de etiqueta-falsa de prometer validación que no se sostiene.
- Frente a los 4 competidores 0★ hallados (imml, AI-SSE-Coating-Screening, electrolyte_optimizer, AI-Based-SSB-Predictor): apuesta por mantenimiento, tests con ground truth externo y honestidad de alcance, no por otro notebook académico.

## Métricas de éxito (KPIs)
| Métrica | Target | Cómo se mide |
|---------|--------|--------------|
| Latencia de validación por candidato | < 2s (excl. red MP) | benchmark local |
| Cobertura de sistemas garnet/LLZO testeados que devuelven `energy_above_hull` | 100% | AC-1 |
| Falsos "estable" no detectados en fixtures de control | 0 | AC-2 |

## Fuera de alcance (Out of scope)
- Predicción de conductividad iónica desde estructura (NEB/MD).
- Modelado de interfaz Li/electrolito.
- Generación de nuevos candidatos (lo aporta el usuario / MLIP externo).

---

*Documento vivo — actualizar cuando cambie la visión del proyecto*
