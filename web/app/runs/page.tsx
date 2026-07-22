"use client";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Card, Badge, Btn, PageHead, fmtTime, fmtDur } from "@/components/ui";

type Task = { id: string; title: string; tool: string; desc: string; script: string; hint?: string; produces: string[] };
type RunMeta = { id: string; taskId: string; title: string; status: "running" | "success" | "failed"; startedAt: number; endedAt?: number };
type RunDetail = RunMeta & { lines: string[]; cursor: number; exitCode?: number; artifacts: { rel: string; mtime: number }[] };

function statusBadge(s: string) {
  return s === "running" ? <Badge tone="running">运行中</Badge>
    : s === "success" ? <Badge tone="moss">成功</Badge>
    : <Badge tone="rust">失败</Badge>;
}

function RunsInner() {
  const params = useSearchParams();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [runs, setRuns] = useState<RunMeta[]>([]);
  const [open, setOpen] = useState<string | null>(params.get("open"));
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const linesRef = useRef<string[]>([]);
  const cursorRef = useRef(0);
  const consoleRef = useRef<HTMLDivElement>(null);
  const focusTask = params.get("task");

  const refresh = useCallback(() => {
    fetch("/api/runs").then((r) => r.json()).then((d) => { setTasks(d.tasks); setRuns(d.runs); });
  }, []);
  useEffect(() => { refresh(); }, [refresh]);

  // 打开某个运行:重置日志游标
  useEffect(() => {
    linesRef.current = []; cursorRef.current = 0; setDetail(null);
  }, [open]);

  // 轮询选中运行的日志
  useEffect(() => {
    if (!open) return;
    let stop = false;
    const tick = async () => {
      const r = await fetch(`/api/runs/${open}?after=${cursorRef.current}`);
      if (r.status === 404) { setErr("运行不存在(dev 服务重启会清空内存记录)"); return; }
      const d: RunDetail = await r.json();
      if (stop) return;
      if (cursorRef.current === 0) linesRef.current = d.lines;
      else linesRef.current = [...linesRef.current, ...d.lines];
      cursorRef.current = d.cursor;
      setDetail({ ...d, lines: linesRef.current });
      const el = consoleRef.current;
      if (el) requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
      if (d.status === "running") setTimeout(tick, 800);
      else refresh();
    };
    tick();
    return () => { stop = true; };
  }, [open, refresh]);

  const start = async (taskId: string) => {
    setErr(null);
    const r = await fetch("/api/runs", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ taskId }) });
    const d = await r.json();
    if (!r.ok) { setErr(d.error ?? "启动失败"); return; }
    setOpen(d.id);
    refresh();
  };

  return (
    <div className="px-10 py-9 max-w-6xl rise">
      <PageHead
        kicker="RUNS"
        title="运行中心"
        sub="预置的示例生成任务(白名单脚本,非任意命令)。启动后实时查看日志与进度,完成后核对产物并跳转预览。"
      />
      {err && (
        <div className="mb-4 rounded-xl border border-line bg-rust-wash text-rust px-4 py-2.5 text-[13px]">{err}</div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-8">
        {tasks.map((t) => {
          const running = runs.some((r) => r.taskId === t.id && r.status === "running");
          const focused = focusTask === t.id;
          return (
            <Card key={t.id} className={"p-5 " + (focused ? "ring-2 ring-clay/40" : "")}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="font-semibold text-[14.5px]">{t.title}</div>
                <Badge tone="clay">{t.tool}</Badge>
              </div>
              <p className="text-[12.5px] text-ink2 leading-relaxed mb-1.5">{t.desc}</p>
              {t.hint && <p className="text-[11.5px] text-faint mb-3">依赖:{t.hint}</p>}
              <div className="flex items-center gap-3">
                <Btn tone="primary" small disabled={running} onClick={() => start(t.id)}>
                  {running ? "运行中…" : "▸ 运行"}
                </Btn>
                <code className="text-[11px] text-faint truncate flex-1">{t.script.split("&&")[0].trim()} …</code>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-2">
          <h2 className="font-display text-[18px] mb-3">运行记录</h2>
          <Card className="divide-y divide-line max-h-[420px] overflow-y-auto">
            {runs.length === 0 && <div className="px-5 py-8 text-center text-[12.5px] text-faint">暂无记录</div>}
            {runs.map((r) => (
              <button
                key={r.id}
                onClick={() => setOpen(r.id)}
                className={"w-full text-left flex items-center gap-3 px-4 py-3 transition-colors " + (open === r.id ? "bg-clay-wash/60" : "hover:bg-panel2")}
              >
                {statusBadge(r.status)}
                <span className="text-[13px] flex-1 truncate">{r.title}</span>
                <span className="text-[11px] text-faint">{fmtTime(r.startedAt)}</span>
              </button>
            ))}
          </Card>
        </div>

        <div className="col-span-3">
          <h2 className="font-display text-[18px] mb-3">日志与产物</h2>
          {!open && (
            <Card className="px-6 py-14 text-center text-[13px] text-faint">
              运行一个任务,或从左侧记录中选择一条查看日志
            </Card>
          )}
          {open && detail && (
            <Card className="overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-line bg-panel2/60">
                {statusBadge(detail.status)}
                <span className="text-[13.5px] font-medium flex-1 truncate">{detail.title}</span>
                <span className="text-[11.5px] text-faint">
                  {detail.endedAt ? `耗时 ${fmtDur(detail.endedAt - detail.startedAt)}` : `已运行 ${fmtDur(Date.now() - detail.startedAt)}`}
                </span>
              </div>
              <div ref={consoleRef} className="console bg-[#2b2823] text-[#d9d5ca] px-4 py-3 h-72 overflow-y-auto">
                {detail.lines.map((l, i) => (
                  <div key={i} className={
                    l.startsWith("$") ? "text-[#e8b98c]" :
                    l.startsWith("[done]") ? "text-[#a9c398]" :
                    l.startsWith("[fail]") || l.startsWith("[error]") ? "text-[#e09a8a]" : ""
                  }>{l}</div>
                ))}
                {detail.status === "running" && <div className="text-[#e8b98c] breathe">▍</div>}
              </div>
              {detail.artifacts.length > 0 && (
                <div className="px-4 py-3 border-t border-line">
                  <div className="text-[11.5px] text-faint mb-2">产物</div>
                  <div className="flex flex-wrap gap-2">
                    {detail.artifacts.map((a) => (
                      <a
                        key={a.rel}
                        href={`/resources?focus=${encodeURIComponent(a.rel)}`}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-panel px-2.5 py-1.5 text-[12px] hover:bg-clay-wash hover:border-clay/40 transition-colors"
                      >
                        <span className={"h-1.5 w-1.5 rounded-full " + (a.mtime >= detail.startedAt - 2000 ? "bg-moss" : "bg-faint")} />
                        {a.rel.split("/").pop()}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}
          {open && !detail && !err && <Card className="px-6 py-14 text-center text-[13px] text-faint">载入日志…</Card>}
        </div>
      </div>
    </div>
  );
}

export default function RunsPage() {
  return (
    <Suspense fallback={<div className="p-10 text-faint text-sm">加载中…</div>}>
      <RunsInner />
    </Suspense>
  );
}
