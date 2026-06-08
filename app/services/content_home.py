from app.models import ContentHome


def get_content_home() -> ContentHome:
    return ContentHome(
        product_name="AI投资想法体检器",
        positioning="看到热点想买？先让 AI 体检一下。",
        hero_promise="输入一句投资想法，生成虚拟样本回放、风险反例、小白提醒和可分享内容。",
        primary_cta="生成想法体检卡",
        compliance_boundary=[
            "不构成投资建议",
            "不提供买卖建议",
            "不接真实资金",
            "不承诺收益",
        ],
    )
