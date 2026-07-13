# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""AC-5: la API key NO esta hardcodeada en el binario ni en el repo.

IMPORTANTE (post-incidente 2026-07-13): este test NUNCA contiene el literal de
la key. La lee del credentials store local (fuera del repo) y la usa para:
  (a) grepear todo el repo (src/ Y tests/) y afirmar que NO aparece, y
  (b) verificar que resolve_mp_api_key() la resuelve.
Si no hay credentials store local (p.ej. CI sin secret), el test hace skip.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ssb_validate.secrets import resolve_mp_api_key

REPO_ROOT = Path(__file__).resolve().parents[1]


def _store_key() -> str | None:
    """Lee la key real del credentials store local (NO hardcodeada en el test)."""
    cred = Path.home() / ".hermes" / "credentials" / "platforms.json"
    if not cred.is_file():
        return None
    try:
        d = json.loads(cred.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    mp = d.get("materials_project")
    if isinstance(mp, dict):
        return mp.get("api_key")
    return None


def test_ac5_key_not_in_repo():
    """AC-5: la key real (del store) NO aparece en ningun archivo del repo (src/ ni tests/)."""
    key = _store_key()
    if not key:
        pytest.skip("No credentials store local (esperado en CI sin secret)")
    r = subprocess.run(
        [
            "grep", "-rn", key,
            "--exclude-dir=.git",
            "--exclude-dir=__pycache__",
            "--exclude=tests/test_security.py",
            ".",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    # grep exit 1 = no match (lo que queremos). exit 0 = encontrado (FALLO).
    assert r.returncode == 1, f"API key encontrada en repo: {r.stdout}"


def test_ac5_resolves_from_credentials(monkeypatch):
    """AC-5: resolve_mp_api_key lee del credentials store (sin env MP_API_KEY)."""
    cred = Path.home() / ".hermes" / "credentials" / "platforms.json"
    if not cred.is_file():
        pytest.skip("No credentials store local (esperado en CI sin secret)")
    monkeypatch.delenv("MP_API_KEY", raising=False)
    key = resolve_mp_api_key()
    assert key is not None, "No se resolvio la key desde credentials store"
    assert key == _store_key()


@pytest.mark.slow
def test_ac1_external_llzo_real_mp():
    """AC-1 (validez EXTERNA): contra MP real, LLZO devuelve E_above_hull ~0 (estable)."""
    if not resolve_mp_api_key():
        pytest.skip("MP_API_KEY no disponible (esperado en CI sin secret)")
    from ssb_validate.mp_client import MPClient
    from ssb_validate.stability import validate_stability

    client = MPClient()
    res = validate_stability(client, "Li7La3Zr2O12")
    assert res.material_id is not None
    assert 0.0 <= res.energy_above_hull_ev_per_atom < 0.05, (
        f"LLZO deberia estar cerca del convex hull, got {res.energy_above_hull_ev_per_atom}"
    )
    assert res.stability_flag is False
