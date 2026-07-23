"use client";
import { useEffect } from "react";
import { Logo } from "./icons";

export function PageHead({ kicker, title, sub, right }: {
  kicker?: string; title: string; sub?: string; right?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between sm:gap-6 mb-7 md:mb-9">
      <div>
        {kicker && (
          <div className="flex items-center gap-2 mb-2.5">
            <Logo size={11} className="text-gold" />
            <span className="text-[11.5px] tracking-[0.18em] text-clay-deep font-medium">{kicker}</span>
          </div>
        )}
        <h1 className="font-display text-[25px] md:text-[30px] leading-snug tracking-tight">{title}</h1>
        {sub && <p className="text-[13.5px] text-ink2 mt-2 max-w-2xl leading-relaxed">{sub}</p>}
      </div>
      {right && <div className="sm:shrink-0">{right}</div>}
    </div>
  );
}

/** 区块标题:星标母题 + 衬线标题 + 弱化副注 */
export function SectionTitle({ title, note, right, className = "" }: {
  title: string; note?: string; right?: React.ReactNode; className?: string;
}) {
  return (
    <div className={"flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-3.5 " + className}>
      <span className="inline-flex items-center gap-2">
        <Logo size={10} className="text-gold translate-y-[-1px]" />
        <h2 className="font-display text-[19px] tracking-tight">{title}</h2>
      </span>
      {note && <span className="text-[11.5px] text-faint">{note}</span>}
      {right && <span className="ml-auto">{right}</span>}
    </div>
  );
}

/** 空态:淡星标 + 一句话 */
export function EmptyState({ title, hint, className = "" }: {
  title: string; hint?: string; className?: string;
}) {
  return (
    <div className={"flex flex-col items-center justify-center text-center py-12 " + className}>
      <Logo size={30} className="text-line" />
      <div className="text-[13px] text-ink2 mt-3">{title}</div>
      {hint && <div className="text-[12px] text-faint mt-1">{hint}</div>}
    </div>
  );
}

export function Card({ children, className = "", onClick }: {
  children: React.ReactNode; className?: string; onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={
        "rounded-2xl border border-line bg-panel shadow-[0_1px_2px_rgba(20,20,19,0.04),0_2px_8px_rgba(20,20,19,0.03)] " +
        (onClick
          ? "cursor-pointer transition-all duration-200 hover:shadow-[0_12px_28px_rgba(20,20,19,0.09)] hover:-translate-y-[2px] hover:border-[#d9d3c3] "
          : "") +
        className
      }
    >
      {children}
    </div>
  );
}

export function Badge({ tone = "neutral", children }: {
  tone?: "neutral" | "clay" | "moss" | "rust" | "running"; children: React.ReactNode;
}) {
  const cls = {
    neutral: "bg-panel2 text-ink2",
    clay: "bg-clay-wash text-clay-deep",
    moss: "bg-moss-wash text-moss",
    rust: "bg-rust-wash text-rust",
    running: "bg-clay-wash text-clay-deep",
  }[tone];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11.5px] font-medium ${cls}`}>
      {tone === "running" && <span className="h-1.5 w-1.5 rounded-full bg-clay breathe" />}
      {children}
    </span>
  );
}

export function Btn({ children, onClick, tone = "ghost", disabled, small }: {
  children: React.ReactNode; onClick?: () => void;
  tone?: "primary" | "ghost" | "danger"; disabled?: boolean; small?: boolean;
}) {
  const base = small ? "px-3.5 py-1.5 text-[12.5px]" : "px-5 py-2 text-[13.5px]";
  const cls = {
    primary: "bg-clay text-white hover:bg-clay-deep shadow-[0_1px_2px_rgba(180,85,45,0.35)]",
    ghost: "border border-line bg-panel text-ink hover:bg-panel2 hover:border-faint/60",
    danger: "border border-line bg-panel text-rust hover:bg-rust-wash hover:border-rust/30",
  }[tone];
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-full font-medium transition-all duration-150 active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100 ${base} ${cls}`}
    >
      {children}
    </button>
  );
}

export function Modal({ open, onClose, children, wide }: {
  open: boolean; onClose: () => void; children: React.ReactNode; wide?: boolean;
}) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[rgba(20,20,19,0.42)] backdrop-blur-[2px] p-4 md:p-6" onClick={onClose}>
      <div
        className={`rise rounded-2xl bg-page border border-line shadow-[0_24px_64px_rgba(20,20,19,0.28)] overflow-hidden ${wide ? "w-[min(1080px,94vw)]" : "w-[min(760px,92vw)]"} max-h-[88vh] flex flex-col`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}

