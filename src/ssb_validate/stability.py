# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regla de estabilidad termodinamica (AC-1, AC-2)."""
from __future__ import annotations

from .models import StabilityResult
from .mp_client import MPClient, MPClientError

# Umbral: materiales con E_above_hull > 0.1 eV/atomo se consideran inestables.
# (Convencion comun en materials science para fase metaestable vs convex hull.)
UNSTABLE_THRESHOLD_EV = 0.1


def validate_stability(
    client: MPClient,
    formula: str,
    unstable_threshold_ev: float = UNSTABLE_THRESHOLD_EV,
) -> StabilityResult:
    """Valida estabilidad contra el convex hull de Materials Project.

    Lanza MPClientError si la API falla (AC-1: nunca valor inventado).
    """
    docs = client.get_thermo(formula)
    if not docs:
        raise MPClientError(f"MP no devolvio datos para formula={formula!r}")

    doc = docs[0]
    e_above = float(doc["energy_above_hull"])
    e_form = float(doc["formation_energy_per_atom"])
    material_id = doc.get("material_id")

    return StabilityResult(
        material_id=material_id,
        formula=doc.get("formula_pretty", formula),
        energy_above_hull_ev_per_atom=e_above,
        formation_energy_per_atom=e_form,
        stability_flag=e_above > unstable_threshold_ev,
        notes=f"umbral inestabilidad={unstable_threshold_ev} eV/atomo",
    )
