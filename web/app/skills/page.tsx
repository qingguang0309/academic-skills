"use client";
import { useCallback, useEffect, useState } from "react";
import { Card, Badge, Btn, Modal, PageHead, SectionTitle, Md } from "@/components/ui";
import { IconDoc, IconGear } from "@/components/icons";

type Skill = {
  name: string; description: string; files: number;
  scripts: string[]; references: string[]; installed: boolean; updatable: boolean;
};
type Workflow = { name: string; description: string; dir: string };

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [doc, setDoc] = useState<{ title: string; content: string } | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const refresh = useCallback(() => {
    fetch("/api/skills").then((r) => r.json()).then((d) => { setSkills(d.skills); setWorkflows(d.workflows); });
  }, []);
  useEffect(() => { refresh(); }, [refresh]);

  const act = async (action: "install" | "uninstall", name: string) => {
    if (action === "uninstall" && !confirm(`从 ~/.claude/skills 移除 ${name}?(仓库内的源不受影响)`)) return;
    setBusy(name);
    const r = await fetch("/api/skills", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, name }),
    });
    const d = await r.json();
    setBusy(null);
    if (!r.ok) { setToast(d.error ?? "操作失败"); return; }
    setSkills(d.skills);
    setToast(action === "install" ? `${name} 已安装/更新到 ~/.claude/skills` : `${name} 已移除`);
    setTimeout(() => setToast(null), 2600);
  };

  const openDoc = async (name: string, file: string) => {
    const r = await fetch(`/api/skills?name=${name}&doc=${encodeURIComponent(file)}`);
    const d = await r.json();
    if (r.ok) setDoc({ title: `${name} / ${file}`, content: d.content });
  };

  return (
    <div className="px-5 py-6 md:px-10 md:py-9 max-w-6xl rise">
      <PageHead
        kicker="SKILLS"
        title="技能管理"
        sub="仓库内的 Agent Skills:安装或更新到 ~/.claude/skills 供 Claude Code 全局使用,并可直接查看技能文档与规范。"
      />
      {toast && (
        <div className="fixed bottom-6 right-6 z-40 rise rounded-xl bg-ink text-paper px-4 py-2.5 text-[13px] shadow-lg">{toast}</div>
      )}

      <div className="space-y-4 mb-10">
        {skills.map((s) => (
          <Card key={s.name} className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1.5">
                  <span className="font-display text-[18px]">{s.name}</span>
                  {s.installed ? (
                    <Badge tone={s.updatable ? "clay" : "moss"}>{s.updatable ? "仓库有更新" : "已安装"}</Badge>
                  ) : (
                    <Badge>未安装</Badge>
                  )}
                  <span className="text-[11.5px] text-faint">{s.files} 个文件</span>
                </div>
                <p className="text-[13px] text-ink2 leading-relaxed mb-3">{s.description}</p>
                <div className="flex flex-wrap items-center gap-1.5">
                  <button onClick={() => openDoc(s.name, "SKILL.md")}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-panel2 px-2.5 py-1 text-[11.5px] font-medium hover:bg-clay-wash hover:text-clay-deep transition-colors">
                    <IconDoc size={12} /> SKILL.md
                  </button>
                  {s.references.map((f) => (
                    <button key={f} onClick={() => openDoc(s.name, `references/${f}`)}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-panel2 px-2.5 py-1 text-[11.5px] text-ink2 hover:bg-clay-wash hover:text-clay-deep transition-colors">
                      <IconDoc size={12} /> {f}
                    </button>
                  ))}
                  {s.scripts.map((f) => (
                    <span key={f} className="inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 py-1 text-[11.5px] text-faint">
                      <IconGear size={11} /> {f}
                    </span>
                  ))}
                </div>
              </div>
              <div className="sm:shrink-0 flex flex-row sm:flex-col gap-2 w-full sm:w-36">
                <Btn tone="primary" small disabled={busy === s.name} onClick={() => act("install", s.name)}>
                  {busy === s.name ? "处理中…" : s.installed ? (s.updatable ? "更新" : "重新安装") : "安装"}
                </Btn>
                {s.installed && (
                  <Btn tone="danger" small disabled={busy === s.name} onClick={() => act("uninstall", s.name)}>
                    移除
                  </Btn>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      <SectionTitle title="内置工作流" />
      <p className="text-[12.5px] text-ink2 mb-4 max-w-2xl">
        paperflow 与 figflow 不是 Agent Skill,而是随仓库分发的流水线/引擎,直接在仓库目录内运行;可在运行中心体验端到端示例。
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {workflows.map((w) => (
          <Card key={w.name} className="p-5">
            <div className="font-semibold text-[14.5px] mb-1.5">{w.name}/</div>
            <p className="text-[12.5px] text-ink2 leading-relaxed">{w.description}</p>
          </Card>
        ))}
      </div>

      <Modal open={!!doc} onClose={() => setDoc(null)} wide>
        {doc && (
          <>
            <div className="flex items-center gap-3 px-5 py-3.5 border-b border-line">
              <span className="font-medium text-[14px] font-[family-name:var(--font-mono)]">{doc.title}</span>
              <button onClick={() => setDoc(null)} className="ml-auto text-faint hover:text-ink text-[18px] leading-none px-1">×</button>
            </div>
            <div className="overflow-y-auto px-7 py-5">
              <Md src={doc.content} />
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}
