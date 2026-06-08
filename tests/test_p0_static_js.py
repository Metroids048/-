from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC_APP = ROOT / "app" / "static"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_static_frontend_calls_only_p0_apis():
    script = read(STATIC_APP / "app.js")

    required_apis = [
        "/api/content/home",
        "/api/ideas/trending",
        "/api/ideas/diagnose",
        "/api/content/share-card",
    ]
    forbidden_apis = [
        "/api/market/summary",
        "/api/knowledge",
        "/api/data/sources",
        "/api/assets/510300/risk-card",
        "/api/ai/ask",
        "/api/strategies/compile",
        "/api/backtests",
        "/api/simulations",
        "/api/leaderboards",
    ]

    for api_path in required_apis:
        assert api_path in script, f"missing required API call {api_path}"

    for api_path in forbidden_apis:
        assert api_path not in script, f"forbidden API call found: {api_path}"

    for state_name in ["loading", "empty", "error"]:
        assert state_name in script

    assert "assetSymbol" in script
    assert "symbol: symbol || null" in script


def test_escape_html_uses_replace_all():
    script = read(STATIC_APP / "app.js")

    assert "function escapeHtml" in script
    assert 'replaceAll("&", "&amp;")' in script
    assert 'replaceAll("<", "&lt;")' in script
    assert 'replaceAll(">", "&gt;")' in script


def test_parse_api_error_helper_exists():
    script = read(STATIC_APP / "app.js")

    assert "function parseApiError" in script
    assert "请至少输入 2 个字的投资想法" in script


def test_share_card_passes_diagnosis_fallback():
    script = read(STATIC_APP / "app.js")

    assert "diagnosis: currentDiagnosis" in script
