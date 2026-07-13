# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""AC-5: la API key NO esta hardcodeada en el binario y se resuelve del credentials store."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ssb_validate.secrets import resolve_mp_api_key

REPO_ROOT = Path(__file__).resolve().parents[1]
# Key real guardada en credentials store (NO debe aparecer en src/)
REAL_KEY = "REDACTED"


def test_ac5_key_not_in_source():
    """AC-5: grep del literal de la key en src/ debe ser vacio."""
    r = subprocess.run(
        ["grep", "-rn", REAL_KEY, "src/"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    # grep exit 1 = no match (lo que queremos). exit 0 = encontrado (FALLO).
    assert r.returncode == 1, f"API key encontrada en src/: {r.stdout}"


def test_ac5_resolves_from_credentials(monkeypatch):
    """AC-5: resolve_mp_api_key lee del credentials store (sin env MP_API_KEY)."""
    monkeypatch.delenv("MP_API_KEY", raising=False)
    key = resolve_mp_api_key()
    assert key is not None, "No se resolvio la key desde credentials store"
    assert key == REAL_KEY


@pytest.mark.slow
def test_ac1_external_llzo_real_mp():
    """AC-1 (validez EXTERNA): contra MP real, LLZO devuelve E_above_hull ~0 (estable)."""
    from ssb_validate.mp_client import MPClient
    from ssb_validate.stability import validate_stability

    # Requiere MP_API_KEY en env o credentials store con la key real.
    client = MPClient()
    res = validate_stability(client, "Li7La3Zr2O12")
    assert res.material_id is not None
    assert 0.0 <= res.energy_above_hull_ev_per_atom < 0.05, (
        f"LLZO deberia estar cerca del convex hull, got {res.energy_above_hull_ev_per_atom}"
    )
    assert res.stability_flag is False
