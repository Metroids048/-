#!/usr/bin/env python3
"""Generate pre-market / post-market brief Markdown from Alpha API services."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.market import get_market_summary
from app.services.watchlist_scan import build_daily_review_narrative, scan_watchlist


def render_pre_market() -> str:
    market = get_market_summary()
    brief = market.pre_market_brief
    lines = [
        f"# 盘前简报 · {market.market_date}",
        "",
        f"**状态**：{market.status}  |  **风险温度**：{market.risk_level}",
        "",
        market.headline,
        "",
    ]
    if brief:
        prob = f"{int(brief.direction_prob * 100)}%" if brief.direction_prob is not None else "—"
        lines.extend(
            [
                f"## 方向框架：{brief.direction_label}（样本概率 {prob}）",
                "",
                "### 跨市场上下文",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in brief.context)
        lines.extend(["", f"**决策口诀**：{brief.action_mantra}", "", "### 证据链", ""])
        lines.extend(f"- {item}" for item in brief.evidence)
        lines.extend(["", f"_{brief.methodology_note}_", ""])
    lines.extend(["## 热门 ETF", ""])
    lines.extend(f"- {item}" for item in market.hot_etfs)
    return "\n".join(lines)


def render_post_market() -> str:
    review = build_daily_review_narrative()
    scan = scan_watchlist()
    lines = [
        f"# {review.headline}",
        "",
        f"**组合扫描**：{scan.portfolio_summary}",
        "",
    ]
    for section in review.sections:
        lines.extend([f"## {section.title}", "", section.body, "", "### 证据", ""])
        lines.extend(f"- {item}" for item in section.evidence)
        lines.append("")
    lines.extend([f"**跟踪条件**：{review.tracking_condition}", "", f"_{review.disclaimer}_"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Alpha daily brief Markdown.")
    parser.add_argument(
        "--mode",
        choices=("pre", "post", "both"),
        default="both",
        help="pre=盘前简报, post=盘后复盘, both=两者",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/briefs"),
        help="Output directory for Markdown files",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode in {"pre", "both"}:
        path = args.output_dir / "pre_market_brief.md"
        path.write_text(render_pre_market(), encoding="utf-8")
        print(f"Wrote {path}")

    if args.mode in {"post", "both"}:
        path = args.output_dir / "post_market_review.md"
        path.write_text(render_post_market(), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
