import { NextResponse } from "next/server";
import { listSkills, listWorkflows } from "@/lib/skills";
import { listArtifacts } from "@/lib/artifacts";
import { listRuns, TASKS } from "@/lib/runs";

export const dynamic = "force-dynamic";

export async function GET() {
  const skills = listSkills();
  const workflows = listWorkflows();
  const artifacts = listArtifacts();
  const runs = listRuns().slice(0, 6);
  return NextResponse.json({
    skills, workflows, runs,
    tasks: TASKS.map(({ id, title, tool }) => ({ id, title, tool })),
    stats: {
      skills: skills.length,
      workflows: workflows.length,
      artifacts: artifacts.length,
      installed: skills.filter((s) => s.installed).length,
    },
    latest: artifacts.filter((a) => a.tier === "final" && a.previewable === "image").slice(0, 8),
  });
}
