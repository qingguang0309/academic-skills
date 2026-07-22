import fs from "node:fs";
import path from "node:path";
import { REPO, walk } from "./paths";

export type Artifact = {
  rel: string;          // 仓库相对路径
  name: string;
  group: string;        // 所属示例/目录
  ext: string;
  size: number;
  mtime: number;
  previewable: "image" | "pdf" | "none";
  sibling?: string;     // pptx 的同名 pdf 预览
};

const EXTS = [".png", ".jpg", ".jpeg", ".svg", ".pdf", ".pptx"];

export function listArtifacts(): Artifact[] {
  const roots = ["examples"];
  const out: Artifact[] = [];
  for (const r of roots) {
    const dir = path.join(REPO, r);
    for (const f of walk(dir, { exts: EXTS, skip: /node_modules|__pycache__|\.git|assets\/fig-00[13]/ })) {
      const rel = path.relative(REPO, f);
      const ext = path.extname(f).toLowerCase();
      const st = fs.statSync(f);
      const parts = rel.split(path.sep);
      const group = parts.length > 2 ? parts.slice(1, -1).join("/") : parts[1] ?? r;
      const previewable = ext === ".pdf" ? "pdf" : ext === ".pptx" ? "none" : "image";
      const art: Artifact = {
        rel, name: path.basename(f), group, ext,
        size: st.size, mtime: st.mtimeMs, previewable,
      };
      if (ext === ".pptx") {
        const pdf = f.replace(/\.pptx$/, ".pdf");
        if (fs.existsSync(pdf)) art.sibling = path.relative(REPO, pdf);
      }
      out.push(art);
    }
  }
  return out.sort((a, b) => b.mtime - a.mtime);
}
