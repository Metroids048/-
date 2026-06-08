"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { fetchAssetBars, type AssetBarsPayload, type MarketBar } from "../app/lib/api";

type Interval = "1d" | "1w" | "1m";
type LowerTab = "kdj" | "rsi";

const INTERVAL_TABS: Array<{ label: string; value: Interval }> = [
  { label: "日K", value: "1d" },
  { label: "周K", value: "1w" },
  { label: "月K", value: "1m" },
];

function numberOrNull(value: number | null | undefined, digits = 3): number | null {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  return Number(value.toFixed(digits));
}

function normalizeSeries(series: Array<number | null> | undefined, length: number): Array<number | null> {
  if (!series?.length) {
    return Array.from({ length }, () => null);
  }
  if (series.length >= length) {
    return series.slice(series.length - length).map((item) => numberOrNull(item, 3));
  }
  const padding = Array.from({ length: length - series.length }, () => null);
  return [...padding, ...series.map((item) => numberOrNull(item, 3))];
}

function isRising(bar: MarketBar): boolean {
  return bar.close >= bar.open;
}

function buildChartOption(payload: AssetBarsPayload, showBoll: boolean, lowerTab: LowerTab): Record<string, unknown> {
  const bars = payload.bars;
  const dates = bars.map((item) => item.date);
  const ohlc = bars.map((item) => [item.open, item.close, item.low, item.high]);
  const volume = bars.map((item) => ({
    value: item.volume,
    itemStyle: { color: isRising(item) ? "#ef5350" : "#26a69a" },
  }));

  const indicators = payload.indicators ?? {};
  const ma = indicators.ma ?? {};
  const boll = indicators.boll ?? {};
  const macd = indicators.macd ?? {};
  const kdj = indicators.kdj ?? {};
  const rsi = indicators.rsi ?? [];

  const ma5 = normalizeSeries(ma.ma5, bars.length);
  const ma10 = normalizeSeries(ma.ma10, bars.length);
  const ma20 = normalizeSeries(ma.ma20, bars.length);
  const ma60 = normalizeSeries(ma.ma60, bars.length);

  const bollUpper = normalizeSeries(boll.upper, bars.length);
  const bollMid = normalizeSeries(boll.mid, bars.length);
  const bollLower = normalizeSeries(boll.lower, bars.length);

  const dif = normalizeSeries(macd.dif, bars.length);
  const dea = normalizeSeries(macd.dea, bars.length);
  const hist = normalizeSeries(macd.hist, bars.length);
  const macdBars = hist.map((item) => ({
    value: numberOrNull(item, 3),
    itemStyle: { color: (item ?? 0) >= 0 ? "#ef5350" : "#26a69a" },
  }));

  const kSeries = normalizeSeries(kdj.k, bars.length);
  const dSeries = normalizeSeries(kdj.d, bars.length);
  const jSeries = normalizeSeries(kdj.j, bars.length);
  const rsiSeries = normalizeSeries(rsi, bars.length);

  return {
    animation: false,
    legend: {
      top: 4,
      left: 12,
      itemWidth: 10,
      itemHeight: 6,
      textStyle: { color: "#68716c", fontSize: 11 },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      borderWidth: 1,
      borderColor: "#ddd6c8",
      backgroundColor: "rgba(255, 255, 255, 0.95)",
      textStyle: { color: "#17201d" },
      formatter: (params: Array<{ dataIndex?: number }>) => {
        const index = params?.[0]?.dataIndex ?? 0;
        const bar = bars[index];
        if (!bar) return "";
        return [
          `<strong>${bar.date}</strong>`,
          `开: ${bar.open.toFixed(3)}  高: ${bar.high.toFixed(3)}`,
          `低: ${bar.low.toFixed(3)}  收: ${bar.close.toFixed(3)}`,
          `量: ${bar.volume.toLocaleString("zh-CN")}`,
        ].join("<br/>");
      },
    },
    axisPointer: {
      link: [{ xAxisIndex: [0, 1, 2, 3] }],
      label: { backgroundColor: "#6a7985" },
    },
    grid: [
      { left: 56, right: 20, top: 34, height: "36%" },
      { left: 56, right: 20, top: "44%", height: "12%" },
      { left: 56, right: 20, top: "60%", height: "14%" },
      { left: 56, right: 20, top: "78%", height: "14%" },
    ],
    xAxis: [0, 1, 2, 3].map((idx) => ({
      type: "category",
      data: dates,
      boundaryGap: true,
      axisLine: { lineStyle: { color: "#d6d1c5" } },
      axisTick: { show: false },
      axisLabel: { color: "#68716c", show: idx === 3 },
      min: "dataMin",
      max: "dataMax",
    })),
    yAxis: [
      {
        scale: true,
        splitNumber: 4,
        axisLine: { show: false },
        axisLabel: { color: "#68716c" },
        splitLine: { lineStyle: { color: "#f0ece3" } },
      },
      {
        scale: true,
        splitNumber: 2,
        axisLine: { show: false },
        axisLabel: { color: "#68716c", formatter: "{value}" },
        splitLine: { show: false },
      },
      {
        scale: true,
        splitNumber: 3,
        axisLine: { show: false },
        axisLabel: { color: "#68716c" },
        splitLine: { lineStyle: { color: "#f5f2ea" } },
      },
      {
        scale: true,
        splitNumber: 3,
        axisLine: { show: false },
        axisLabel: { color: "#68716c" },
        splitLine: { lineStyle: { color: "#f5f2ea" } },
      },
    ],
    dataZoom: [
      {
        type: "inside",
        xAxisIndex: [0, 1, 2, 3],
        start: 45,
        end: 100,
      },
      {
        type: "slider",
        xAxisIndex: [0, 1, 2, 3],
        bottom: 4,
        height: 16,
        borderColor: "#d9d4c8",
      },
    ],
    series: [
      {
        name: "K线",
        type: "candlestick",
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ohlc,
        itemStyle: {
          color: "#ef5350",
          color0: "#26a69a",
          borderColor: "#ef5350",
          borderColor0: "#26a69a",
        },
      },
      {
        name: "MA5",
        type: "line",
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma5,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#f5a623" },
      },
      {
        name: "MA10",
        type: "line",
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma10,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#5c90ff" },
      },
      {
        name: "MA20",
        type: "line",
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma20,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#8b6bd6" },
      },
      {
        name: "MA60",
        type: "line",
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma60,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: "#7b8a8b" },
      },
      ...(showBoll
        ? [
            {
              name: "BOLL上轨",
              type: "line",
              xAxisIndex: 0,
              yAxisIndex: 0,
              data: bollUpper,
              showSymbol: false,
              lineStyle: { width: 1, color: "#f06292" },
            },
            {
              name: "BOLL中轨",
              type: "line",
              xAxisIndex: 0,
              yAxisIndex: 0,
              data: bollMid,
              showSymbol: false,
              lineStyle: { width: 1, color: "#9575cd" },
            },
            {
              name: "BOLL下轨",
              type: "line",
              xAxisIndex: 0,
              yAxisIndex: 0,
              data: bollLower,
              showSymbol: false,
              lineStyle: { width: 1, color: "#4db6ac" },
            },
          ]
        : []),
      {
        name: "VOL",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volume,
      },
      {
        name: "MACD",
        type: "bar",
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: macdBars,
      },
      {
        name: "DIF",
        type: "line",
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: dif,
        showSymbol: false,
        lineStyle: { width: 1.1, color: "#4f8cff" },
      },
      {
        name: "DEA",
        type: "line",
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: dea,
        showSymbol: false,
        lineStyle: { width: 1.1, color: "#ff9800" },
      },
      ...(lowerTab === "kdj"
        ? [
            {
              name: "K",
              type: "line",
              xAxisIndex: 3,
              yAxisIndex: 3,
              data: kSeries,
              showSymbol: false,
              lineStyle: { width: 1.1, color: "#ff5252" },
            },
            {
              name: "D",
              type: "line",
              xAxisIndex: 3,
              yAxisIndex: 3,
              data: dSeries,
              showSymbol: false,
              lineStyle: { width: 1.1, color: "#42a5f5" },
            },
            {
              name: "J",
              type: "line",
              xAxisIndex: 3,
              yAxisIndex: 3,
              data: jSeries,
              showSymbol: false,
              lineStyle: { width: 1.1, color: "#ab47bc" },
            },
          ]
        : [
            {
              name: "RSI",
              type: "line",
              xAxisIndex: 3,
              yAxisIndex: 3,
              data: rsiSeries,
              showSymbol: false,
              lineStyle: { width: 1.2, color: "#ff7043" },
            },
          ]),
    ],
  };
}

