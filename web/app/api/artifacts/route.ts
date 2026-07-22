import { NextResponse } from "next/server";
import { listArtifacts } from "@/lib/artifacts";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ artifacts: listArtifacts() });
}
