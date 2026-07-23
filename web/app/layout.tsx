import type { Metadata } from "next";
import { Archivo, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { Shell } from "./shell";

// Claude 系字体近似:Tiempos → Source Serif 4,Styrene → Archivo(构建时下载自托管)
const serif = Source_Serif_4({ subsets: ["latin"], variable: "--gf-serif", display: "swap" });
const sans = Archivo({ subsets: ["latin"], variable: "--gf-sans", display: "swap" });

export const metadata: Metadata = {
  title: "academic-skills 工作台",
  description: "学术技能合集:生成、进度、资源与技能管理",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${serif.variable} ${sans.variable}`}>
      <body className="min-h-screen">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
