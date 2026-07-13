# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cliente de Materials Project (endpoint /materials/thermo/).

Pitfall verificado 2026-07-13: la API nueva renombro `limit`/`skip` a `_limit`/`_skip`.
El convex hull vive en /materials/thermo/ (NO en /core/). `ionic_conductivity` NO es campo.
"""
from __future__ import annotations

import time

import httpx

from .secrets import resolve_mp_api_key

MP_API_ROOT = "https://api.materialsproject.org"
_THERMO = "/materials/thermo/"
_RATE_LIMIT_S = 3.0  # MP aplica limites agresivos; respetamos >=1 req / 3s


class MPClientError(RuntimeError):
    """Error de red/API de Materials Project. Nunca devolvemos valor inventado."""


class MPClient:
    def __init__(
        self,
        api_key: str | None = None,
        api_root: str = MP_API_ROOT,
        timeout: float = 30.0,
        rate_limit_s: float = _RATE_LIMIT_S,
    ):
        self._api_key = api_key if api_key is not None else resolve_mp_api_key()
        self._root = api_root.rstrip("/")
        self._timeout = timeout
        self._rate_limit_s = rate_limit_s
        self._last_call = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if self._last_call and elapsed < self._rate_limit_s:
            time.sleep(self._rate_limit_s - elapsed)
        self._last_call = time.monotonic()

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            # Dejamos que la API responda 401; no inventamos nada.
            return {"User-Agent": "ssb-validate/0.1"}
        return {"x-api-key": self._api_key, "User-Agent": "ssb-validate/0.1"}

    def get_thermo(self, formula: str, max_retries: int = 3) -> list[dict]:
        """Consulta /materials/thermo/?formula=... y devuelve la lista de docs.

        Usa _limit/_fields (nomenclatura nueva). Lanza MPClientError en fallo.
        """
        if not self._api_key:
            raise MPClientError("MP_API_KEY no resuelto (env MP_API_KEY o credentials store)")

        params = {
            "formula": formula,
            "_fields": "formula_pretty,material_id,energy_above_hull,formation_energy_per_atom",
            "_limit": "1",
        }
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            self._throttle()
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    r = client.get(
                        f"{self._root}{_THERMO}", params=params, headers=self._headers()
                    )
                if r.status_code == 200:
                    return r.json().get("data", [])
                if r.status_code in (401, 403):
                    raise MPClientError(f"MP auth fallo: HTTP {r.status_code}")
                if r.status_code == 429:
                    time.sleep(15 + attempt * 10)
                    last_exc = MPClientError("MP 429 (rate limit)")
                    continue
                raise MPClientError(f"MP HTTP {r.status_code}: {r.text[:200]}")
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(5 + attempt * 5)
        raise MPClientError(f"MP fallo tras {max_retries} intentos: {last_exc}")
