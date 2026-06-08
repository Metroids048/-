import type { Metadata } from "next";
import { AppShell } from "../components/AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "投研智体工作台",
  description: "市场解释、标的研究、K线、风险卡、策略实验、知识库、问AI和预警复盘的一体化投研工作台。"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
