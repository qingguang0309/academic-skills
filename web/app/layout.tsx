import type { Metadata } from "next";
import { Archivo, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { Nav } from "./nav";
import { Logo } from "@/components/icons";

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
        <div className="flex min-h-screen">
          <aside className="w-60 shrink-0 border-r border-line bg-paper sticky top-0 h-screen flex flex-col">
            <div className="px-5 pt-6 pb-4">
              <div className="flex items-center gap-2.5">
                <Logo size={30} className="text-clay shrink-0" />
                <div>
                  <div className="font-display text-[15px] leading-tight tracking-tight">academic-skills</div>
                  <div className="text-[11px] text-faint leading-tight mt-0.5">科研技能工作台</div>
                </div>
              </div>
            </div>
            <Nav />
            <div className="mt-auto px-5 py-4 border-t border-line">
              <p className="text-[11px] text-faint leading-relaxed">
                从数据到投稿,再到上台汇报
                <br />
                质量做成机制,而非叮嘱
              </p>
            </div>
          </aside>
          <main className="flex-1 min-w-0 bg-page">{children}</main>
        </div>
      </body>
    </html>
  );
}
