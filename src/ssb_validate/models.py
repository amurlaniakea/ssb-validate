# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Contratos de datos de ssb-validate. Unica fuente de verdad (SDD: una dataclass/firma)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class StabilityResult(BaseModel):
    """Resultado de la validacion de estabilidad termodinamica."""

    material_id: str | None = None
    formula: str
    energy_above_hull_ev_per_atom: float
    formation_energy_per_atom: float
    stability_flag: bool = Field(
        description="True si el material es termodinamicamente inestable (E_above_hull > umbral)."
    )
    notes: str = ""


class ConductivityResult(BaseModel):
    """Resultado de la validacion de coherencia de conductividad ionica (Fase 2)."""

    conductivity_value_log_s_cm: float | None = None
    conductivity_out_of_range: bool | None = None
    notes: str = ""


class ValidationReport(BaseModel):
    """Reporte estructurado emitido por `ssb-validate check`."""

    material_id: str | None = None
    formula: str
    stability: StabilityResult
    conductivity: ConductivityResult | None = None
    notes: str = ""
