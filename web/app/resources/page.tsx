"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Card, Badge, Modal, PageHead, fmtSize, fmtTime } from "@/components/ui";
import { IconDoc, IconDownload, IconResources } from "@/components/icons";

type Artifact = {
  rel: string; name: string; topGroup: string; subPath: string; ext: string;
  size: number; mtime: number; kind: "image" | "pdf" | "deck";
  tier: "final" | "material";
  previewable: "image" | "pdf" | "none"; sibling?: string;
};

const EXT_LABEL: Record<string, string> = { ".png": "PNG", ".jpg": "JPG", ".jpeg": "JPG", ".svg": "SVG", ".pdf": "PDF", ".pptx": "PPTX" };
const KINDS = [
  { id: "all", label: "全部" },
  { id: "image", label: "图像" },
  { id: "pdf", label: "文档" },
  { id: "deck", label: "演示文稿" },
] as const;

/** 分区元信息:标题与一句话说明(未登记的目录回退为目录名) */
const GROUP_META: Record<string, { label: string; desc: string; order: number }> = {
  "bse-eds-report": { label: "BSE–EDS 研究计划", desc: "paperflow 再生成的研究报告 + paper-slides 生成的基金汇报", order: 1 },
  "figflow-demo": { label: "figflow · 架构大图", desc: "并行面板与确定性锚点合成的四阶段架构图", order: 2 },
  "paper-figures-demo": { label: "paper-figures · OER 组图", desc: "按期刊栏宽的出版级四联图演示", order: 3 },
  "paperflow-demo": { label: "paperflow · OER 论文", desc: "论文流水线端到端产物(LaTeX → PDF)", order: 4 },
};

function ArtCard({ a, onOpen }: { a: Artifact; onOpen: () => void }) {
  const fileUrl = `/api/file?path=${encodeURIComponent(a.rel)}`;
  return (
    <Card onClick={onOpen} className="overflow-hidden">
      <div className="aspect-[4/3] bg-panel2 grid place-items-center overflow-hidden">
        {a.previewable === "image" ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={fileUrl} alt={a.name} loading="lazy" className="h-full w-full object-cover" />
        ) : a.kind === "pdf" || a.sibling ? (
          <div className="text-center text-clay-deep">
            <IconDoc size={30} className="mx-auto" />
            <div className="text-[11px] text-faint mt-2">{EXT_LABEL[a.ext]} 文档</div>
          </div>
        ) : (
          <div className="text-center text-clay-deep">
            <IconResources size={30} className="mx-auto" />
            <div className="text-[11px] text-faint mt-2">演示文稿</div>
          </div>
        )}
      </div>
      <div className="px-3 py-2.5">
        <div className="flex items-center gap-2">
          <span className="text-[12.5px] font-medium truncate flex-1">{a.name}</span>
          {a.tier === "material" && <Badge>素材</Badge>}
          <Badge tone={a.kind === "image" ? "neutral" : "clay"}>{EXT_LABEL[a.ext] ?? a.ext}</Badge>
        </div>
        <div className="text-[11px] text-faint mt-1 truncate">
          {a.subPath ? a.subPath + " · " : ""}{fmtSize(a.size)} · {fmtTime(a.mtime)}
        </div>
      </div>
    </Card>
  );
}

