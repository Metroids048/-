from app.services.compliance_guard import DEFAULT_DISCLAIMER, sanitize_payload


TRENDING_TEMPLATES = [
    ("trend_ai_etf", "AI ETF 又涨了，现在追是不是晚了？", "追涨型", 92, 78, "热度高，但追涨风险也高。"),
    ("trend_broker", "券商突然放量拉升，现在上车会不会太晚？", "追涨型", 88, 74, "行情热，但波动与回撤风险同时放大。"),
    ("trend_new_energy", "新能源跌这么久了，现在是不是抄底窗口？", "抄底型", 85, 81, "看似便宜，但下跌趋势可能未结束。"),
    ("trend_gold", "黄金连续上涨，避险仓位要不要加？", "防守型", 80, 63, "防守逻辑成立，但追高同样有波动风险。"),
    ("trend_dividend", "红利 ETF 一直稳，这时候加仓稳吗？", "高股息型", 78, 58, "防守风格有效，但风格切换要警惕。"),
    ("trend_chip", "半导体突破后，能不能继续追？", "追涨型", 83, 76, "突破后最怕放量滞涨导致回撤。"),
    ("trend_robot", "机器人概念火了，现在补票还来得及吗？", "题材幻想型", 90, 84, "题材拥挤阶段，退潮风险偏高。"),
    ("trend_low_altitude", "低空经济反复活跃，现在适合参与吗？", "题材幻想型", 79, 72, "叙事强，但持续性不确定。"),
    ("trend_medicine", "医药反弹了，是不是跌够了？", "抄底型", 77, 69, "反弹可能存在，但确认信号仍不足。"),
    ("trend_bank", "银行高股息还能继续作为核心防守吗？", "高股息型", 74, 56, "防守价值在，但估值也要关注。"),
]


def list_trending_ideas() -> dict:
    items = [
        {
            "id": item_id,
            "title": title,
            "idea_type": idea_type,
            "heat_score": heat_score,
            "risk_score": risk_score,
            "teaser": teaser,
        }
        for item_id, title, idea_type, heat_score, risk_score, teaser in TRENDING_TEMPLATES
    ]
    return sanitize_payload({"items": items, "disclaimer": DEFAULT_DISCLAIMER})
