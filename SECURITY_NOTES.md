# Security Notes — ssb-validate

## Incidente de API key de Materials Project (2026-07-13)

- **Key expuesta en historial público entre 2026-07-13 13:34:01 +0200 (commit inicial) y 2026-07-13 15:24:14 +0200 (purge).**
- **Purgada del historial pero NO rotada, por decisión del autor.** Riesgo conocido y asumido.
- Mitigación posterior: `tests/test_security.py` ya no hardcodea la key (la lee del credentials store local y grepea el repo completo); `gitleaks` añadido a CI.
- Ver también: nota de incidente en la documentación del proyecto (Obsidian `ssb-validate.md`).
