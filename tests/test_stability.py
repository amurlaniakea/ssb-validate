# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests de estabilidad (AC-1, AC-2, AC-4, AC-5) SIN red: fixture local con valores reales.

Fixture LLZO (verificado 2026-07-13 contra MP real):
  Li7La3Zr2O12 -> energy_above_hull = 0.0068 eV/atom (estable), E_form = -3.124 eV/atom.
El fixture inestable fuerza el flag de inestabilidad (AC-2). Esto es SELF-CONSISTENCY
(implementacion coincide con su propio spec); la validez EXTERNA la da el test @slow contra MP.
"""
from __future__ import annotations

from typer.testing import CliRunner

from ssb_validate.cli import app
from ssb_validate.mp_client import MPClient, MPClientError
from ssb_validate.stability import validate_stability

# Ground truth medido 2026-07-13 (MP real, LLZO garnet)
LLZO_E_ABOVE = 0.006846009531249031
LLZO_E_FORM = -3.1241169363888894

UNSTABLE_E_ABOVE = 0.450  # > umbral 0.1 -> inestable


class _FakeClient(MPClient):
    """Cliente MP mock: devuelve fixture local, no toca red."""

    def __init__(self, docs: list[dict]):
        super().__init__(api_key="dummy")
        self._docs = docs

    def get_thermo(self, formula: str, max_retries: int = 3) -> list[dict]:
        return self._docs


LLZO_DOC = {
    "formula_pretty": "Li7La3Zr2O12",
    "material_id": "mp-aaacbqoz",
    "energy_above_hull": LLZO_E_ABOVE,
    "formation_energy_per_atom": LLZO_E_FORM,
}


def test_ac1_returns_energy_above_hull_from_fixture():
    """AC-1 (self-consistency): el cliente mock devuelve E_above_hull y E_form."""
    client = _FakeClient([LLZO_DOC])
    res = validate_stability(client, "Li7La3Zr2O12")
    assert res.energy_above_hull_ev_per_atom == LLZO_E_ABOVE
    assert res.formation_energy_per_atom == LLZO_E_FORM
    assert res.material_id == "mp-aaacbqoz"


def test_ac2_stable_not_flagged():
    """AC-2: LLZO (E_above_hull ~0) NO se marca inestable."""
    client = _FakeClient([LLZO_DOC])
    res = validate_stability(client, "Li7La3Zr2O12")
    assert res.stability_flag is False


def test_ac2_unstable_flagged():
    """AC-2: material con E_above_hull > 0.1 se marca inestable."""
    unstable = dict(LLZO_DOC, energy_above_hull=UNSTABLE_E_ABOVE)
    client = _FakeClient([unstable])
    res = validate_stability(client, "FakeUnstable")
    assert res.stability_flag is True


def test_ac1_no_data_raises():
    """AC-1: sin datos MP, lanza error (nunca valor inventado)."""
    client = _FakeClient([])
    try:
        validate_stability(client, "Nothing")
        raise AssertionError("debia lanzar MPClientError")
    except MPClientError:
        pass


def test_ac4_cli_human_and_json():
    """AC-4: CLI emite reporte con campos requeridos, en humano y JSON."""
    runner = CliRunner()
    # Parchear MPClient usado por cli con el mock LLZO
    import ssb_validate.cli as cli_mod

    cli_mod.MPClient = lambda *a, **k: _FakeClient([LLZO_DOC])  # type: ignore[assignment]
    r = runner.invoke(app, ["check", "--material", "Li7La3Zr2O12"])
    assert r.exit_code == 0
    assert "Li7La3Zr2O12" in r.stdout
    assert "Inestable:" in r.stdout
    assert "False" in r.stdout

    rj = runner.invoke(app, ["check", "--material", "Li7La3Zr2O12", "--json"])
    assert rj.exit_code == 0
    # El JSON debe contener campos requeridos
    assert "energy_above_hull_ev_per_atom" in rj.stdout
    assert "stability_flag" in rj.stdout


def test_ac4_cli_requires_input():
    """AC-4: CLI falla (exit 2) sin --material ni --cif."""
    runner = CliRunner()
    r = runner.invoke(app, ["check"])
    assert r.exit_code == 2
