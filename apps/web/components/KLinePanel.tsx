import { ThsKLineChart } from "./ThsKLineChart";
import type { AssetBarsPayload, BarIndicators, MarketBar } from "../app/lib/api";

export function KLinePanel({
  bars,
  symbol = "510300",
  indicators = null,
}: {
  bars: MarketBar[];
  symbol?: string;
  indicators?: BarIndicators | null;
}) {
  const initialData: AssetBarsPayload = {
    symbol,
    interval: "1d",
    bars,
    source: {
      source_name: "页面预加载",
      fetched_at: new Date().toISOString(),
      quality_status: "partial",
      rights_status: "internal_sample",
    },
    fallback_notice: null,
    indicators,
  };
  return <ThsKLineChart symbol={symbol} initialData={initialData} />;
}

export { ThsKLineChart };
