from app.services.knowledge_loader import CATEGORY_LABELS, load_knowledge_documents, search_articles


def test_knowledge_loader_finds_thirty_plus_articles():
    articles = load_knowledge_documents(force=True)

    assert len(articles) >= 30
    assert len(CATEGORY_LABELS) == 6
    categories = {article.category for article in articles}
    assert categories == set(CATEGORY_LABELS.keys())
    for article in articles:
        assert article.slug
        assert article.title
        assert article.summary
        assert len(article.body) >= 200


def test_knowledge_loader_search_filters_by_category_and_query():
    articles = load_knowledge_documents(force=True)
    compliance = search_articles(category="compliance")
    backtest_hits = search_articles(query="回测")

    assert len(compliance) >= 5
    assert all(item.category == "compliance" for item in compliance)
    assert len(backtest_hits) >= 3
    assert len(articles) >= 30
