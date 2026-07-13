# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fast-suite smoke: el paquete importa y la CLI responde sin red."""
from __future__ import annotations

from typer.testing import CliRunner

from ssb_validate.cli import app
from ssb_validate.models import ValidationReport


def test_package_imports():
    import ssb_validate

    assert ssb_validate.__version__ == "0.1.0"


def test_validation_report_model():
    from ssb_validate.stability import UNSTABLE_THRESHOLD_EV
    from ssb_validate.models import StabilityResult

    rep = ValidationReport(
        formula="Li7La3Zr2O12",
        stability=StabilityResult(
            formula="Li7La3Zr2O12",
            energy_above_hull_ev_per_atom=0.0,
            formation_energy_per_atom=-3.0,
            stability_flag=False,
        ),
    )
    assert rep.formula == "Li7La3Zr2O12"
    assert UNSTABLE_THRESHOLD_EV == 0.1


def test_cli_help():
    runner = CliRunner()
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "ssb-validate" in r.stdout
