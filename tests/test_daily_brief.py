import sys
from pathlib import Path
from unittest.mock import patch

from scripts.daily_brief import render_post_market, render_pre_market


def test_daily_brief_renderers_include_core_sections():
    pre = render_pre_market()
    post = render_post_market()

    assert "盘前简报" in pre
    assert "决策口诀" in pre
    assert "样本概率" in pre

    assert "盘后数据复盘" in post
    assert "跟踪条件" in post
    assert "不构成" in post


def test_daily_brief_script_writes_files(tmp_path: Path):
    from scripts.daily_brief import main

    with patch.object(
        sys,
        "argv",
        ["daily_brief.py", "--mode", "both", "--output-dir", str(tmp_path)],
    ):
        main()

    assert (tmp_path / "pre_market_brief.md").exists()
    assert (tmp_path / "post_market_review.md").exists()
    assert "盘前简报" in (tmp_path / "pre_market_brief.md").read_text(encoding="utf-8")
