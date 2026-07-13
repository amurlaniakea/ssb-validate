# RESEARCH.md — Fundamento y limitaciones de ssb-validate

**Autor:** Pedro Sordo Martínez (amurlaniakea@gmail.com)
**Licencia:** AGPL-3.0-or-later
**Fecha:** 2026-07-13

Este documento detalla la base científica, los oráculos utilizados y — de forma
explícita — las **limitaciones** del proyecto, para que cualquier usuario o
empresa evalúe el alcance real antes de confiar en la herramienta.

---

## 1. Qué valida ssb-validate

`ssb-validate` es un **validador de coherencia**, no un predictor. Toma un
candidato de electrolito sólido (estructura CIF o valores aportados por el
usuario / un modelo generativo) y valida dos cosas contra *ground truth*
independiente:

1. **Estabilidad termodinámica** — contra el convex hull de
   [Materials Project](https://materialsproject.org) vía `energy_above_hull`.
2. **Coherencia de conductividad iónica** — contra el benchmark público
   [arXiv 2601.10997](https://arxiv.org/abs/2601.10997)
   (Zenodo [10.5281/zenodo.17157647](https://doi.org/10.5281/zenodo.17157647)).

## 2. Estabilidad (oráculo externo verificado)

- Endpoint: Materials Project `/materials/thermo/` (el convex hull vive ahí, no en `/core/`).
- Verificación empírica (2026-07-13): para LLZO garnet `Li7La3Zr2O12`,
  `energy_above_hull = 0.0068 eV/átomo` (prácticamente en el convex hull → estable),
  `formation_energy_per_atom = -3.124 eV/átomo`.
- Criterio de inestabilidad: `energy_above_hull > 0.1 eV/átomo`.
- Validez: **EXTERNA** — el test `@pytest.mark.slow` consulta MP real y verifica
  que LLZO devuelve `E_above_hull ≈ 0` y `stability_flag = False`.

## 3. Conductividad (oráculo externo, capacidad limitada)

### 3.1 Dataset
El dataset se descargó de la fuente primaria citada por el propio paper
(Zenodo 10.5281/zenodo.17157647, sheet `all`, n = 499). Contiene:
`composition`, `log_target(S/cm)`, `POAV (cm³/g)`, parámetros de red `a/b/c`
y fracciones atómicas por elemento. NO se usó un fixture sintético de
contingencia porque el dataset real es automatizadamente descargable y parseable.

### 3.2 Oráculo implementado (MVP)
Se entrenó un `GradientBoostingRegressor` (sklearn, 300 árboles, prof. 3,
seed 42) sobre el dataset real usando descriptores **geométricos + composicionales**
(POAV, `a/b/c`, fracciones atómicas) → `log10(σ)`. El modelo se cachea en
`data/model_gbr.joblib` (artifact local, no commiteado; reproducible con `--force`).

**MAE del oráculo en holdout (medido, no del paper): 1.464 log(S/cm).**

El paper de los autores reporta MAE = 0.543 log(S/cm) con un GBR sobre
**más descriptors** + un GNN/LLM. Nuestro oráculo MVP es deliberadamente más
simple y, por tanto, más ruidoso.

### 3.3 Límite de coherencia y por qué es 4.0

El filtro `conductivity` compara la conductividad **aportada por el usuario**
con la predicción del oráculo y marca `conductivity_out_of_range = True` si

```
|σ_aportada − σ_oráculo| > UMBRAL_LOG_S_CM
```

`UMBRAL_LOG_S_CM = 4.0` (≈ 4 órdenes de magnitud).

**Justificación honesta del umbral:**

El oráculo MVP tiene MAE = 1.464. Si fijáramos el umbral en ~1–2 (cerca del
MAE), el filtro marcaría como "incoherente" la variación *normal* del propio
modelo, produciendo **falsos positivos sistemáticos** en materiales correctos.
Lo comprobamos en ejecución real: para Li10SiP2S12, cuyo valor real es
`log σ = −2.638`, el oráculo MVP predice `−5.775` (delta 3.1) — el valor real
salía incorrectamente marcado con umbral 2.0.

Por eso el umbral se fijó en **4.0**: solo señala diferencias MUCHO mayores al
MAE del oráculo. Consecuencia declarada:

> **El filtro de conductividad de ssb-validate es un DETECTOR DE DISPARATES
> (screening grueso), NO una validación fina.** Detecta valores absurdos
> (p.ej. afirmar σ = 10⁸ S/cm para una fase conocida), pero NO certifica que
> un valor modestamente distinto sea correcto.

Una validación fina requeriría el modelo de los autores (GNN/LLM entrenado
sobre el mismo dataset con sus descriptores completos) — fuera del alcance MVP.

## 4. Qué NO hace (out of scope)

- **No predice conductividad desde la estructura** (NEB/MD de barreras de migración).
- **No modela la interfaz Li/electrolito.** Es el subproblema más duro; no hay
  dataset público amplio ni heurística barata conocida (ver 2606.07772, MD
  ab-initio de interfaces específicas). Prometerlo sin método sería la trampa
  de "etiqueta-falsa de validación" que este proyecto evita por diseño.
- **No genera nuevos candidatos** (lo aporta el usuario / un MLIP externo).

## 5. Reproducibilidad

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m ssb_validate.train_conductivity   # descarga dataset, entrena, cachea
pytest -m slow                              # valida contra MP real + dataset 2601.10997
pytest                                      # fast suite (mocks, sin red)
```

La API key de Materials Project se resuelve desde `~/.hermes/credentials/platforms.json`
o la variable de entorno `MP_API_KEY`. **Nunca** está en el código ni en el repo.

## 6. Declaración de validez (anti-trampa SDD)

| AC | Tipo de validez | Qué demuestra |
|----|-----------------|---------------|
| AC-1/AC-2 | Externa (MP real) | El código consulta y respeta el convex hull de una DB independiente |
| AC-3 | Externa (dataset real 2601.10997) | El oráculo se entrena/evalúa en ground truth real; el holdout mide su capacidad predictiva (MAE 1.464), no "resuelve el problema" |
| AC-4 | Funcional | La CLI emite el reporte con los campos requeridos |
| AC-5 | Seguridad | La key no está en el binario ni se commitea |

Ningún test de "plomería" se presenta como validación física del dominio.
