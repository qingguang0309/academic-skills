"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Card, Badge, Modal, PageHead, fmtSize, fmtTime } from "@/components/ui";

type Artifact = {
  rel: string; name: string; group: string; ext: string;
  size: number; mtime: number; previewable: "image" | "pdf" | "none"; sibling?: string;
};

const EXT_LABEL: Record<string, string> = { ".png": "PNG", ".jpg": "JPG", ".jpeg": "JPG", ".svg": "SVG", ".pdf": "PDF", ".pptx": "PPTX" };

function ResourcesInner() {
  const params = useSearchParams();
  const [arts, setArts] = useState<Artifact[]>([]);
  const [filter, setFilter] = useState<string>("全部");
  const [focus, setFocus] = useState<Artifact | null>(null);

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

  const groups = useMemo(() => ["全部", ...new Set(arts.map((a) => a.group.split("/")[0]))], [arts]);
  const shown = filter === "全部" ? arts : arts.filter((a) => a.group.split("/")[0] === filter);

  const fileUrl = (rel: string) => `/api/file?path=${encodeURIComponent(rel)}`;

  return (
    <div className="px-10 py-9 max-w-6xl rise">
      <PageHead
        kicker="RESOURCES"
        title="资源库"
        sub="examples 目录下的全部产物:图、PDF、演示文稿。点击卡片预览,PPTX 通过同名 PDF 预览、原文件可下载。"
        right={
          <div className="flex gap-1.5">
            {groups.map((g) => (
              <button
                key={g}
                onClick={() => setFilter(g)}
                className={
                  "rounded-full px-3 py-1.5 text-[12px] font-medium transition-colors " +
                  (filter === g ? "bg-clay text-white" : "bg-panel border border-line text-ink2 hover:bg-panel2")
                }
              >
                {g}
              </button>
            ))}
          </div>
        }
      />

      <div className="grid grid-cols-4 gap-4">
        {shown.map((a) => (
          <Card key={a.rel} onClick={() => setFocus(a)} className="overflow-hidden">
            <div className="aspect-[4/3] bg-panel2 grid place-items-center overflow-hidden">
              {a.previewable === "image" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={fileUrl(a.rel)} alt={a.name} loading="lazy" className="h-full w-full object-cover" />
              ) : a.previewable === "pdf" || a.sibling ? (
                <div className="text-center">
                  <div className="font-display text-[26px] text-clay-deep">A4</div>
                  <div className="text-[11px] text-faint mt-1">{EXT_LABEL[a.ext]} 文档</div>
                </div>
              ) : (
                <div className="text-center">
                  <div className="font-display text-[26px] text-clay-deep">16:9</div>
                  <div className="text-[11px] text-faint mt-1">演示文稿</div>
                </div>
              )}
            </div>
            <div className="px-3 py-2.5">
              <div className="flex items-center gap-2">
                <span className="text-[12.5px] font-medium truncate flex-1">{a.name}</span>
                <Badge>{EXT_LABEL[a.ext] ?? a.ext}</Badge>
              </div>
              <div className="text-[11px] text-faint mt-1 truncate">{a.group} · {fmtSize(a.size)} · {fmtTime(a.mtime)}</div>
            </div>
          </Card>
        ))}
      </div>
      {shown.length === 0 && <div className="text-center text-faint text-sm py-16">该分组暂无产物</div>}

      <Modal open={!!focus} onClose={() => setFocus(null)} wide>
        {focus && (
          <>
            <div className="flex items-center gap-3 px-5 py-3.5 border-b border-line">
              <span className="font-medium text-[14px] truncate">{focus.name}</span>
              <span className="text-[11.5px] text-faint truncate flex-1">{focus.rel}</span>
              <a
                className="text-[12.5px] font-medium text-clay-deep hover:underline"
                href={`${fileUrl(focus.rel)}&dl=1`}
              >
                下载
              </a>
              {focus.sibling && (
                <span className="text-[11.5px] text-faint">(预览为同名 PDF)</span>
              )}
              <button onClick={() => setFocus(null)} className="text-faint hover:text-ink text-[18px] leading-none px-1">×</button>
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
