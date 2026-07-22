"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/", label: "概览", icon: "◫" },
  { href: "/runs", label: "运行", icon: "▸" },
  { href: "/resources", label: "资源", icon: "❏" },
  { href: "/skills", label: "技能", icon: "✦" },
];

export function Nav() {
  const path = usePathname();
  return (
    <nav className="px-3 mt-2 space-y-0.5">
      {ITEMS.map((it) => {
        const active = it.href === "/" ? path === "/" : path.startsWith(it.href);
        return (
          <Link
            key={it.href}
            href={it.href}
            className={
              "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] transition-colors " +
              (active
                ? "bg-clay-wash text-clay-deep font-medium"
                : "text-ink2 hover:bg-panel2 hover:text-ink")
            }
          >
            <span className={"w-4 text-center " + (active ? "text-clay" : "text-faint")}>{it.icon}</span>
            {it.label}
          </Link>
        );
      })}
    </nav>
  );
}
