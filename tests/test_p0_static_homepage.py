from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC_APP = ROOT / "app" / "static"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_static_homepage_is_idea_diagnosis_product():
    html = read(STATIC_APP / "index.html")

    required_markers = [
        "AI投资想法体检器",
        "看到热点想买",
        'id="ideaInput"',
        'id="assetSymbol"',
        'id="diagnoseIdea"',
        'id="diagnosisCard"',
        'id="trendingIdeaList"',
        'id="contentGenerator"',
        "不构成投资建议",
        "不接真实资金",
        "不提供买卖建议",
    ]

    for marker in required_markers:
        assert marker in html, f"missing homepage marker {marker}"

    forbidden_markers = [
        "Alpha模拟场",
        "策略工厂",
        "运行回测",
        "加入模拟盘",
        "7天观察",
        "问问Alpha",
        "风险卡",
        "知识库",
        "数据源",
        "市场解释",
    ]

    for marker in forbidden_markers:
        assert marker not in html, f"forbidden homepage marker found: {marker}"


def test_static_styles_keep_required_structure_and_responsive_rules():
    styles = read(STATIC_APP / "styles.css")

    required_sections = [
        "/* tokens */",
        "/* base */",
        "/* layout */",
        "/* components */",
        "/* states */",
        "/* responsive */",
    ]

    for section in required_sections:
        assert section in styles

    assert "@media (max-width: 980px)" in styles
    assert "@media (max-width: 640px)" in styles