function ResourcesInner() {
  const params = useSearchParams();
  const [arts, setArts] = useState<Artifact[]>([]);
  const [kind, setKind] = useState<string>("all");
  const [q, setQ] = useState("");
  const [focus, setFocus] = useState<Artifact | null>(null);
  const [openMaterials, setOpenMaterials] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch("/api/artifacts").then((r) => r.json()).then((d) => {
      setArts(d.artifacts);
      const f = params.get("focus");
      if (f) {
        const hit = (d.artifacts as Artifact[]).find((a) => a.rel === f);
        if (hit) setFocus(hit);
      }
    });
  }, [params]);

  const searching = q.trim() !== "";
  const filtered = useMemo(() => {
    const kw = q.trim().toLowerCase();
    return arts.filter((a) =>
      (kind === "all" || a.kind === kind) &&
      (!kw || a.rel.toLowerCase().includes(kw)));
  }, [arts, kind, q]);

  const sections = useMemo(() => {
    const by = new Map<string, Artifact[]>();
    for (const a of filtered) {
      if (!by.has(a.topGroup)) by.set(a.topGroup, []);
      by.get(a.topGroup)!.push(a);
    }
    return [...by.entries()]
      .sort((x, y) => (GROUP_META[x[0]]?.order ?? 99) - (GROUP_META[y[0]]?.order ?? 99))
      .map(([g, list]) => ({
        group: g,
        meta: GROUP_META[g] ?? { label: g, desc: "", order: 99 },
        finals: list.filter((a) => a.tier === "final"),
        materials: list.filter((a) => a.tier === "material"),
      }));
  }, [filtered]);

  const toggleMaterials = (g: string) =>
    setOpenMaterials((s) => {
      const n = new Set(s);
      if (n.has(g)) n.delete(g); else n.add(g);
      return n;
    });

  const fileUrl = (rel: string) => `/api/file?path=${encodeURIComponent(rel)}`;

  return (
    <div className="px-5 py-6 md:px-10 md:py-9 max-w-6xl rise">
      <PageHead
        kicker="RESOURCES"
        title="资源库"
        sub="examples 目录下的全部产物,按项目分区;过程素材默认折叠。点击卡片预览,PPTX 通过同名 PDF 预览、原文件可下载。"
        right={
          <div className="flex flex-col items-stretch sm:items-end gap-2">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="搜索文件名或路径…"
              className="w-full sm:w-60 rounded-lg border border-line bg-panel px-3 py-1.5 text-[12.5px] placeholder:text-faint focus:outline-none focus:border-clay/50"
            />
            <div className="flex flex-wrap gap-1.5">
              {KINDS.map((k) => (
                <button
                  key={k.id}
                  onClick={() => setKind(k.id)}
                  className={
                    "rounded-full px-3 py-1 text-[12px] font-medium transition-colors " +
                    (kind === k.id ? "bg-clay text-white" : "bg-panel border border-line text-ink2 hover:bg-panel2")
                  }
                >
                  {k.label}
                </button>
              ))}
            </div>
          </div>
        }
      />

      <div className="space-y-9">
        {sections.map(({ group, meta, finals, materials }) => (
          <section key={group}>
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-3.5">
              <h2 className="font-display text-[18px]">{meta.label}</h2>
              <span className="text-[11.5px] text-faint">
                {finals.length + materials.length} 个文件 · examples/{group}
              </span>
              {meta.desc && <span className="w-full sm:w-auto text-[12px] text-ink2">{meta.desc}</span>}
            </div>

            {finals.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
                {finals.map((a) => <ArtCard key={a.rel} a={a} onOpen={() => setFocus(a)} />)}
              </div>
            ) : (
              <div className="text-[12.5px] text-faint">本区无匹配的成品文件</div>
            )}

            {materials.length > 0 && (
              <div className="mt-3.5">
                {(searching || openMaterials.has(group)) ? (
                  <>
                    {!searching && (
                      <button onClick={() => toggleMaterials(group)}
                        className="mb-3 text-[12.5px] text-clay-deep hover:underline">
                        收起过程素材 ▴
                      </button>
                    )}
                    <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4 opacity-90">
                      {materials.map((a) => <ArtCard key={a.rel} a={a} onOpen={() => setFocus(a)} />)}
                    </div>
                  </>
                ) : (
                  <button onClick={() => toggleMaterials(group)}
                    className="text-[12.5px] text-ink2 hover:text-clay-deep transition-colors">
                    展开 {materials.length} 个过程素材(面板 / 图素材)▾
                  </button>
                )}
              </div>
            )}
          </section>
        ))}
      </div>
      {sections.length === 0 && (
        <div className="text-center text-faint text-sm py-16">没有匹配的文件,换个关键词或类型试试</div>
      )}

      <Modal open={!!focus} onClose={() => setFocus(null)} wide>
        {focus && (
          <>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-5 py-3.5 border-b border-line">
              <span className="font-medium text-[14px] truncate">{focus.name}</span>
              <span className="hidden sm:inline text-[11.5px] text-faint truncate flex-1">
                {focus.rel} · {fmtSize(focus.size)} · {fmtTime(focus.mtime)}
              </span>
              <a
                className="inline-flex items-center gap-1 text-[12.5px] font-medium text-clay-deep hover:underline"
                href={`${fileUrl(focus.rel)}&dl=1`}
              >
                <IconDownload size={13} /> 下载
              </a>
              {focus.sibling && <span className="text-[11.5px] text-faint">(预览为同名 PDF)</span>}
              <button onClick={() => setFocus(null)} className="ml-auto sm:ml-0 text-faint hover:text-ink text-[18px] leading-none px-1">×</button>
            </div>
            <div className="bg-panel2/50 overflow-auto grid place-items-center min-h-[420px]">
              {focus.previewable === "image" && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={fileUrl(focus.rel)} alt={focus.name} className="max-h-[74vh] w-auto" />
              )}
              {(focus.previewable === "pdf" || focus.sibling) && (
                <iframe
                  src={fileUrl(focus.previewable === "pdf" ? focus.rel : focus.sibling!)}
                  className="w-full h-[74vh] border-0"
                  title={focus.name}
                />
              )}
              {focus.previewable === "none" && !focus.sibling && (
                <div className="text-[13px] text-faint py-20">此格式无法直接预览,请下载后查看</div>
              )}
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}

export default function ResourcesPage() {
  return (
    <Suspense fallback={<div className="p-10 text-faint text-sm">加载中…</div>}>
      <ResourcesInner />
    </Suspense>
  );
}
