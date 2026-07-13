# Spec — ssb-validate (CORE)

**Autor:** Pedro Sordo Martínez (amurlaniakea@gmail.com)
**Licencia:** AGPL-3.0-or-later
**Creado:** 2026-07-13

## Qué hace
Valida la coherencia de un candidato de electrolito sólido contra (1) estabilidad termodinámica vía el convex hull de Materials Project y (2) conductividad iónica vía el benchmark público arXiv 2601.10997. Emite un reporte estructurado (JSON + humano) con flags de coherencia. NO predice propiedades desde cero.

## Contexto / Motivación
El frente de baterías sólidas tiene modelos generativos maduros (materials_discovery, MLIPs) pero falta una capa de validación reutilizable y mantenida. El `total_count=0` por frase "screening tool" era falso-negativo (hallados 4 competidores 0★). El gap real es **herramienta mantenida con ground truth externo**, no inexistencia. La estabilidad termodinámica es abordable vía MP (verificado: LLZO `energy_above_hull`=0.0068 eV/átomo, HTTP 200 con key). La conductividad requiere el benchmark 2601.10997 (n=499, MAE=0.543 log(S/cm)). La interfaz Li/SE no tiene dataset público → fuera de alcance.

## Criterios de aceptación (AC)

| ID | Criterio | Cómo se verifica | Tipo de validez |
|----|----------|------------------|-----------------|
| AC-1 | Dado `material_id` o fórmula, la herramienta consulta MP `/materials/thermo/` y devuelve `energy_above_hull` y `formation_energy_per_atom`. | Test contra MP real (`@pytest.mark.slow`) + fixture local con valor conocido LLZO=0.0068 eV/átomo (medido 2026-07-13). | **Externa** (ground truth de DB independiente) |
| AC-2 | Materiales con `energy_above_hull` > 0.1 eV/átomo se marcan `thermodynamically_unstable=true`. | Fixture inestable (E_above_hull alto) → assert flag; fixture benigno LLZO → assert NO flag. | **Externa** (fixture con ground truth conocido) |
| AC-3 | Dado candidato con descriptores (POAV, params de red) + conductividad aportada, la herramienta la marca `conductivity_out_of_range` si difiere > umbral de la predicción del modelo benchmark 2601.10997. El oráculo debe ser el **modelo de los autores** (externo), no reimplementación de la misma regla. | Requiere dataset/pesos 2601.10997 accesibles. Si NO descargable → AC-3 queda como **self-consistency** documentada (no PAS externo) hasta obtener oráculo externo. Nunca marcar PASS externo sin ello. | Externa (dataset real descargado de Zenodo 10.5281/zenodo.17157647) |
| AC-4 | CLI `ssb-validate check` acepta `--material <id>` y `--cif <file>` y emite reporte estructurado (JSON + humano) con campos `energy_above_hull`, `stability_flag`, `conductivity_flag`. | Test con Typer CliRunner; assert salida JSON con campos requeridos y valores coherentes con fixture. | Funcional |
| AC-5 | API key se resuelve desde credentials store o env `MP_API_KEY`; el binario no contiene el literal de la key ni se commitea. | Test que lee de env var; `grep -rn "<literal_key>" src/` debe ser vacío en CI. | Seguridad |

## Casos de uso / User Stories
- **Como** investigador de baterías **quiero** validar la estabilidad de un candidato contra el convex hull de MP **para** descartar sintetizar fase inestable.
- **Como** ingeniero de materials informatics **quiero** chequear que la conductividad aportada por mi MLIP es coherente con los descriptores del candidato **para** no priorizar un valor irreal.

## Reglas de negocio / Edge cases
| Escenario | Comportamiento esperado |
|-----------|-------------------------|
| MP devuelve 401/403/timeout | Error explícito, NUNCA valor inventado ni silenciado |
| Conductividad sin oráculo externo disponible | Herramienta LO DECLARA y omite `conductivity_flag`, no lo silencia |
| `--cif` sin `--material` | Se parsea CIF localmente (pymatgen, Fase 2); si no hay pymatgen, error claro |
| `energy_above_hull` ≈ 0 (estable) | `stability_flag=false` |

## API / Interfaces
### CLI
| Comando | Argumentos | Salida | Códigos |
|--------|------|---------|---------|
| `ssb-validate check` | `--material <id>` O `--cif <path>` | reporte JSON + humano | 0 ok, 1 error validación, 2 error red/API |

### Contratos de datos
```json
{
  "material_id": "string | null",
  "formula": "string",
  "energy_above_hull_ev_per_atom": "float",
  "formation_energy_per_atom": "float",
  "stability_flag": "boolean",
  "conductivity_value_log_s_cm": "float | null",
  "conductivity_out_of_range": "boolean | null",
  "notes": "string"
}
```

## No funcionales
- **Performance:** < 2s por candidato (excl. red MP).
- **Seguridad:** API key jamás en código/repo; validación de input (paths, fórmulas).
- **Resiliencia red:** rate-limit MP ≤ 1 req/3s, backoff ante 429; tests de red tras `@pytest.mark.slow`, mock local para fast suite.

## Dependencias
- Requiere: MP API key (en credentials store), benchmark 2601.10997 (verificar descarga en Fase 2).
- Bloquea: nada por ahora.

---

*Documento vivo — actualizar antes de cualquier cambio importante en la feature*
