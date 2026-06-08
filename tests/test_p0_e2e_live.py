"""Live HTTP E2E checks for P0 homepage flow."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, str]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def test_live_homepage_serves_static_shell():
    status, body = _request("GET", "/")
    assert status == 200
    assert "AI投资想法体检器" in body
    assert 'id="ideaInput"' in body
    assert 'id="diagnoseIdea"' in body


def test_live_app_js_has_friendly_error_parser():
    status, body = _request("GET", "/static/app.js")
    assert status == 200
    assert "function parseApiError" in body
    assert "请至少输入 2 个字的投资想法" in body
    assert "/api/market/summary" not in body


def test_live_guang_module_diagnose_flow():
    status, body = _request(
        "POST",
        "/api/ideas/diagnose",
        {"idea": "光模块", "market": "A股", "risk_preference": "小白默认"},
    )
    assert status == 200, body
    diagnosis = json.loads(body)
    assert diagnosis["raw_idea"] == "光模块"
    assert diagnosis["replay_type"] == "demo_virtual_sample"
    assert diagnosis["replay_note"]

    share_status, share_body = _request(
        "POST",
        "/api/content/share-card",
        {
            "diagnosis_id": diagnosis["idea_id"],
            "platform": "xiaohongshu",
            "diagnosis": diagnosis,
        },
    )
    assert share_status == 200, share_body
    share = json.loads(share_body)
    assert share["titles"]
    assert share["short_video_script"]["hook"]
    assert "不构成投资建议" in share["disclaimer"]


def test_live_single_char_idea_returns_422_not_200():
    status, body = _request(
        "POST",
        "/api/ideas/diagnose",
        {"idea": "光", "market": "A股", "risk_preference": "小白默认"},
    )
    assert status == 422
    assert "string_too_short" in body
