import { AssetSearch } from "../../components/AssetSearch";

const examples = [
  { symbol: "510300", name: "沪深300ETF", body: "宽基指数、回撤、成交量和风险卡观察。" },
  { symbol: "159915", name: "创业板ETF", body: "成长风格弹性较高，重点看波动和行业集中。" },
  { symbol: "512880", name: "证券ETF", body: "行业主题样本，适合观察板块轮动和成交热度。" },
  { symbol: "600000", name: "浦发银行", body: "A股个股样本，进入财务、公告和K线解释链路。" }
];

export default function AssetsPage() {
  return (
    <div className="page-stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">标的研究</p>
          <h1>用代码进入研究，而不是从榜单开始</h1>
          <p>股票、ETF、指数先进入同一套研究链路：K线、资料、风险卡、问AI和观察列表。</p>
        </div>
        <AssetSearch />
      </section>

      <section className="task-entry-grid four">
        {examples.map((item) => (
          <a className="entry-card" href={`/assets/${item.symbol}`} key={item.symbol}>
            <span>{item.symbol}</span>
            <strong>{item.name}</strong>
            <p>{item.body}</p>
          </a>
        ))}
      </section>
    </div>
  );
}
