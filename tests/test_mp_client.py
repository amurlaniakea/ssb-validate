# Copyright (C) 2026 Pedro Sordo Martinez
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests de mp_client.py SIN red: mocks de httpx.Client y time.sleep.

Cubre: _throttle (con/sin espera), _headers (con/sin key), y get_thermo
en sus ramas: 200, 401, 403, 429->retry success, 429->agota, sin key,
HTTPError->retry->agota. Todo local, sin tocar red externa.
"""
from __future__ import annotations

from unittest import mock

from ssb_validate.mp_client import MPClient, MPClientError


def _fake_response(status_code: int, json_data: dict | None = None, text: str = ""):
    resp = mock.Mock()
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


def test_headers_with_key():
    c = MPClient(api_key="dummy")
    h = c._headers()
    assert h["x-api-key"] == "dummy"
    assert h["User-Agent"] == "ssb-validate/0.1"


def test_headers_without_key():
    c = MPClient(api_key="")  # string vacio fuerza rama sin key (None resolviera del store)
    h = c._headers()
    assert "x-api-key" not in h
    assert h["User-Agent"] == "ssb-validate/0.1"


def test_throttle_no_wait_when_fresh(monkeypatch):
    sleeps = []
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr(
        "ssb_validate.mp_client.time.monotonic", lambda: 1000.0
    )
    c = MPClient(api_key="dummy")
    c._last_call = 0.0  # primera llamada: no duerme
    c._throttle()
    assert sleeps == []


def test_throttle_sleeps_when_recent(monkeypatch):
    sleeps = []
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: sleeps.append(s))
    # last_call=1000, ahora=1001 (< rate_limit 3s) -> debe dormir ~2s
    monkeypatch.setattr("ssb_validate.mp_client.time.monotonic", lambda: 1001.0)
    c = MPClient(api_key="dummy", rate_limit_s=3.0)
    c._last_call = 1000.0
    c._throttle()
    assert sleeps == [2.0]


def test_get_thermo_200(monkeypatch):
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: None)
    fake = _fake_response(200, {"data": [{"material_id": "mp-x", "energy_above_hull": 0.1}]})
    with mock.patch("ssb_validate.mp_client.httpx.Client") as Client:
        Client.return_value.__enter__.return_value.get.return_value = fake
        c = MPClient(api_key="dummy")
        out = c.get_thermo("Li7La3Zr2O12")
    assert out == [{"material_id": "mp-x", "energy_above_hull": 0.1}]


def test_get_thermo_401(monkeypatch):
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: None)
    fake = _fake_response(401, text="unauthorized")
    with mock.patch("ssb_validate.mp_client.httpx.Client") as Client:
        Client.return_value.__enter__.return_value.get.return_value = fake
        c = MPClient(api_key="dummy")
        try:
            c.get_thermo("X")
            raise AssertionError("debia lanzar MPClientError")
        except MPClientError as e:
            assert "401" in str(e)


def test_get_thermo_403(monkeypatch):
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: None)
    fake = _fake_response(403, text="forbidden")
    with mock.patch("ssb_validate.mp_client.httpx.Client") as Client:
        Client.return_value.__enter__.return_value.get.return_value = fake
        c = MPClient(api_key="dummy")
        try:
            c.get_thermo("X")
            raise AssertionError("debia lanzar MPClientError")
        except MPClientError as e:
            assert "403" in str(e)


def test_get_thermo_429_then_success(monkeypatch):
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: None)
    r429 = _fake_response(429, text="rate limit")
    r200 = _fake_response(200, {"data": [{"material_id": "mp-y"}]})
    with mock.patch("ssb_validate.mp_client.httpx.Client") as Client:
        Client.return_value.__enter__.return_value.get.side_effect = [r429, r200]
        c = MPClient(api_key="dummy")
        out = c.get_thermo("X", max_retries=3)
    assert out == [{"material_id": "mp-y"}]


def test_get_thermo_429_exhausted(monkeypatch):
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: None)
    r429 = _fake_response(429, text="rate limit")
    with mock.patch("ssb_validate.mp_client.httpx.Client") as Client:
        Client.return_value.__enter__.return_value.get.return_value = r429
        c = MPClient(api_key="dummy")
        try:
            c.get_thermo("X", max_retries=2)
            raise AssertionError("debia lanzar MPClientError")
        except MPClientError as e:
            assert "intentos" in str(e)


def test_get_thermo_without_key():
    c = MPClient(api_key="")  # string vacio fuerza rama sin key
    try:
        c.get_thermo("X")
        raise AssertionError("debia lanzar MPClientError (sin key)")
    except MPClientError as e:
        assert "MP_API_KEY no resuelto" in str(e)


def test_get_thermo_http_error_exhausted(monkeypatch):
    monkeypatch.setattr("ssb_validate.mp_client.time.sleep", lambda s: None)
    with mock.patch("ssb_validate.mp_client.httpx.Client") as Client:
        Client.return_value.__enter__.return_value.get.side_effect = (
            httpx_library_error
        )
        c = MPClient(api_key="dummy")
        try:
            c.get_thermo("X", max_retries=2)
            raise AssertionError("debia lanzar MPClientError")
        except MPClientError as e:
            assert "intentos" in str(e)


def httpx_library_error(*args, **kwargs):
    import httpx

    raise httpx.HTTPError("connection reset")
