# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests de secrets.py SIN red: ramas de fallback del credentials store.

Cubre: _CRED_PATHS no existe -> None (linea 23); JSON corrupto -> salta (29-30);
entrada materials_project ausente / sin api_key -> None (36). Y el camino feliz
cuando el store tiene la key. Todo con _CRED_PATHS monkeypatcheado a tmp via
monkeypatch (se restaura automatico), nunca el store real de ~/.hermes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ssb_validate import secrets as secrets_mod
from ssb_validate.secrets import resolve_mp_api_key


def _point_to(secrets_mod, monkeypatch, path: Path):
    monkeypatch.setattr(secrets_mod, "_CRED_PATHS", [path], raising=False)


def test_no_cred_file_returns_none(tmp_path, monkeypatch):
    _point_to(secrets_mod, monkeypatch, tmp_path / "noexiste.json")
    monkeypatch.delenv("MP_API_KEY", raising=False)
    assert resolve_mp_api_key() is None


def test_corrupt_json_returns_none(tmp_path, monkeypatch):
    p = tmp_path / "platforms.json"
    p.write_text("{esto no es json", encoding="utf-8")
    _point_to(secrets_mod, monkeypatch, p)
    monkeypatch.delenv("MP_API_KEY", raising=False)
    assert resolve_mp_api_key() is None


def test_materials_project_missing_returns_none(tmp_path, monkeypatch):
    p = tmp_path / "platforms.json"
    p.write_text(json.dumps({"other_service": {"api_key": "x"}}), encoding="utf-8")
    _point_to(secrets_mod, monkeypatch, p)
    monkeypatch.delenv("MP_API_KEY", raising=False)
    assert resolve_mp_api_key() is None


def test_materials_project_without_api_key_returns_none(tmp_path, monkeypatch):
    p = tmp_path / "platforms.json"
    p.write_text(json.dumps({"materials_project": {"note": "sin key"}}), encoding="utf-8")
    _point_to(secrets_mod, monkeypatch, p)
    monkeypatch.delenv("MP_API_KEY", raising=False)
    assert resolve_mp_api_key() is None


def test_env_mp_api_key_wins(tmp_path, monkeypatch):
    p = tmp_path / "platforms.json"
    p.write_text(json.dumps({"materials_project": {"api_key": "del-store"}}), encoding="utf-8")
    _point_to(secrets_mod, monkeypatch, p)
    monkeypatch.setenv("MP_API_KEY", "del-env")
    assert resolve_mp_api_key() == "del-env"


def test_store_key_resolved(tmp_path, monkeypatch):
    p = tmp_path / "platforms.json"
    p.write_text(json.dumps({"materials_project": {"api_key": "del-store"}}), encoding="utf-8")
    _point_to(secrets_mod, monkeypatch, p)
    monkeypatch.delenv("MP_API_KEY", raising=False)
    assert resolve_mp_api_key() == "del-store"
