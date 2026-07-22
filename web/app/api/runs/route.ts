import { NextResponse } from "next/server";
import { listRuns, startRun, TASKS } from "@/lib/runs";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ tasks: TASKS, runs: listRuns() });
}

export async function POST(req: Request) {
  const { taskId } = (await req.json().catch(() => ({}))) as { taskId?: string };
  if (!taskId) return NextResponse.json({ error: "taskId required" }, { status: 400 });
  try {
    const run = startRun(taskId);
    return NextResponse.json({ ok: true, id: run.id });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 409 });
  }
}
