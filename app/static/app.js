let currentDiagnosis = null;
let currentPlatform = "xiaohongshu";
let latestShareContent = null;

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(parseApiError(detail, response.status));
  }
  return response.json();
}

function parseApiError(rawText, status) {
  if (!rawText) {
    return `请求失败（${status}）`;
  }

  try {
    const payload = JSON.parse(rawText);
    const detail = payload.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail.map((item) => {
        const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : "";
        if (field === "idea" && item.type === "string_too_short") {
          return "请至少输入 2 个字的投资想法。";
        }
        if (field === "idea" && item.type === "missing") {
          return "请先输入一句投资想法。";
        }
        if (typeof item.msg === "string" && /[\u4e00-\u9fff]/.test(item.msg)) {
          return item.msg;
        }
        return "请求参数有误，请检查后重试。";
      });
      return [...new Set(messages)].join(" ");
    }
  } catch (_error) {
    // Keep non-JSON bodies readable but avoid dumping huge payloads.
  }

  return rawText.length > 120 ? "请求失败，请稍后重试。" : rawText;
}

function setState(area, state, message = "") {
  const el = document.getElementById(area);
  if (!el) return;
  el.dataset.state = state;
  el.className = `page-state state-${state}`;
  el.textContent = message;
  el.hidden = state === "idle" || !message;
}

function showError(message) {
  setState("pageState", "error", message);
}

function setSectionState(elementId, state) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.dataset.loading = state === "loading" ? "true" : "false";
  el.dataset.empty = state === "empty" ? "true" : "false";
  el.dataset.error = state === "error" ? "true" : "false";
}

async function loadHome() {
  setState("pageState", "loading", "正在加载首页文案…");
  try {
    const home = await api("/api/content/home");
    document.getElementById("targetUser").textContent = home.positioning;
    document.getElementById("heroPromise").textContent = [
      home.hero_promise,
      "不荐股、不跟单、不接真实资金、不提供买卖建议。",
    ].join(" ");
    setState("pageState", "idle", "");
  } catch (error) {
    showError(`首页文案加载失败：${error.message}`);
    throw error;
  }
}

function renderTrendingIdeas(data) {
  const container = document.getElementById("trendingIdeaList");
  if (!data.items || !data.items.length) {
    container.innerHTML = '<p class="empty">暂无热点体检条目。</p>';
    setSectionState("trendingIdeas", "empty");
    return;
  }

  setSectionState("trendingIdeas", "ready");
  container.innerHTML = data.items
    .map(
      (item) => `
        <article class="trending-item" data-idea="${escapeHtml(item.title)}">
          <div class="trending-head">
            <span class="idea-type-tag">${escapeHtml(item.idea_type)}</span>
            <span class="heat-score">热度 ${item.heat_score}</span>
            <span class="risk-score">风险 ${item.risk_score}</span>
          </div>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.teaser)}</p>
          <button type="button" class="btn-link trending-try">试试这个热点</button>
        </article>
      `
    )
    .join("");

  container.querySelectorAll(".trending-item").forEach((card) => {
    card.addEventListener("click", () => {
      document.getElementById("ideaInput").value = card.dataset.idea;
      diagnoseIdea();
    });
  });
}