export function ThsKLineChart({
  symbol,
  initialData,
  limit = 120,
}: {
  symbol: string;
  initialData?: AssetBarsPayload | null;
  limit?: number;
}) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const [interval, setInterval] = useState<Interval>(initialData?.interval ?? "1d");
  const [lowerTab, setLowerTab] = useState<LowerTab>("kdj");
  const [showBoll, setShowBoll] = useState(false);
  const [payload, setPayload] = useState<AssetBarsPayload | null>(initialData ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setInterval(initialData?.interval ?? "1d");
    setPayload(initialData ?? null);
    setError("");
  }, [symbol, initialData]);

  useEffect(() => {
    let cancelled = false;
    async function loadBars() {
      if (initialData && initialData.symbol === symbol && initialData.interval === interval) {
        return;
      }
      setLoading(true);
      setError("");
      try {
        const next = await fetchAssetBars(symbol, interval, limit);
        if (cancelled) return;
        setPayload(next);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? `K线接口不可用：${err.message}` : "K线接口不可用，请稍后重试。");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void loadBars();
    return () => {
      cancelled = true;
    };
  }, [symbol, interval, limit, initialData]);

  const hasBars = useMemo(() => (payload?.bars?.length ?? 0) > 0, [payload]);

  useEffect(() => {
    if (!chartRef.current || !payload || !payload.bars.length) return;
    const currentPayload = payload;

    let disposed = false;
    let instance: { setOption: (option: object, notMerge?: boolean) => void; resize: () => void; dispose: () => void } | null = null;
    let onResize: (() => void) | null = null;

    async function renderChart() {
      const echarts = await import("echarts");
      if (disposed || !chartRef.current) return;

      instance = echarts.init(chartRef.current);
      instance.setOption(buildChartOption(currentPayload, showBoll, lowerTab), true);
      onResize = () => instance?.resize();
      window.addEventListener("resize", onResize);
    }

    void renderChart();
    return () => {
      disposed = true;
      if (onResize) {
        window.removeEventListener("resize", onResize);
      }
      instance?.dispose();
    };
  }, [payload, showBoll, lowerTab]);

  return (
    <div className="ths-kline-card">
      <div className="ths-kline-toolbar">
        <div className="ths-kline-tabs">
          {INTERVAL_TABS.map((tab) => (
            <button
              type="button"
              key={tab.value}
              className={interval === tab.value ? "active" : ""}
              onClick={() => setInterval(tab.value)}
              disabled={loading}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="ths-kline-tabs secondary">
          <button type="button" className={showBoll ? "active" : ""} onClick={() => setShowBoll((value) => !value)}>
            BOLL
          </button>
          <button type="button" className={lowerTab === "kdj" ? "active" : ""} onClick={() => setLowerTab("kdj")}>
            KDJ
          </button>
          <button type="button" className={lowerTab === "rsi" ? "active" : ""} onClick={() => setLowerTab("rsi")}>
            RSI
          </button>
        </div>
      </div>

      {error ? <div className="ths-kline-error">{error}</div> : null}
      {loading ? <div className="ths-kline-hint">K线数据加载中…</div> : null}
      {!hasBars && !loading && !error ? <div className="empty-panel">暂无K线数据。</div> : null}
      <div ref={chartRef} className={`ths-kline-canvas ${hasBars ? "" : "hidden"}`} />
    </div>
  );
}
