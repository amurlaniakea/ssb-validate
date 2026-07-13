# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""CLI de ssb-validate (Typer)."""
from __future__ import annotations

import json
import typer

from .mp_client import MPClient
from .stability import validate_stability
from .models import ValidationReport, ConductivityResult

app = typer.Typer(name="ssb-validate", help="Validador de coherencia para electrolitos solidos.")


@app.callback()
def _root() -> None:
    """ssb-validate: valida estabilidad (MP convex hull) y coherencia de conductividad."""


@app.command()
def check(
    material: str = typer.Option(None, "--material", help="material_id o formula, p.ej. Li7La3Zr2O12"),
    cif: str = typer.Option(None, "--cif", help="ruta a estructura CIF (Fase 3)"),
    conductivity_log: float = typer.Option(None, "--conductivity-log", help="log10(sigma) aportada en S/cm"),
    poav: float = typer.Option(None, "--poav", help="probe-occupiable volume cm3/g"),
    a: float = typer.Option(None, "--a", help="parametro de red a"),
    b: float = typer.Option(None, "--b", help="parametro de red b"),
    c: float = typer.Option(None, "--c", help="parametro de red c"),
    json_out: bool = typer.Option(False, "--json", help="salida JSON"),
) -> None:
    """Valida un candidato contra convex hull de Materials Project y coherencia de conductividad."""
    if not material and not cif:
        typer.echo("Error: requiere --material o --cif", err=True)
        raise typer.Exit(code=2)

    client = MPClient()
    try:
        stability = validate_stability(client, material or "")
    except Exception as exc:  # noqa: BLE001 - reporte limpio al usuario
        typer.echo(f"Error de validacion: {exc}", err=True)
        raise typer.Exit(code=1)

    conductivity = None
    if conductivity_log is not None and poav is not None and a is not None and b is not None and c is not None:
        from .conductivity import train_oracle, validate_conductivity_coherence

        model, _ = train_oracle()
        conductivity = validate_conductivity_coherence(
            model, conductivity_log, poav, a, b, c, composition={}
        )
    elif conductivity_log is not None:
        typer.echo(
            "Aviso: --conductivity-log requiere --poav/--a/--b/--c para validar coherencia.",
            err=True,
        )

    report = ValidationReport(
        material_id=stability.material_id,
        formula=stability.formula,
        stability=stability,
        conductivity=conductivity,
        notes="Fase 2: estabilidad (MP) + coherencia conductividad (oraculo 2601.10997).",
    )

    if json_out:
        typer.echo(report.model_dump_json())
    else:
        typer.echo(f"Formula:        {report.formula}")
        typer.echo(f"Material ID:    {report.material_id}")
        typer.echo(f"E_above_hull:  {stability.energy_above_hull_ev_per_atom} eV/atom")
        typer.echo(f"E_form:        {stability.formation_energy_per_atom} eV/atom")
        typer.echo(f"Inestable:     {stability.stability_flag}")
        if conductivity is not None:
            typer.echo(f"Cond. aportada: {conductivity.conductivity_value_log_s_cm}")
            typer.echo(f"Cond. incoherente: {conductivity.conductivity_out_of_range}")
            typer.echo(f"  -> {conductivity.notes}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
