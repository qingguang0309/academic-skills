import { NextResponse } from "next/server";
import { getRun } from "@/lib/runs";

export const dynamic = "force-dynamic";

export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const after = Number(new URL(req.url).searchParams.get("after") ?? "0");
  const run = getRun(id, Number.isFinite(after) ? after : 0);
  if (!run) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json(run);
}
