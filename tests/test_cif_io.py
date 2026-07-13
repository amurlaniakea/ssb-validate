# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests de cif_io.py SIN red: fixture CIF incluido en el repo.

Usa tests/fixtures/llzo.cif (generado localmente con pymatgen, composicion
Li7La3Zr2O12). No descarga nada de red.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from ssb_validate.cif_io import CifData, parse_cif

pytest.importorskip("pymatgen")

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "llzo.cif"


def test_parse_cif_llzo_composition():
    data = parse_cif(FIXTURE)
    assert isinstance(data, CifData)
    assert data.formula == "Li7La3Zr2O12"
    assert data.nsites == 24
    # La composicion debe tener Li, La, Zr, O
    for el in ("Li", "La", "Zr", "O"):
        assert el in data.composition


def test_parse_cif_returns_counts():
    data = parse_cif(FIXTURE)
    assert data.composition["Li"] == pytest.approx(7.0)
    assert data.composition["La"] == pytest.approx(3.0)
    assert data.composition["Zr"] == pytest.approx(2.0)
    assert data.composition["O"] == pytest.approx(12.0)


def test_parse_cif_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_cif("no_existe_12345.cif")


def test_parse_cif_bad_path_type(tmp_path):
    # un archivo que existe pero no es CIF valido -> ValueError
    bad = tmp_path / "x.cif"
    bad.write_text("esto no es un cif", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_cif(bad)
