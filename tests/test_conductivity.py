# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests del filtro de conductividad (AC-3).

AC-3a (oraculo externo): el GBR entrenado sobre el dataset REAL 2601.10997 tiene
MAE holdout medido < 2.0 log(S/cm). Esto mide CAPACIDAD PREDICTIVA del oráculo
sobre ground truth externo (no el del paper). No es "resuelve el problema".
AC-3b (filtro coherencia): usa filas del dataset como candidatos conocidos;
un valor APORTADO coherente -> flag False; uno incoherente (>umbral) -> flag True.
"""
from __future__ import annotations

import pandas as pd
import pytest

from ssb_validate.conductivity import (
    UMBRAL_LOG_S_CM,
    feature_cols,
    predict_log_sigma,
    train_oracle,
    validate_conductivity_coherence,
)

pytestmark = pytest.mark.slow  # requiere dataset real en data/raw/


def _sample_rows():
    df = pd.read_excel(
        "data/raw/all_cif_data.xlsx", sheet_name="all"
    ).dropna(subset=["log_target(S/cm)"])
    geom = ["POAV (cm3/g)", "a", "b", "c"]
    elems = [c for c in feature_cols() if c not in geom]
    rows = []
    for _, r in df.head(20).iterrows():
        comp = {e: float(r[e]) for e in elems if e in r and pd.notna(r[e])}
        rows.append({
            "poav": float(r["POAV (cm3/g)"]),
            "a": float(r["a"]), "b": float(r["b"]), "c": float(r["c"]),
            "comp": comp,
            "true_log": float(r["log_target(S/cm)"]),
        })
    return rows


def test_ac3a_oracle_mae_measured():
    """AC-3a: MAE del oráculo en holdout del dataset real es razonable (< 2.0)."""
    _, mae = train_oracle()
    assert mae < 2.0, f"MAE oráculo inesperado: {mae}"


def test_ac3b_coherent_not_flagged():
    """AC-3b: valor aportado COHERENTE (≈ prediccion) -> flag False."""
    model, _ = train_oracle()
    rows = _sample_rows()
    r0 = rows[0]
    pred = predict_log_sigma(model, r0["poav"], r0["a"], r0["b"], r0["c"], r0["comp"])
    # aportamos el propio valor predicho -> delta ~0 -> coherente
    kw = dict(poav=r0["poav"], a=r0["a"], b=r0["b"], c=r0["c"], composition=r0["comp"])
    res = validate_conductivity_coherence(model, pred, **kw)
    assert res.conductivity_out_of_range is False
    assert abs(res.conductivity_value_log_s_cm - pred) < 1e-6


def test_ac3b_incoherent_flagged():
    """AC-3b: valor aportado INCOHERENTE (>umbral) -> flag True."""
    model, _ = train_oracle()
    rows = _sample_rows()
    r0 = rows[0]
    pred = predict_log_sigma(model, r0["poav"], r0["a"], r0["b"], r0["c"], r0["comp"])
    absurd = pred + (UMBRAL_LOG_S_CM + 1.0)  # diferencia > umbral
    kw = dict(poav=r0["poav"], a=r0["a"], b=r0["b"], c=r0["c"], composition=r0["comp"])
    res = validate_conductivity_coherence(model, absurd, **kw)
    assert res.conductivity_out_of_range is True


def test_ac3b_no_value_omits_flag():
    """AC-3b: sin conductividad aportada -> flag None (no silenciado como 0)."""
    model, _ = train_oracle()
    rows = _sample_rows()
    r0 = rows[0]
    kw = dict(poav=r0["poav"], a=r0["a"], b=r0["b"], c=r0["c"], composition=r0["comp"])
    res = validate_conductivity_coherence(model, None, **kw)
    assert res.conductivity_out_of_range is None
