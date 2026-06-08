from app.models import Citation, KnowledgeLesson
from app.services.legacy_content import get_knowledge_base
from app.services.knowledge_loader import load_knowledge_documents


def _lessons_from_articles() -> list[KnowledgeLesson]:
    lessons: list[KnowledgeLesson] = []
    for article in load_knowledge_documents():
        body_lines = [line.strip() for line in article.body.splitlines() if line.strip() and not line.startswith("#")]
        example = body_lines[1] if len(body_lines) > 1 else body_lines[0] if body_lines else article.summary
        lessons.append(
            KnowledgeLesson(
                term=article.title,
                plain_explanation=article.summary,
                why_it_matters=body_lines[0] if body_lines else article.summary,
                example=example,
            )
        )
    return lessons


def _all_lessons() -> list[KnowledgeLesson]:
    articles = _lessons_from_articles()
    if len(articles) >= 30:
        return articles
    return get_knowledge_base().lessons


def search_knowledge(question: str, limit: int = 3) -> list[KnowledgeLesson]:
    lessons = _all_lessons()
    normalized = question.lower()
    scored: list[tuple[int, KnowledgeLesson]] = []
    for lesson in lessons:
        score = 0
        for token in (lesson.term, lesson.plain_explanation, lesson.why_it_matters, lesson.example):
            if token and token.lower() in normalized:
                score += 3
        for keyword in ("回撤", "回测", "模拟", "风险", "数据源", "过拟合", "k线", "etf"):
            if keyword in normalized and keyword in lesson.plain_explanation.lower():
                score += 2
        if score:
            scored.append((score, lesson))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return lessons[:limit]
    return [lesson for _, lesson in scored[:limit]]


def citations_for_lessons(lessons: list[KnowledgeLesson]) -> list[Citation]:
    return [
        Citation(
            source_type="knowledge_chunk",
            source_id=f"kb_{lesson.term}",
            title=lesson.term,
            url="/api/knowledge",
        )
        for lesson in lessons
    ]
