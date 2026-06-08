"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ApiNotice } from "../../components/ApiNotice";
import { apiFetch, type KnowledgeArticleSummary, type KnowledgeArticlesResponse } from "../lib/api";

export default function KnowledgePage() {
  const [articles, setArticles] = useState<KnowledgeArticleSummary[]>([]);
  const [categories, setCategories] = useState<KnowledgeArticlesResponse["categories"]>([]);
  const [activeCategory, setActiveCategory] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadKnowledge(category = activeCategory, search = query) {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      if (search.trim()) params.set("q", search.trim());
      const suffix = params.toString() ? `?${params.toString()}` : "";
      const payload = await apiFetch<KnowledgeArticlesResponse>(`/api/knowledge/articles${suffix}`);
      setArticles(payload.items);
      setCategories(payload.categories);
    } catch (err) {
      setArticles([]);
      setCategories([]);
      setError(err instanceof Error ? `知识库接口不可用：${err.message}` : "知识库接口不可用，请确认后端已启动。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadKnowledge();
  }, []);

  const totalLabel = useMemo(() => {
    if (loading) return "加载中";
    return `${articles.length} 篇`;
  }, [articles.length, loading]);

  function handleCategoryChange(category: string) {
    setActiveCategory(category);
    void loadKnowledge(category, query);
  }

  function handleSearchSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadKnowledge(activeCategory, query);
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">知识库</p>
          <h1>策略、回测与模拟盘学习中心</h1>
          <p>六类内容覆盖产品帮助、量化基础、策略案例、失败复盘、合规说明与数据口径，共 {totalLabel}。</p>
        </div>
        <form className="hero-search" onSubmit={handleSearchSubmit}>
          <label htmlFor="knowledge-search">搜索文章</label>
          <div className="asset-search compact">
            <div>
              <input
                id="knowledge-search"
                placeholder="搜索标题、摘要或正文关键词"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <button type="submit">搜索</button>
            </div>
          </div>
        </form>
      </section>

      <ApiNotice message={error} onRetry={() => loadKnowledge()} />

      <section className="asset-layout">
        <aside className="panel">
          <div className="section-title horizontal">
            <div>
              <p className="eyebrow">分类</p>
              <h2>内容导航</h2>
            </div>
          </div>
          <div className="list-stack" style={{ marginTop: 12 }}>
            <button
              type="button"
              className={activeCategory ? "list-row" : "list-row"}
              style={{
                textAlign: "left",
                borderColor: activeCategory ? "var(--line)" : "var(--accent)",
                background: activeCategory ? "#fff" : "#e9f3ef"
              }}
              onClick={() => handleCategoryChange("")}
            >
              <strong>全部文章</strong>
              <small>{categories.reduce((sum, item) => sum + item.count, 0)} 篇</small>
            </button>
            {categories.map((category) => (
              <button
                key={category.id}
                type="button"
                className="list-row"
                style={{
                  textAlign: "left",
                  borderColor: activeCategory === category.id ? "var(--accent)" : "var(--line)",
                  background: activeCategory === category.id ? "#e9f3ef" : "#fff"
                }}
                onClick={() => handleCategoryChange(category.id)}
              >
                <strong>{category.label}</strong>
                <small>{category.count} 篇</small>
              </button>
            ))}
          </div>
        </aside>

        <div className="panel">
          <div className="section-title horizontal">
            <div>
              <p className="eyebrow">文章列表</p>
              <h2>{activeCategory ? categories.find((item) => item.id === activeCategory)?.label : "全部内容"}</h2>
            </div>
            <small>{totalLabel}</small>
          </div>

          {loading ? <div className="empty-panel">知识库加载中…</div> : null}

          {!loading && articles.length > 0 ? (
            <div className="list-stack" style={{ marginTop: 12 }}>
              {articles.map((article) => (
                <Link className="list-row" href={`/knowledge/${article.slug}`} key={article.slug}>
                  <span className="temp">{article.category_label}</span>
                  <strong>{article.title}</strong>
                  <p>{article.summary}</p>
                  <small>{article.tags.join(" · ")}</small>
                </Link>
              ))}
            </div>
          ) : null}

          {!loading && articles.length === 0 && !error ? (
            <div className="empty-panel">没有匹配的文章，请换个关键词或分类试试。</div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
