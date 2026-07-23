import fs from "node:fs";
import path from "node:path";
import { REPO, walk } from "./paths";

export type Artifact = {
  rel: string;          // 仓库相对路径
  name: string;
  topGroup: string;     // 顶层示例目录(分区依据)
  subPath: string;      // 分区内子路径(不含文件名)
  ext: string;
  size: number;
  mtime: number;
  kind: "image" | "pdf" | "deck";
  tier: "final" | "material";   // 成品 / 过程素材
  previewable: "image" | "pdf" | "none";
  sibling?: string;     // pptx 的同名 pdf 预览
};

const EXTS = [".png", ".jpg", ".jpeg", ".svg", ".pdf", ".pptx"];
// 中间素材目录:面板、按需收集的图素材、模板编译目录
const MATERIAL_RE = /(^|\/)(panels|assets|pkuthss_build|__pycache__)(\/|$)/;

export function listArtifacts(): Artifact[] {
  const out: Artifact[] = [];
  const dir = path.join(REPO, "examples");
  for (const f of walk(dir, { exts: EXTS, skip: /node_modules|__pycache__|\.git|assets\/fig-00[13]/ })) {
    const rel = path.relative(REPO, f);
    const ext = path.extname(f).toLowerCase();
    const st = fs.statSync(f);
    const parts = rel.split(path.sep); // examples / <top> / ... / file
    const topGroup = parts[1] ?? "examples";
    const subPath = parts.slice(2, -1).join("/");
    const kind = ext === ".pdf" ? "pdf" : ext === ".pptx" ? "deck" : "image";
    const art: Artifact = {
      rel, name: path.basename(f), topGroup, subPath, ext,
      size: st.size, mtime: st.mtimeMs, kind,
      tier: MATERIAL_RE.test(rel) ? "material" : "final",
      previewable: kind === "pdf" ? "pdf" : kind === "deck" ? "none" : "image",
    };
    if (ext === ".pptx") {
      const pdf = f.replace(/\.pptx$/, ".pdf");
      if (fs.existsSync(pdf)) art.sibling = path.relative(REPO, pdf);
    }
    out.push(art);
  }
  return out.sort((a, b) => b.mtime - a.mtime);
}
