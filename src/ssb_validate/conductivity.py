# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Filtro de coherencia de conductividad ionica (Fase 2, AC-3).

Oráculo EXTERNO: se entrena un GBR ligero sobre el dataset publico del paper
arXiv 2601.10997 (Zenodo 10.5281/zenodo.17157647, sheet 'all', n=499) usando
descriptores geometricos + composicionales (POAV, parametros de red, fracciones
atomicas) -> log10(sigma en S/cm). El modelo se cachea en data/model_gbr.joblib
(generado por train_conductivity.py, seed fijo, reproducible).

El filtro 'conductivity' compara la conductividad APORTADA por el usuario con la
prediccion del oráculo y flaguea si |delta| > UMBRAL_LOG.

NOTA DE VALIDEZ (SDD anti-trampa): el holdout es del MISMO dataset (es la unica
fuente de ground truth disponible). Evaluar el oráculo en ese holdout mide su
CAPACIDAD PREDICTIVA (MAE real, no el del paper), no que "resuelva el problema".
El valor real del filtro es sobre candidatos del USUARIO fuera del dataset. Se
documenta explicitamente para no confundir un test de plomería con validez fisica.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from .models import ConductivityResult

# Umbral de incoherencia: > 4.0 log(S/cm) ~ 4 ordenes de magnitud de diferencia.
# El oráculo MVP (GBR sobre POAV+red+composicion) tiene MAE holdout medido 1.464
# log(S/cm) sobre 2601.10997, asi que solo diferencias MUCHO mayores al MAE son
# significativas. El filtro es un DETECTOR DE DISPARATES (screening grueso), NO una
# validacion fina: un oráculo fino requeriria el GNN/LLM de los autores (fuera de MVP).
UMBRAL_LOG_S_CM = 4.0

_DATASET_XLSX = Path(__file__).resolve().parents[2] / "data" / "raw" / "all_cif_data.xlsx"
_MODEL_CACHE = Path(__file__).resolve().parents[2] / "data" / "model_gbr.joblib"

# Fuente primaria del dataset (paper arXiv 2601.10997, cita explícita en el PDF):
# Zenodo 10.5281/zenodo.17157647, archivo all_cif_data.xlsx (sheet 'all', n=499).
_ZENODO_XLSX = "https://zenodo.org/records/17157647/files/all_cif_data.xlsx"

_ELEMENT_COLS = [
    "Ag","Al","B","Ba","Bi","Br","C","Ca","Ce","Cl","Co","Cr","Cu","Er","F",
    "Fe","Ga","Gd","Ge","H","Hf","I","In","K","La","Li","Lu","Mg","Mn","Mo","N",
    "Na","Nb","Nd","Ni","O","P","Pb","Pr","S","Sb","Sc","Se","Si","Sm","Sn",
    "Sr","Ta","Te","Ti","V","W","Y","Zn","Zr",
]
_GEOM_COLS = ["POAV (cm3/g)", "a", "b", "c"]


def _ensure_dataset() -> None:
    """Descarga el dataset de Zenodo (fuente primaria) si no esta en data/raw/.

    Reproducible y automatico: el slow-suite de CI no commitea el binario, asi
    que lo baja en caliente. Nunca se usa un fixture sintetico.
    """
    if _DATASET_XLSX.is_file():
        return
    _DATASET_XLSX.parent.mkdir(parents=True, exist_ok=True)
    import urllib.request

    req = urllib.request.Request(
        _ZENODO_XLSX, headers={"User-Agent": "Mozilla/5.0 (research ssb-validate)"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        _DATASET_XLSX.write_bytes(r.read())



def _load_dataset() -> pd.DataFrame:
    _ensure_dataset()
    if not _DATASET_XLSX.is_file():
        raise FileNotFoundError(
            f"Dataset no encontrado tras descarga: {_DATASET_XLSX}."
        )
    df = pd.read_excel(_DATASET_XLSX, sheet_name="all")
    needed = ["log_target(S/cm)"] + _GEOM_COLS + _ELEMENT_COLS
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset no tiene columnas esperadas: {missing}")
    return df.dropna(subset=["log_target(S/cm)"])


def feature_cols() -> list[str]:
    return _GEOM_COLS + _ELEMENT_COLS


def train_oracle(force: bool = False):
    """Entrena y cachea el GBR. Devuelve (modelo, mae_holdout)."""
    if _MODEL_CACHE.is_file() and not force:
        model, mae = joblib.load(_MODEL_CACHE)
        return model, mae

    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import train_test_split

    df = _load_dataset()
    X = df[feature_cols()].fillna(0.0).to_numpy()
    y = df["log_target(S/cm)"].to_numpy()

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(random_state=42, n_estimators=300, max_depth=3)
    model.fit(X_tr, y_tr)
    mae = mean_absolute_error(y_te, model.predict(X_te))

    _MODEL_CACHE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump((model, mae), _MODEL_CACHE)
    return model, mae


def predict_log_sigma(model, poav: float, a: float, b: float, c: float,
                      composition: dict[str, float]) -> float:
    """Predice log10(sigma) a partir de descriptores del candidato."""
    row = {col: 0.0 for col in feature_cols()}
    row["POAV (cm3/g)"] = poav
    row["a"], row["b"], row["c"] = a, b, c
    for el, frac in composition.items():
        if el in row:
            row[el] = float(frac)
    import numpy as np
    X = np.array([[row[c] for c in feature_cols()]], dtype=float)
    return float(model.predict(X)[0])


def validate_conductivity_coherence(
    model,
    conductivity_log_s_cm: float | None,
    poav: float,
    a: float,
    b: float,
    c: float,
    composition: dict[str, float],
    threshold: float = UMBRAL_LOG_S_CM,
) -> ConductivityResult:
    """Valida coherencia de la conductividad APORTADA vs oráculo.

    Si no se aporta conductividad -> se omite el flag (no se silencia como 0).
    """
    if conductivity_log_s_cm is None:
        return ConductivityResult(
            conductivity_value_log_s_cm=None,
            conductivity_out_of_range=None,
            notes="Sin conductividad aportada: flag omitido (no silenciado).",
        )
    pred = predict_log_sigma(model, poav, a, b, c, composition)
    delta = abs(conductivity_log_s_cm - pred)
    return ConductivityResult(
        conductivity_value_log_s_cm=conductivity_log_s_cm,
        conductivity_out_of_range=delta > threshold,
        notes=f"prediccion oráculo={pred:.3f} log(S/cm); |delta|={delta:.3f}; umbral={threshold}",
    )
