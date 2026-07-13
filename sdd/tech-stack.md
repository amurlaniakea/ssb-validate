# Tech Stack — ssb-validate

**Autor:** Pedro Sordo Martínez (amurlaniakea@gmail.com)
**Licencia:** AGPL-3.0-or-later
**Creado:** 2026-07-13

## Stack principal
| Capa | Tecnología | Versión | Justificación |
|------|------------|---------|---------------|
| Lenguaje | Python | 3.11+ | Ecosistema materials science (pymatgen, mp-api), tipado estricto |
| CLI | Typer | 0.12+ | Subcomandos; **NOTA pitfall SDD:** requiere `@app.callback()` para enrutar `check` |
| HTTP client | httpx | 0.27+ | Async, reintentos, respeto rate-limit MP |
| Validación datos | pydantic | v2 | Contratos de entrada/salida (única fuente de verdad) |
| Testing | pytest + pytest-cov | 8.x | Cobertura medida (nunca afirmar % sin `pytest --cov` real) |
| Lint/Format | ruff + black | latest | Velocidad y consistencia |
| CI/CD | GitHub Actions | - | lint → test → SonarCloud (en fase ~90%) |

## Convenciones de código
- **Estilo:** PEP 8
- **Naming:** `snake_case` funciones/vars, `PascalCase` clases, `run_*` para funciones ejecutables internas (evita colisión con `test_*` de pytest)
- **Commits:** Conventional Commits
- **Branching:** trunk-based (feature branch → main en push final)

## Arquitectura
- **Patrón:** Modular monolith — capa cliente (MP) + reglas de validación + CLI
- **Estructura carpetas:**
  ```
  src/ssb_validate/
  ├── mp_client.py      # cliente Materials Project (thermo endpoint)
  ├── stability.py       # regla energy_above_hull
  ├── conductivity.py    # regla coherencia contra benchmark 2601.10997
  ├── models.py          # contratos pydantic (única fuente de verdad)
  └── cli.py             # Typer entrypoint
  tests/
  ├── test_stability.py
  ├── test_conductivity.py
  └── test_cli.py
  ```

## Dependencias clave
| Paquete | Propósito | Licencia |
|---------|-----------|----------|
| httpx | Llamadas MP API | MIT |
| pydantic | Contratos de datos | MIT |
| typer | CLI | MIT |
| pytest / pytest-cov | Testing | MIT |
| pymatgen | Parseo CIF local (Fase 2, opcional) | BSD-3 |

## Infraestructura
- **Hosting:** ninguno hasta ~90% (local-first por preferencia del usuario)
- **Secrets:** leer de `~/.hermes/credentials/platforms.json` → `materials_project.api_key` O variable de entorno `MP_API_KEY`. **NUNCA hardcodear** en código ni repo.
- **Observabilidad:** logging a stderr, JSON estructurado en salida.

---

*Documento vivo — actualizar al cambiar stack o convenciones*
