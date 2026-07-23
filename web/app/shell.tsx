"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Nav } from "./nav";
import { Logo, IconMenu, IconPanel, IconX } from "@/components/icons";

function SideHeader({ collapsed }: { collapsed: boolean }) {
  return (
    <div className={"flex items-center gap-2.5 " + (collapsed ? "justify-center" : "")}>
      <Logo size={30} className="text-clay shrink-0" />
      {!collapsed && (
        <div className="min-w-0">
          <div className="font-display text-[15px] leading-tight tracking-tight truncate">academic-skills</div>
          <div className="text-[11px] text-faint leading-tight mt-0.5 truncate">科研技能工作台</div>
        </div>
      )}
    </div>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const path = usePathname();

  useEffect(() => { setCollapsed(localStorage.getItem("as-sidebar") === "1"); }, []);
  useEffect(() => { setMobileOpen(false); }, [path]);
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && setMobileOpen(false);
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  const toggle = () =>
    setCollapsed((c) => { localStorage.setItem("as-sidebar", c ? "0" : "1"); return !c; });

  return (
    <div className="flex min-h-screen">
      {/* 桌面侧栏(可收缩) */}
      <aside
        className={
          "hidden md:flex shrink-0 border-r border-line bg-paper sticky top-0 h-screen flex-col transition-[width] duration-200 " +
          (collapsed ? "w-[64px]" : "w-60")
        }
      >
        <div className={"pt-6 pb-4 " + (collapsed ? "px-3" : "px-5")}>
          <SideHeader collapsed={collapsed} />
        </div>
        <Nav collapsed={collapsed} />
        <div className={"mt-auto border-t border-line " + (collapsed ? "px-3 py-3" : "px-5 py-4")}>
          {!collapsed && (
            <p className="text-[11px] text-faint leading-relaxed mb-2.5">
              从数据到投稿,再到上台汇报
              <br />
              质量做成机制,而非叮嘱
            </p>
          )}
          <button
            onClick={toggle}
            title={collapsed ? "展开侧栏" : "收起侧栏"}
            className={
              "flex items-center gap-2 rounded-lg text-faint hover:text-ink hover:bg-panel2 transition-colors " +
              (collapsed ? "justify-center w-full py-2" : "px-2 py-1.5 -mx-2")
            }
          >
            <IconPanel size={16} flip={collapsed} />
            {!collapsed && <span className="text-[12px]">收起侧栏</span>}
          </button>
        </div>
      </aside>

      {/* 移动端抽屉 */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden" onClick={() => setMobileOpen(false)}>
          <div className="absolute inset-0 bg-[rgba(20,20,19,0.4)]" />
          <aside
            className="rise absolute left-0 top-0 h-full w-64 bg-paper border-r border-line flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-5 pt-6 pb-4 flex items-center justify-between">
              <SideHeader collapsed={false} />
              <button onClick={() => setMobileOpen(false)} className="text-faint hover:text-ink p-1" aria-label="关闭菜单">
                <IconX size={16} />
              </button>
            </div>
            <Nav collapsed={false} />
            <div className="mt-auto px-5 py-4 border-t border-line">
              <p className="text-[11px] text-faint leading-relaxed">
                从数据到投稿,再到上台汇报
                <br />
                质量做成机制,而非叮嘱
              </p>
            </div>
          </aside>
        </div>
      )}

      <div className="flex-1 min-w-0 bg-page flex flex-col">
        {/* 移动端顶栏 */}
        <header className="md:hidden sticky top-0 z-40 flex items-center gap-3 border-b border-line bg-paper/92 backdrop-blur px-4 h-[52px]">
          <button onClick={() => setMobileOpen(true)} className="text-ink2 hover:text-ink p-1 -ml-1" aria-label="打开菜单">
            <IconMenu size={19} />
          </button>
          <Logo size={22} className="text-clay" />
          <span className="font-display text-[14.5px] tracking-tight">academic-skills</span>
        </header>
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
