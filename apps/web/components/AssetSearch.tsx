"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function AssetSearch({ initialSymbol = "510300", compact = false }: { initialSymbol?: string; compact?: boolean }) {
  const router = useRouter();
  const [symbol, setSymbol] = useState(initialSymbol);

  function submit(event: FormEvent) {
    event.preventDefault();
    const normalized = symbol.trim().toUpperCase();
    if (normalized) {
      router.push(`/assets/${encodeURIComponent(normalized)}`);
    }
  }

  return (
    <form className={compact ? "asset-search compact" : "asset-search"} onSubmit={submit}>
      <label htmlFor="asset-symbol">输入股票 / ETF 代码</label>
      <div>
        <input
          id="asset-symbol"
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
          placeholder="510300 / 159915 / 600000"
        />
        <button type="submit">查看标的</button>
      </div>
    </form>
  );
}
