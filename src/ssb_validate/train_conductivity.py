# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Entrena y cachea el oráculo de conductividad (Fase 2). Reproducible (seed 42).

Uso:
    python -m ssb_validate.train_conductivity [--force]
Genera data/model_gbr.joblib (NO se commitea; artifact local).
"""
from __future__ import annotations

import argparse

from .conductivity import train_oracle


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="reentrena aunque exista cache")
    args = ap.parse_args()
    model, mae = train_oracle(force=args.force)
    print(f"Oracle entrenado. MAE holdout (dataset 2601.10997) = {mae:.3f} log(S/cm)")
    print("Modelo cacheado en data/model_gbr.joblib")


if __name__ == "__main__":
    main()
