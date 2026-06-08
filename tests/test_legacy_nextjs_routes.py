import pytest
from pathlib import Path

pytestmark = pytest.mark.skip(reason="P2/future: Next.js 不参与当前 P0 MVP")

ROOT = Path(__file__).resolve().parents[1]
WEB_APP = ROOT / "apps" / "web" / "app"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_next_app_is_split_into_research_workbench_routes():
    required_routes = [
        WEB_APP / "page.tsx",
        WEB_APP / "quant" / "page.tsx",
        WEB_APP / "market" / "page.tsx",
        WEB_APP / "assets" / "page.tsx",
        WEB_APP / "assets" / "[symbol]" / "page.tsx",
        WEB_APP / "strategy-lab" / "page.tsx",
        WEB_APP / "knowledge" / "page.tsx",
        WEB_APP / "knowledge" / "[slug]" / "page.tsx",
        WEB_APP / "ai" / "page.tsx",
        WEB_APP / "alerts" / "page.tsx",
    ]

    for route in required_routes:
        assert route.exists(), f"missing route {route}"


def test_home_page_is_alpha_sim_dashboard_with_live_leaderboard():
    home = read(WEB_APP / "page.tsx")

    assert "Alpha模拟场" in home
    assert "/api/leaderboards" in home
    assert "leaderboard.items" in home
    assert "创建策略" in home
    assert "/quant" in home
    assert "不构成投资建议" in home and "不接真实资金" in home
    assert "/strategy-lab" in home
    assert "handleRunBacktest" not in home
    assert "virtual_capital" in home or "running_strategies" in home


def test_asset_detail_page_has_the_code_to_kline_to_ai_flow():
    asset_page = read(WEB_APP / "assets" / "[symbol]" / "page.tsx")

    required_markers = [
        '"use client"',
        "/api/assets/",
        "/profile",
        "/bars",
        "/risk-card",
        "/research-report",
        "/api/ai/ask",
        "/api/watchlist",
        "handleAskAlpha",
        "handleAddWatchlist",
        "retryAssetLoad",
    ]

    for marker in required_markers:
        assert marker in asset_page
    assert "KLinePanel" in asset_page or "ThsKLineChart" in asset_page


def test_strategy_lab_is_separate_and_keeps_quant_as_professional_tool():
    strategy_page = read(WEB_APP / "strategy-lab" / "page.tsx")

    required_markers = [
        '"use client"',
        "验证投资想法",
        "/api/strategies/compile",
        "/api/backtests",
        "/api/simulations",
        "handleCompileStrategy",
        "handleRunBacktest",
        "handleJoinSimulation",
        "不构成投资建议",
    ]

    for marker in required_markers:
        assert marker in strategy_page


def test_shared_components_support_navigation_search_errors_and_kline():
    expected = [
        ROOT / "apps" / "web" / "components" / "AppShell.tsx",
        ROOT / "apps" / "web" / "components" / "AssetSearch.tsx",
        ROOT / "apps" / "web" / "components" / "ApiNotice.tsx",
        ROOT / "apps" / "web" / "components" / "ApiStatus.tsx",
        ROOT / "apps" / "web" / "components" / "KLinePanel.tsx",
    ]

    for path in expected:
        assert path.exists(), f"missing component {path}"

    shell = read(expected[0])
    search = read(expected[1])
    notice = read(expected[2])
    status = read(expected[3])
    chart = read(expected[4])

    assert "Alpha模拟场" in shell
    assert "量化模拟" in shell and "/quant" in shell
    assert "市场" in shell and "标的" in shell and "策略" in shell
    assert "ApiStatus" in shell
    assert "router.push" in search
    assert "重试" in notice
    assert "后端" in status
    assert "echarts" in chart or "ThsKLineChart" in chart
