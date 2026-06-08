"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiNotice } from "../../../components/ApiNotice";
import { apiFetch, type KnowledgeArticleDetail } from "../../lib/api";

function renderInlineMarkdown(text: string) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

function MarkdownBody({ body }: { body: string }) {
  const blocks = body.split(/\n{2,}/);

  return (
    <div className="list-stack">
      {blocks.map((block, index) => {
        const trimmed = block.trim();
        if (!trimmed) return null;
        if (trimmed.startsWith("## ")) {
          return <h3 key={index}>{trimmed.slice(3)}</h3>;
        }
        if (trimmed.startsWith("# ")) {
          return <h2 key={index}>{trimmed.slice(2)}</h2>;
        }
        if (trimmed.startsWith("- ")) {
          const items = trimmed.split("\n").filter((line) => line.startsWith("- "));
          return (
            <ul key={index} style={{ margin: 0, paddingLeft: 20, lineHeight: 1.75 }}>
              {items.map((item, itemIndex) => (
                <li
                  key={itemIndex}
                  dangerouslySetInnerHTML={{ __html: renderInlineMarkdown(item.slice(2)) }}
                />
              ))}
            </ul>
          );
        }
        return (
          <p
            key={index}
            style={{ lineHeight: 1.76, color: "#46504b" }}
            dangerouslySetInnerHTML={{ __html: renderInlineMarkdown(trimmed.replace(/\n/g, "<br />")) }}
          />
        );
      })}
    </div>
  );
}

export default function KnowledgeArticlePage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const slug = params.slug;
  const [article, setArticle] = useState<KnowledgeArticleDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadArticle() {
    if (!slug) return;
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch<KnowledgeArticleDetail>(`/api/knowledge/articles/${slug}`);
      setArticle(payload);
    } catch (err) {
      setArticle(null);
      setError(err instanceof Error ? `文章加载失败：${err.message}` : "文章加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadArticle();
  }, [slug]);

  function handleContinueAsk() {
    if (!article) return;
    const question = encodeURIComponent(`关于《${article.title}》，还有哪些需要注意的风险和限制？`);
    const context = encodeURIComponent(
      JSON.stringify({
        article_slug: article.slug,
        article_title: article.title,
        article_summary: article.summary
      })
    );
    router.push(`/ai?q=${question}&context=${context}`);
  }

  return (
    <div className="page-stack">
      <section className="page-header" style={{ gridTemplateColumns: "minmax(0, 1fr)" }}>
        <div>
          <p className="eyebrow">知识库文章</p>
          <h1>{article?.title || "加载中…"}</h1>
          {article ? (
            <>
              <p>{article.summary}</p>
              <small>
                {article.category_label} · {article.tags.join(" · ")}
              </small>
            </>
          ) : null}
        </div>
      </section>

      <ApiNotice message={error} onRetry={loadArticle} />

      {loading ? <div className="empty-panel">文章加载中…</div> : null}

      {!loading && article ? (
        <>
          <section className="panel">
            <MarkdownBody body={article.body} />
          </section>

          <section className="split-panel">
            <div>
              <p className="eyebrow">继续研究</p>
              <h2>带着上下文追问 Alpha</h2>
              <p>围绕当前文章内容继续提问，系统会结合知识库片段与合规边界给出解释。</p>
            </div>
            <div style={{ display: "grid", gap: 10, alignContent: "start" }}>
              <button type="button" onClick={handleContinueAsk}>
                继续追问
              </button>
              <Link href="/knowledge" className="fine-print">
                返回知识库列表
              </Link>
            </div>
          </section>

          <p className="fine-print">{article.disclaimer}</p>
        </>
      ) : null}
    </div>
  );
}
