"use client";

import { useEffect, useRef } from "react";
import { fmtPct, type MarketHeatmapItem } from "../../app/lib/api";

type Props = {
  items: MarketHeatmapItem[];
};

function colorForChange(changePct: number): string {
  if (changePct >= 0.015) return "#c62828";
  if (changePct >= 0.005) return "#ef5350";
  if (changePct > 0) return "#f28b82";
  if (changePct <= -0.015) return "#1b5e20";
  if (changePct <= -0.005) return "#26a69a";
  return "#81c784";
}

function buildTreemapOption(items: MarketHeatmapItem[]): Record<string, unknown> {
  const sorted = [...items].sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct));
  return {
    tooltip: {
      formatter: (params: { name?: string; data?: { changePct?: number } }) => {
        const change = params.data?.changePct ?? 0;
        return `${params.name ?? ""}<br/>涨跌幅 ${fmtPct(change)}`;
      },
    },
    series: [
      {
        type: "treemap",
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: {
          show: true,
          formatter: (params: { name?: string; data?: { changePct?: number } }) =>
            `${params.name ?? ""}\n${fmtPct(params.data?.changePct ?? 0)}`,
          fontSize: 12,
          color: "#fff",
        },
        upperLabel: { show: false },
        itemStyle: {
          borderColor: "#fffdf8",
          borderWidth: 2,
          gapWidth: 2,
        },
        data: sorted.map((item) => ({
          name: item.name,
          value: Math.max(Math.abs(item.change_pct), 0.001),
          changePct: item.change_pct,
          itemStyle: { color: colorForChange(item.change_pct) },
        })),
      },
    ],
  };
}

export function SectorTreemap({ items }: Props) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let instance: { dispose: () => void; setOption: (option: Record<string, unknown>) => void; resize: () => void } | null =
      null;
    let disposed = false;

    async function renderChart() {
      if (!chartRef.current || !items.length) return;
      const echarts = await import("echarts");
      if (disposed || !chartRef.current) return;
      instance = echarts.init(chartRef.current);
      instance.setOption(buildTreemapOption(items));

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
  }, [items]);

  return <div className="sector-treemap" ref={chartRef} role="img" aria-label="行业板块热力图" />;
}