async function loadTrendingIdeas() {
  setSectionState("trendingIdeas", "loading");
  const container = document.getElementById("trendingIdeaList");
  container.innerHTML = '<p class="loading">正在加载热点体检榜…</p>';
  try {
    const data = await api("/api/ideas/trending");
    renderTrendingIdeas(data);
  } catch (error) {
    container.innerHTML = `<p class="error">热点榜加载失败：${escapeHtml(error.message)}</p>`;
    setSectionState("trendingIdeas", "error");
    showError(`热点榜加载失败：${error.message}`);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderDiagnosisCard(diagnosis) {
  currentDiagnosis = diagnosis;
  const card = document.getElementById("diagnosisCard");
  card.classList.remove("hidden");

  document.getElementById("ideaType").textContent = diagnosis.idea_type;
  document.getElementById("emotionTag").textContent = diagnosis.emotion_tag;
  document.getElementById("diagnosisSummary").textContent = diagnosis.diagnosis_summary;
  document.getElementById("diagnosisLens").textContent = diagnosis.diagnosis_lens || "";
  document.getElementById("diagnosisBasis").textContent = diagnosis.diagnosis_basis
    ? `体检依据：${diagnosis.diagnosis_basis.join("、")}`
    : "";

  const replay = diagnosis.historical_replay || {};
  document.getElementById("replaySimilar").textContent = `${replay.similar_cases || "-"} 次`;
  document.getElementById("replayMedian").textContent = replay.median_case || "-";
  document.getElementById("replayWorst").textContent = replay.worst_case || "-";
  document.getElementById("replayDrawdown").textContent = replay.max_drawdown || "-";

  const badge = document.getElementById("replayTypeBadge");
  badge.textContent =
    diagnosis.replay_type === "demo_virtual_sample" ? "虚拟样本回放" : "示例回放";
  document.getElementById("replayNote").textContent =
    diagnosis.replay_note || "以下为虚拟/示例样本回放，非真实历史统计，不代表未来表现。";

  document.getElementById("riskFlagList").innerHTML = (diagnosis.risk_flags || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  document.getElementById("failureCaseList").innerHTML = (diagnosis.failure_cases || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  document.getElementById("xiaobaiReminder").textContent = diagnosis.xiaobai_reminder;
  document.getElementById("cardDisclaimer").textContent = diagnosis.disclaimer;

  document.getElementById("contentGenerator").classList.remove("hidden");
  latestShareContent = null;
  document.getElementById("shareTitleList").innerHTML = "";
  document.getElementById("shareBody").textContent = "";
  document.getElementById("shortVideoScript").innerHTML = "";

  if (diagnosis.warning) {
    setState("pageState", "error", diagnosis.warning);
  } else {
    setState("pageState", "idle", "");
  }

  card.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function diagnoseIdea() {
  const idea = document.getElementById("ideaInput").value.trim();
  const symbol = document.getElementById("assetSymbol")?.value.trim().toUpperCase() || "";
  if (!idea) {
    showError("请先输入一句投资想法。");
    return;
  }
  if (idea.length < 2) {
    showError("请至少输入 2 个字的投资想法。");
    return;
  }

  setState("pageState", "loading", "正在生成想法体检卡…");
  try {
    const diagnosis = await api("/api/ideas/diagnose", {
      method: "POST",
      body: JSON.stringify({
        idea,
        market: "A股",
        risk_preference: "小白默认",
        symbol: symbol || null,
      }),
    });
    renderDiagnosisCard(diagnosis);
  } catch (error) {
    showError(`体检失败：${error.message}`);
  }
}

function renderShareContent(content) {
  latestShareContent = content;
  document.getElementById("shareTitleList").innerHTML = (content.titles || [])
    .map((title) => `<li>${escapeHtml(title)}</li>`)
    .join("");
  document.getElementById("shareBody").textContent = content.body || "";

  const script = content.short_video_script || {};
  document.getElementById("shortVideoScript").innerHTML = `
    <p><strong>开场：</strong>${escapeHtml(script.hook || "")}</p>
    <p><strong>正文：</strong>${escapeHtml(script.body || "")}</p>
    <p><strong>结尾：</strong>${escapeHtml(script.ending || "")}</p>
  `;
}

async function generateShareContent(platform = currentPlatform) {
  if (!currentDiagnosis) {
    showError("请先生成想法体检卡。");
    return;
  }

  setState("pageState", "loading", "正在生成分享文案…");
  try {
    const content = await api("/api/content/share-card", {
      method: "POST",
      body: JSON.stringify({
        diagnosis_id: currentDiagnosis.idea_id,
        platform,
        diagnosis: currentDiagnosis,
      }),
    });
    renderShareContent(content);
    setState("pageState", "idle", "");
  } catch (error) {
    showError(`分享文案生成失败：${error.message}`);
  }
}

async function copyShareContent() {
  if (!latestShareContent) {
    showError("请先生成分享文案。");
    return;
  }

  const script = latestShareContent.short_video_script || {};
  const text = [
    (latestShareContent.titles || []).join("\n"),
    "",
    latestShareContent.body || "",
    "",
    `开场：${script.hook || ""}`,
    `正文：${script.body || ""}`,
    `结尾：${script.ending || ""}`,
    "",
    latestShareContent.disclaimer || "",
  ].join("\n");

  try {
    await navigator.clipboard.writeText(text);
    setState("pageState", "idle", "分享文案已复制到剪贴板。");
  } catch (error) {
    showError(`复制失败：${error.message}`);
  }
}

function bindEvents() {
  document.getElementById("diagnoseIdea").addEventListener("click", diagnoseIdea);
  document.getElementById("generateShareContent").addEventListener("click", () => {
    generateShareContent(currentPlatform);
  });
  document.getElementById("copyShareContent").addEventListener("click", copyShareContent);

  document.querySelectorAll(".platform-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".platform-tab").forEach((el) => el.classList.remove("active"));
      tab.classList.add("active");
      currentPlatform = tab.dataset.platform;
      if (currentDiagnosis) {
        generateShareContent(currentPlatform);
      }
    });
  });
}

async function init() {
  bindEvents();
  await loadHome();
  await loadTrendingIdeas();
}

init();
