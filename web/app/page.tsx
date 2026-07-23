"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, Badge, PageHead, fmtTime } from "@/components/ui";

type Overview = {
  skills: { name: string; description: string; installed: boolean; updatable: boolean; scripts: string[] }[];
  workflows: { name: string; description: string }[];
  runs: { id: string; title: string; status: string; startedAt: number }[];
  tasks: { id: string; title: string; tool: string }[];
  stats: { skills: number; workflows: number; artifacts: number; installed: number };
  latest: { rel: string; name: string; ext: string; group: string; previewable: string; sibling?: string }[];
};

const TOOL_TASK: Record<string, string> = {
  "paper-slides": "slides", "paper-figures": "oer", figflow: "figflow", paperflow: "paperflow",
};

export default function Home() {
  const [data, setData] = useState<Overview | null>(null);
  useEffect(() => {
    fetch("/api/overview").then((r) => r.json()).then(setData);
  }, []);
  if (!data) return <div className="p-10 text-faint text-sm">加载中…</div>;

  const stat = [
    { label: "可用技能", v: data.stats.skills },
    { label: "已装到 ~/.claude", v: data.stats.installed },
    { label: "内置工作流", v: data.stats.workflows },
    { label: "产物文件", v: data.stats.artifacts },
  ];

  return (
    <div className="px-5 py-6 md:px-10 md:py-9 max-w-6xl rise">
      <PageHead
        kicker="ACADEMIC SKILLS"
        title="从数据到投稿,再到上台汇报"
        sub="论文绘图、学术汇报 PPT、论文流水线与多面板大图——每一环都把质量做成机制:组件库、布局引擎、锚点合成与引用核验门。"
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-8">
        {stat.map((s) => (
          <Card key={s.label} className="px-5 py-4">
            <div className="font-display text-[30px] text-clay-deep leading-none">{s.v}</div>
            <div className="text-[12px] text-ink2 mt-2">{s.label}</div>
          </Card>
        ))}
      </div>

      <h2 className="font-display text-[18px] mb-3">技能</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
        {data.skills.map((s) => (
          <Card key={s.name} className="p-5 flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <div className="font-semibold text-[15px]">{s.name}</div>
              {s.installed ? (
                <Badge tone={s.updatable ? "clay" : "moss"}>{s.updatable ? "可更新" : "已安装"}</Badge>
              ) : (
                <Badge>未安装</Badge>
              )}
            </div>
            <p className="text-[12.5px] text-ink2 leading-relaxed line-clamp-3 flex-1">{s.description}</p>
            <div className="flex items-center gap-2 mt-4">
              {TOOL_TASK[s.name] && (
                <Link href={`/runs?task=${TOOL_TASK[s.name]}`} className="text-[12.5px] font-medium text-clay-deep hover:underline">
                  运行示例 →
                </Link>
              )}
              <Link href="/skills" className="text-[12.5px] text-ink2 hover:underline ml-auto">
                管理
              </Link>
            </div>
          </Card>
        ))}
        {data.workflows.map((w) => (
          <Card key={w.name} className="p-5 flex flex-col border-dashed">
            <div className="flex items-center justify-between mb-2">
              <div className="font-semibold text-[15px]">{w.name}</div>
              <Badge>工作流</Badge>
            </div>
            <p className="text-[12.5px] text-ink2 leading-relaxed line-clamp-3 flex-1">{w.description}</p>
            <div className="mt-4">
              {TOOL_TASK[w.name] && (
                <Link href={`/runs?task=${TOOL_TASK[w.name]}`} className="text-[12.5px] font-medium text-clay-deep hover:underline">
                  运行示例 →
                </Link>
              )}
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <div className="xl:col-span-3">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="font-display text-[18px]">最新产物</h2>
            <Link href="/resources" className="text-[12.5px] text-clay-deep hover:underline">全部资源 →</Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {data.latest.filter((a) => a.previewable === "image").slice(0, 8).map((a) => (
              <Link key={a.rel} href={`/resources?focus=${encodeURIComponent(a.rel)}`}>
                <Card className="overflow-hidden">
                  <div className="aspect-[4/3] bg-panel2 overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={`/api/file?path=${encodeURIComponent(a.rel)}`} alt={a.name} className="h-full w-full object-cover" />
                  </div>
                  <div className="px-2.5 py-2">
                    <div className="text-[11.5px] truncate">{a.name}</div>
                    <div className="text-[10.5px] text-faint truncate">{a.group}</div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
        <div className="xl:col-span-2">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="font-display text-[18px]">最近运行</h2>
            <Link href="/runs" className="text-[12.5px] text-clay-deep hover:underline">运行中心 →</Link>
          </div>
          <Card className="divide-y divide-line">
            {data.runs.length === 0 && (
              <div className="px-5 py-8 text-center text-[12.5px] text-faint">
                还没有运行记录
                <div className="mt-1">去运行中心跑一个示例任务试试</div>
              </div>
            )}
            {data.runs.map((r) => (
              <Link key={r.id} href={`/runs?open=${r.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-panel2 transition-colors">
                <Badge tone={r.status === "running" ? "running" : r.status === "success" ? "moss" : "rust"}>
                  {r.status === "running" ? "运行中" : r.status === "success" ? "成功" : "失败"}
                </Badge>
                <span className="text-[13px] flex-1 truncate">{r.title}</span>
                <span className="text-[11.5px] text-faint">{fmtTime(r.startedAt)}</span>
              </Link>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
