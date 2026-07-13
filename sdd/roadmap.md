# Roadmap — ssb-validate

**Autor:** Pedro Sordo Martínez (amurlaniakea@gmail.com)
**Licencia:** AGPL-3.0-or-later
**Creado:** 2026-07-13

## Visión general
Capa de confianza ligera y honesta para cribado de electrolitos sólidos: valida estabilidad contra convex hull de Materials Project (ground truth verificado) y coherencia de conductividad contra benchmark público. Construcción local-first hasta ~90%, luego `gh repo create --source . --push` con aislamiento git.

## Fases / Releases

### Fase 1 — Constitución + Núcleo estabilidad
**Objetivo:** repo local, cliente MP, validación de estabilidad contra ground truth externo.

| Feature ID | Feature | Prioridad | Estimación | Estado |
|------------|---------|-----------|------------|--------|
| 001 | Cliente MP (`/materials/thermo/`, params `_limit`/`_fields`) + resolución de API key desde credentials/env | P0 | 2d | **done** |
| 002 | Regla estabilidad + AC-1, AC-2 (energy_above_hull, flag inestable) | P0 | 2d | **done** |
| 003 | CLI base `ssb-validate check` (AC-4 skeleton) + AC-5 (secret safety) | P1 | 1d | **done** |

### Fase 2 — Conductividad coherencia (gating: verificar dataset)
**Objetivo:** módulo de conductividad contra benchmark externo 2601.10997.

| Feature ID | Feature | Prioridad | Estimación | Estado |
|------------|---------|-----------|------------|--------|
| 004 | Verificar descarga dataset/pesos 2601.10997 (resolver URL primaria, no adivinar) | P0 | 1d | **done (descargado de Zenodo 10.5281/zenodo.17157647)** |
| 005 | Regla coherencia conductividad (AC-3, oráculo EXTERNO) | P0 | 3d | **done (oráculo GBR sobre dataset real; MAE holdout 1.464 log S/cm)** |

### Fase 3 — Empaquetado y despliegue (~90%)
**Objetivo:** LICENSE AGPL-3.0, README, RESEARCH.md, CI, GitHub con aislamiento.

| Feature ID | Feature | Prioridad | Estimación | Estado |
|------------|---------|-----------|------------|--------|
| 006 | Packaging (pyproject, LICENSE, README, RESEARCH.md) + CI lint→test→SonarCloud | P1 | 2d | **done** |
| 007 | `gh repo create --source . --push` con aislamiento git (orphan seed main + feature) | P2 | 0.5d | **done** |

### Fase 4 — CIF parsing (pendiente, cubre `--cif` stub)
**Objetivo:** parsear estructura CIF localmente y alimentar los validadores, en lugar de exigir `--material` o valores manuales.

**Estado actual:** `--cif` existe en la CLI pero es un **stub honesto** — el help lo marca "(Fase 3)" (ahora Fase 4) y, si se pasa sin `--material`, cae a `validate_stability(client, "")` (string vacío): no falla feo pero no hace nada útil. `pymatgen` (dependencia para parsear CIF) NO estaba en pyproject; se añadió como extra opcional `cif` en esta revisión.

| Feature ID | Feature | Prioridad | Estimación | Estado |
|------------|---------|-----------|------------|--------|
| 008 | `pymatgen` como extra opcional `cif` en pyproject | P2 | 0.5h | **done** |
| 009 | Módulo `cif_io.py`: parsear CIF → extraer composition, POAV, params de red, fracciones atómicas | P1 | 1d | pendiente |
| 010 | CLI `--cif` usa `cif_io` para poblar el oráculo de conductividad y derivar `material_id`/fórmula para MP | P1 | 1d | pendiente |
| 011 | Tests: CIF de fixture (ej. LLZO) → validación estabilidad + coherencia conductividad sin inputs manuales | P1 | 0.5d | pendiente |

**Alcance:** el parseo CIF alimenta los validadores ya existentes; NO añade predicción nueva. pymatgen es pesado → extra opcional, no en core.

## Dependencias entre features
- `002` depende de `001`.
- `005` depende de `004` (si dataset no accesible, AC-3 degrada a self-consistency documentada).
- `007` depende de `006` y de todo el código en local.

## Riesgos y mitigaciones
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| MP API cambia nombres de params (ya pasó: `limit`→`_limit`) | Media | Medio | Wrapper con reintentos + tests contra fixture local (no solo red) |
| Dataset 2601.10997 bloqueado (403) o URL no resoluble | Media | Alto | Fixture sintético controlado para self-consistency; oráculo externo solo si descarga real verificada (nunca URL adivinada) |
| Red sandbox flaky (WSL reinicia conexiones) | Alta | Medio | Tests de red tras `@pytest.mark.slow`; mock `http.server` local para fast suite |
| Falso-negativo de gap (competidores 0★ no maduros) | Baja | Bajo | Diferencial = mantenimiento + ground truth externo + honestidad de alcance |

---

*Documento vivo — actualizar al replanificar*
