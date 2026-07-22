import fs from "node:fs";
import path from "node:path";
import { safeRepoPath } from "@/lib/paths";

export const dynamic = "force-dynamic";

const MIME: Record<string, string> = {
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml", ".pdf": "application/pdf",
  ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  ".md": "text/markdown; charset=utf-8", ".json": "application/json",
  ".txt": "text/plain; charset=utf-8",
};

export async function GET(req: Request) {
  const url = new URL(req.url);
  const rel = url.searchParams.get("path") ?? "";
  const download = url.searchParams.get("dl") === "1";
  let abs: string;
  try { abs = safeRepoPath(rel); } catch { return new Response("forbidden", { status: 403 }); }
  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) return new Response("not found", { status: 404 });
  const ext = path.extname(abs).toLowerCase();
  if (!(ext in MIME)) return new Response("type not allowed", { status: 415 });
  const buf = fs.readFileSync(abs);
  const headers: Record<string, string> = {
    "content-type": MIME[ext],
    "cache-control": "no-store",
  };
  if (download) headers["content-disposition"] = `attachment; filename="${encodeURIComponent(path.basename(abs))}"`;
  return new Response(new Uint8Array(buf), { headers });
}