export function fmtSize(n: number): string {
  if (n > 1 << 20) return (n / (1 << 20)).toFixed(1) + " MB";
  if (n > 1 << 10) return (n / (1 << 10)).toFixed(0) + " KB";
  return n + " B";
}
export function fmtTime(t: number): string {
  const d = new Date(t);
  const pad = (x: number) => String(x).padStart(2, "0");
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
export function fmtDur(ms: number): string {
  return ms < 60_000 ? (ms / 1000).toFixed(1) + "s" : Math.floor(ms / 60_000) + "m" + Math.round((ms % 60_000) / 1000) + "s";
}

/** 极简 Markdown 渲染(标题/加粗/行内码/列表/表格/分隔线),够看 SKILL.md */
export function Md({ src }: { src: string }) {
  const body = src.replace(/^---\n[\s\S]*?\n---\n/, "");
  const lines = body.split("\n");
  const out: React.ReactNode[] = [];
  let i = 0, key = 0;
  const inline = (s: string) => {
    const parts: React.ReactNode[] = [];
    let rest = s, k = 0;
    const re = /(\*\*([^*]+)\*\*)|(`([^`]+)`)/;
    while (rest) {
      const m = rest.match(re);
      if (!m || m.index === undefined) { parts.push(rest); break; }
      if (m.index > 0) parts.push(rest.slice(0, m.index));
      if (m[2]) parts.push(<strong key={k++} className="font-semibold text-ink">{m[2]}</strong>);
      else parts.push(<code key={k++} className="rounded bg-panel2 px-1 py-0.5 text-[0.9em] font-[family-name:var(--font-mono)]">{m[4]}</code>);
      rest = rest.slice(m.index + m[0].length);
    }
    return parts;
  };
  while (i < lines.length) {
    const ln = lines[i];
    if (ln.startsWith("```")) {
      const buf: string[] = []; i++;
      while (i < lines.length && !lines[i].startsWith("```")) buf.push(lines[i++]);
      i++;
      out.push(<pre key={key++} className="my-3 rounded-xl bg-[#2b2823] text-[#e8e5dd] p-4 text-[12px] leading-relaxed overflow-x-auto">{buf.join("\n")}</pre>);
      continue;
    }
    if (/^#{1,4} /.test(ln)) {
      const lvl = (ln.match(/^#+/) as RegExpMatchArray)[0].length;
      const txt = ln.replace(/^#+ /, "");
      const cls = lvl <= 2 ? "font-display text-[19px] mt-6 mb-2" : "text-[15px] font-semibold mt-5 mb-1.5";
      out.push(<div key={key++} className={cls}>{inline(txt)}</div>);
      i++; continue;
    }
    if (/^\s*[-*] /.test(ln)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*] /.test(lines[i])) items.push(lines[i++].replace(/^\s*[-*] /, ""));
      out.push(
        <ul key={key++} className="my-2 space-y-1.5">
          {items.map((it, j) => (
            <li key={j} className="flex gap-2 text-[13.5px] leading-relaxed text-ink2">
              <span className="mt-[8px] h-1.5 w-1.5 shrink-0 bg-gold" />
              <span>{inline(it)}</span>
            </li>
          ))}
        </ul>
      );
      continue;
    }
    if (/^\|/.test(ln)) {
      const rows: string[][] = [];
      while (i < lines.length && /^\|/.test(lines[i])) {
        const cells = lines[i].split("|").slice(1, -1).map((c) => c.trim());
        if (!cells.every((c) => /^:?-+:?$/.test(c))) rows.push(cells);
        i++;
      }
      out.push(
        <div key={key++} className="my-3 overflow-x-auto">
          <table className="w-full text-[12.5px]">
            <thead><tr className="border-t-2 border-b border-ink/60 text-left">{rows[0]?.map((c, j) => <th key={j} className="py-1.5 pr-4 font-semibold">{inline(c)}</th>)}</tr></thead>
            <tbody>
              {rows.slice(1).map((r, ri) => (
                <tr key={ri} className={"border-b " + (ri === rows.length - 2 ? "border-ink/60" : "border-line")}>
                  {r.map((c, j) => <td key={j} className="py-1.5 pr-4 text-ink2 align-top">{inline(c)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }
    if (/^---+$/.test(ln.trim())) { out.push(<hr key={key++} className="my-4 border-line" />); i++; continue; }
    if (ln.trim() === "") { i++; continue; }
    const buf: string[] = [];
    while (i < lines.length && lines[i].trim() !== "" && !/^(#|```|\||\s*[-*] |---)/.test(lines[i])) buf.push(lines[i++]);
    out.push(<p key={key++} className="my-2 text-[13.5px] leading-relaxed text-ink2">{inline(buf.join(" "))}</p>);
  }
  return <div>{out}</div>;
}
