"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { ApiStatus } from "./ApiStatus";

const navItems: { href: Route; label: string; detail: string }[] = [
  { href: "/quant", label: "量化模拟", detail: "榜单 / 模拟盘" },
  { href: "/market", label: "市场", detail: "指数 / 行业" },
  { href: "/assets", label: "标的", detail: "股票 / ETF" },
  { href: "/strategy-lab", label: "策略", detail: "验证投资想法" },
  { href: "/knowledge", label: "知识库", detail: "概念和案例" },
  { href: "/ai", label: "问 AI", detail: "证据问答" },
  { href: "/alerts", label: "预警复盘", detail: "观察列表" }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="side-nav" aria-label="Alpha模拟场导航">
        <Link className="brand" href="/">
          <span>A</span>
          <div>
            <strong>Alpha模拟场</strong>
            <small>虚拟资金策略模拟场</small>
          </div>
        </Link>

        <nav>
          {navItems.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link className={active ? "active" : ""} href={item.href} key={item.href}>
                <b>{item.label}</b>
                <small>{item.detail}</small>
              </Link>
            );
          })}
        </nav>

        <ApiStatus />

        <div className="compliance-box">
          <strong>合规边界</strong>
          <p>只做投研解释、风险观察、策略模拟和学习复盘；不荐股、不带单、不接真实资金、不自动交易。</p>
        </div>
      </aside>
      <main className="main-workspace">{children}</main>
    </div>
  );
}
