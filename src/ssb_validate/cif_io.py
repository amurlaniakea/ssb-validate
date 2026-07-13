# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""cif_io: parseo local de estructuras CIF para alimentar los validadores.

MVP (item 009 del roadmap): extrae composicion y numero de sitios desde un CIF
usando pymatgen. NO toca red ni predice propiedades. pymatgen es un extra opcional
(`pip install ".[cif]"`), no dependencia core, porque es pesado.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pymatgen.core import Structure


@dataclass
class CifData:
    """Resultado del parseo de un CIF."""

    formula: str  # formula reducida, p.ej. "Li7La3Zr2O12"
    composition: dict[str, float]  # {elemento: cantidad atomica}
    nsites: int
    source: str  # ruta del CIF parseado


def parse_cif(path: str | Path) -> CifData:
    """Parsea un CIF local y devuelve su composicion.

    Args:
        path: ruta al archivo CIF (local, sin red).

    Raises:
        FileNotFoundError: si el CIF no existe.
        ValueError: si pymatgen no puede parsear el CIF.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"CIF no encontrado: {p}")
    try:
        struct = Structure.from_file(str(p))
    except Exception as exc:  # pymatgen lanza varias subclases; las normalizamos
        raise ValueError(f"No se pudo parsear el CIF {p}: {exc}") from exc
    comp = struct.composition
    return CifData(
        formula=comp.reduced_formula,
        composition={el.symbol: float(amt) for el, amt in comp.items()},
        nsites=len(struct),
        source=str(p),
    )
