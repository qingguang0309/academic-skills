"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { IconOverview, IconRuns, IconResources, IconSkills } from "@/components/icons";

const ITEMS = [
  { href: "/", label: "概览", Icon: IconOverview },
  { href: "/runs", label: "运行", Icon: IconRuns },
  { href: "/resources", label: "资源", Icon: IconResources },
  { href: "/skills", label: "技能", Icon: IconSkills },
];

export function Nav({ collapsed = false }: { collapsed?: boolean }) {
  const path = usePathname();
  return (
    <nav className={"mt-2 space-y-0.5 " + (collapsed ? "px-2.5" : "px-3")}>
      {ITEMS.map(({ href, label, Icon }) => {
        const active = href === "/" ? path === "/" : path.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            title={collapsed ? label : undefined}
            className={
              "flex items-center rounded-lg py-2 text-[13.5px] transition-colors " +
              (collapsed ? "justify-center px-0 " : "gap-2.5 px-3 ") +
              (active
                ? "bg-clay-wash text-clay-deep font-medium"
                : "text-ink2 hover:bg-panel2 hover:text-ink")
            }
          >
            <Icon size={16} className={active ? "text-clay" : "text-faint"} />
            {!collapsed && label}
          </Link>
        );
      })}
    </nav>
  );
}
