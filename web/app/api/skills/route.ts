import { NextResponse } from "next/server";
import { listSkills, listWorkflows, installSkill, uninstallSkill, readSkillDoc } from "@/lib/skills";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const doc = url.searchParams.get("doc");
  const name = url.searchParams.get("name");
  if (doc && name) {
    try {
      return NextResponse.json({ content: readSkillDoc(name, doc) });
    } catch {
      return NextResponse.json({ error: "not found" }, { status: 404 });
    }
  }
  return NextResponse.json({ skills: listSkills(), workflows: listWorkflows() });
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const { action, name } = body as { action?: string; name?: string };
  if (!name || !/^[\w-]+$/.test(name)) return NextResponse.json({ error: "bad name" }, { status: 400 });
  try {
    if (action === "install") installSkill(name);
    else if (action === "uninstall") uninstallSkill(name);
    else return NextResponse.json({ error: "bad action" }, { status: 400 });
    return NextResponse.json({ ok: true, skills: listSkills() });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
