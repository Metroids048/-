"""Load knowledge CMS markdown articles from data/knowledge/."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_ROOT = ROOT / "data" / "knowledge"

CATEGORY_DIRS = {
    "product_help": "product_help",
    "quant_basics": "quant_basics",
    "strategy_cases": "strategy_cases",
    "failure_cases": "failure_cases",
    "compliance": "compliance",
    "data_dictionary": "data_dictionary",
}

CATEGORY_LABELS = {
    "product_help": "产品帮助",
    "quant_basics": "量化基础",
    "strategy_cases": "策略案例",
    "failure_cases": "失败案例",
    "compliance": "合规说明",
    "data_dictionary": "数据口径",
}

_DIR_TO_CATEGORY = {folder: key for key, folder in CATEGORY_DIRS.items()}

_CACHED_ARTICLES: list[KnowledgeArticle] | None = None


@dataclass(frozen=True)
class KnowledgeArticle:
    slug: str
    title: str
    category: str
    tags: list[str]
    summary: str
    body: str
    source_path: str

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category)

    @property
    def embedding_text(self) -> str:
        return f"{self.title}\n{self.summary}\n{self.body}"

    @property
    def document_id(self) -> str:
        return self.slug


def _parse_tags(raw: str) -> list[str]:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("'\"") for part in inner.split(",") if part.strip()]
    return [part.strip() for part in raw.split(",") if part.strip()]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text.strip()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not match:
        return {}, text.strip()
    meta_block, body = match.group(1), match.group(2).strip()
    meta: dict[str, str] = {}
    for line in meta_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def _infer_summary(body: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _article_from_file(path: Path, category: str) -> KnowledgeArticle | None:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    slug = meta.get("slug") or path.stem
    title = meta.get("title") or slug
    file_category = meta.get("category") or category
    tags = _parse_tags(meta.get("tags", ""))
    summary = _infer_summary(body, meta.get("summary"))
    if not body:
        return None
    return KnowledgeArticle(
        slug=slug,
        title=title,
        category=file_category,
        tags=tags,
        summary=summary,
        body=body,
        source_path=str(path.relative_to(ROOT)).replace("\\", "/"),
    )


def load_knowledge_documents(*, force: bool = False) -> list[KnowledgeArticle]:
    global _CACHED_ARTICLES
    if _CACHED_ARTICLES is not None and not force:
        return _CACHED_ARTICLES

    articles: list[KnowledgeArticle] = []
    if not KNOWLEDGE_ROOT.exists():
        _CACHED_ARTICLES = []
        return _CACHED_ARTICLES

    for subdir in sorted(KNOWLEDGE_ROOT.iterdir()):
        if not subdir.is_dir():
            continue
        category = _DIR_TO_CATEGORY.get(subdir.name, subdir.name)
        for path in sorted(subdir.glob("*.md")):
            article = _article_from_file(path, category)
            if article:
                articles.append(article)

    articles.sort(key=lambda item: (item.category, item.slug))
    _CACHED_ARTICLES = articles
    return articles


def get_article_by_slug(slug: str) -> KnowledgeArticle | None:
    for article in load_knowledge_documents():
        if article.slug == slug:
            return article
    return None


def search_articles(*, category: str | None = None, query: str | None = None) -> list[KnowledgeArticle]:
    results = load_knowledge_documents()
    if category:
        results = [article for article in results if article.category == category]
    if query:
        normalized = query.strip().lower()
        if normalized:
            filtered: list[KnowledgeArticle] = []
            for article in results:
                haystack = " ".join(
                    [article.title, article.summary, article.body, " ".join(article.tags)]
                ).lower()
                if normalized in haystack:
                    filtered.append(article)
            results = filtered
    return results
