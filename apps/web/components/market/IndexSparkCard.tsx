"use client";

import { useEffect, useRef } from "react";
import { changeClass, fmtPct, fmtPrice, type MarketIndexItem } from "../../app/lib/api";

type Props = {
  item: MarketIndexItem;
};

function buildSparkOption(item: MarketIndexItem): Record<string, unknown> {
  const closes = item.sparkline.map((bar) => bar.close);
  const rising = item.change_pct >= 0;
  const lineColor = rising ? "#ef5354" : "#26a69a";
  const areaColor = rising ? "rgba(239,83,84,0.18)" : "rgba(38,166,154,0.18)";

  return {
    animation: false,
    grid: { left: 0, right: 0, top: 2, bottom: 2 },
    xAxis: { type: "category", show: false, data: item.sparkline.map((bar) => bar.date) },
    yAxis: { type: "value", show: false, scale: true },
    series: [
      {
        type: "line",
        data: closes,
        smooth: true,
        symbol: "none",
        lineStyle: { width: 2, color: lineColor },
        areaStyle: { color: areaColor },
      },
    ],
  };
}

export function IndexSparkCard({ item }: Props) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let instance: { dispose: () => void; setOption: (option: Record<string, unknown>) => void; resize: () => void } | null =
      null;
    let disposed = false;

    async function renderChart() {
      if (!chartRef.current) return;
      const echarts = await import("echarts");
      if (disposed || !chartRef.current) return;
      instance = echarts.init(chartRef.current);
      instance.setOption(buildSparkOption(item));

      const onResize = () => instance?.resize();
      window.addEventListener("resize", onResize);
      return () => window.removeEventListener("resize", onResize);
    }

    const cleanupPromise = renderChart();
    return () => {
      disposed = true;
      void cleanupPromise.then((cleanup) => cleanup?.());
      instance?.dispose();
    };
  }, [item]);

  return (
    <article className="index-card">
      <div className="index-card-head">
        <div>
          <p className="eyebrow">{item.code}</p>
          <strong>{item.name}</strong>
        </div>
        <span className={`change-pill ${changeClass(item.change_pct)}`}>{fmtPct(item.change_pct)}</span>
      </div>
      <p className="index-price">{fmtPrice(item.latest_price)}</p>
      <div className="index-sparkline" ref={chartRef} aria-hidden="true" />
    </article>
  );
}
