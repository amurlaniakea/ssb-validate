# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resolucion de secretos: SOLO desde credentials store o env. NUNCA hardcodeado."""
from __future__ import annotations

import json
import os
from pathlib import Path

_CRED_PATHS = [
    Path.home() / ".hermes" / "credentials" / "platforms.json",
]


def resolve_mp_api_key() -> str | None:
    """Devuelve la API key de Materials Project.

    Orden: variable de entorno MP_API_KEY, luego credentials store local.
    No lanza si no hay key: quien llama decide el fallo (AC-5).
    """
    env_key = os.environ.get("MP_API_KEY")
    if env_key:
        return env_key.strip()

    for path in _CRED_PATHS:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            mp = data.get("materials_project")
            if isinstance(mp, dict):
                key = mp.get("api_key")
                if key:
                    return str(key).strip()
    return None
