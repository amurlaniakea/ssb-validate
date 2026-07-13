# ssb-validate

Validador de **coherencia** para electrolitos sólidos (solid-state electrolytes, SSE).

> No predice propiedades desde cero. Toma un candidato (estructura CIF o valores aportados)
> y valida su coherencia contra:
> 1. **Estabilidad termodinámica** — convex hull de [Materials Project](https://materialsproject.org)
>    (`energy_above_hull`). Verificado: LLZO garnet `Li7La3Zr2O12` → `E_above_hull` = 0.0068 eV/átomo.
> 2. **Conductividad iónica** — benchmark público arXiv 2601.10997 (n=499, MAE=0.543 log(S/cm)).

## Por qué
El descubrimiento de electrolitos sólidos tiene modelos generativos maduros pero falta una
**capa de confianza reutilizable** que las empresas necesitan para decidir qué sintetizar.
La interfaz Li/electrolito (el problema más duro) queda **fuera de alcance** — no hay dataset
público ni heurística barata conocida.

## Estado
Fase 2 completa: validación de estabilidad (MP) + filtro de coherencia de conductividad (oráculo 2601.10997).

## Investigación y limitaciones
Lee **[RESEARCH.md](RESEARCH.md)** para la base científica, los oráculos y — de forma
explícita — las **limitaciones**: el filtro de conductividad es un *detector de
disparates* (umbral 4.0 log(S/cm) ≈ 4 órdenes de magnitud), NO una validación fina.

## Licencia
AGPL-3.0-or-later — Pedro Sordo Martínez (amurlaniakea@gmail.com)
