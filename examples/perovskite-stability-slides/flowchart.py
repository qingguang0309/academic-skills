#!/usr/bin/env python3
# ============================================================
# flowchart.py — 用 Graphviz 确定性布局引擎绘制流程图 / 技术路线图
#
# 为什么用 Graphviz(而不是手拍坐标、也不是生成模型):
#   节点位置与连线走向由布局引擎(dot)计算,箭头永不悬空、层级永不错位——
#   与 slidekit 的"版式交给引擎"是同一条原则。对比过 D2(PNG 导出依赖
#   Playwright,本机下载失败)与 Mermaid(需 Chromium),Graphviz 直出 PNG、
#   零浏览器依赖、CJK 正常,故定为本 skill 的流程图引擎。
#
# 用法:
#   python3 flowchart.py spec.json -o assets/dg/pipeline.png
#   python3 flowchart.py spec.json -o out.png --dpi 260   # 更高分辨率
#
# spec.json:
# {
#   "theme": "pku",              // azure | pine | plum | pku(与 slidekit 主题同色)
#   "direction": "LR",           // LR 横向(默认) | TB 纵向
#   "nodes": [
#     {"id": "a", "label": "卫星气溶胶\\nMODIS/MAIAC"},
#     {"id": "c", "label": "融合模型", "tone": "emphasis"},   // 主色实底,白字:全图重心
#     {"id": "d", "label": "浓度场",   "tone": "tint"},       // 浅色底:中间产物/输出
#     {"id": "q", "label": "残差达标?", "shape": "decision"}  // 判断菱形
#   ],
#   "edges": [ {"from": "a", "to": "c", "label": "光学厚度", "style": "dashed"} ],
#   "groups": [ {"label": "数据源", "nodes": ["a", "b"]} ]     // 虚线分组框
# }
# ============================================================
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

# 与 slidekit.js 的 THEMES 保持一致:图与页面同色,观众感知为"一套东西"
THEMES = {
    "azure": dict(primary="1F3A5F", accent="2F6FAE", wash="F3F6FA", tint="E7EEF6",
                  ink="23272E", muted="6E7681", line="D9DEE6"),
    "pine":  dict(primary="1C4B3F", accent="2E7D6B", wash="F2F7F5", tint="E4EFEA",
                  ink="242826", muted="6F7873", line="D8E2DD"),
    "plum":  dict(primary="4B2D50", accent="7B4E80", wash="F6F3F7", tint="EFE7F0",
                  ink="26232A", muted="757079", line="E0D8E2"),
    "pku":   dict(primary="9A0001", accent="BE2A2E", wash="FBF5F4", tint="F4E4E3",
                  ink="2A2422", muted="797069", line="E7DAD8"),
}
# 单字体内含拉丁 + 中日韩:避免逐字回退不可靠导致的豆腐块
CJK_FONT = "Arial Unicode MS"
SHAPES = {"box": "box", "decision": "diamond", "round": "ellipse", "cylinder": "cylinder"}


def q(s: str) -> str:
    """DOT 字符串转义;\\n 保留为 Graphviz 的换行。"""
    return '"' + str(s).replace('"', r'\"') + '"'


def node_style(th: dict, tone: str) -> str:
    if tone == "emphasis":   # 全图重心:主色实底白字
        return f'fillcolor="#{th["primary"]}", fontcolor="white", color="#{th["primary"]}"'
    if tone == "tint":       # 中间产物 / 输出
        return f'fillcolor="#{th["tint"]}", fontcolor="#{th["ink"]}", color="#{th["primary"]}"'
    if tone == "plain":      # 弱化的旁支
        return f'fillcolor="white", fontcolor="#{th["muted"]}", color="#{th["line"]}"'
    return f'fillcolor="#{th["wash"]}", fontcolor="#{th["ink"]}", color="#{th["primary"]}"'


def build_dot(spec: dict) -> str:
    th = THEMES.get(spec.get("theme", "azure"))
    if th is None:
        sys.exit(f"[flowchart] 未知主题 {spec.get('theme')};可选 {'/'.join(THEMES)}")
    rankdir = "TB" if str(spec.get("direction", "LR")).upper() in ("TB", "TD") else "LR"
    font = spec.get("font", CJK_FONT)

    L = [f"digraph G {{",
         f'  rankdir={rankdir}; bgcolor="transparent"; splines=spline; compound=true;',
         f'  nodesep={spec.get("nodesep", 0.42)}; ranksep={spec.get("ranksep", 0.6)};',
         f'  node [shape=box, style="rounded,filled", fontname={q(font)}, fontsize={spec.get("fontsize", 13)},',
         f'        penwidth=1.3, margin="0.22,0.14"];',
         f'  edge [color="#{th["muted"]}", fontname={q(font)}, fontsize={spec.get("edgefontsize", 10.5)},',
         f'        fontcolor="#{th["muted"]}", penwidth=1.2, arrowsize=0.78];']

    # 分组框(虚线 cluster):表达"阶段"而不额外画装饰
    grouped = set()
    for i, g in enumerate(spec.get("groups", [])):
        L.append(f'  subgraph cluster_{i} {{')
        L.append(f'    label={q(g.get("label", ""))}; labeljust="l"; fontname={q(font)};')
        L.append(f'    fontsize={spec.get("groupfontsize", 11)}; fontcolor="#{th["accent"]}";')
        L.append(f'    style="dashed,rounded"; color="#{th["line"]}"; penwidth=1.1; margin=14;')
        for nid in g.get("nodes", []):
            L.append(f"    {nid};")
            grouped.add(nid)
        L.append("  }")

    for n in spec.get("nodes", []):
        shp = SHAPES.get(n.get("shape", "box"), "box")
        st = "rounded,filled" if shp == "box" else "filled"
        L.append(f'  {n["id"]} [label={q(n["label"])}, shape={shp}, style="{st}", '
                 f'{node_style(th, n.get("tone", "default"))}];')

    for e in spec.get("edges", []):
        opts = [f'style={e["style"]}'] if e.get("style") else []
        if e.get("label"):
            opts.append(f'label={q(e["label"])}')
        if e.get("tone") == "emphasis":
            opts.append(f'color="#{th["primary"]}", penwidth=1.8')
        if e.get("dir") == "both":
            opts.append("dir=both")
        L.append(f'  {e["from"]} -> {e["to"]}' + (f' [{", ".join(opts)}]' if opts else "") + ";")

    L.append("}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="Graphviz 流程图:声明 JSON → 演示级 PNG")
    ap.add_argument("spec", help="spec.json 路径")
    ap.add_argument("-o", "--out", required=True, help="输出 PNG")
    ap.add_argument("--dpi", type=int, default=220, help="渲染 DPI(默认 220,投影足够)")
    ap.add_argument("--keep-dot", action="store_true", help="保留中间 .dot 便于调试")
    args = ap.parse_args()

    if not shutil.which("dot"):
        sys.exit("[flowchart] 未找到 graphviz 的 dot 命令。安装:brew install graphviz "
                 "(或 apt-get install graphviz);没有它就不要手拍坐标画流程图。")

    spec = json.loads(pathlib.Path(args.spec).read_text())
    dot = build_dot(spec)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dot_path = out.with_suffix(".dot")
    dot_path.write_text(dot)

    r = subprocess.run(["dot", "-Tpng", f"-Gdpi={args.dpi}", str(dot_path), "-o", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"[flowchart] dot 渲染失败:\n{r.stderr.strip()}")
    if not args.keep_dot:
        dot_path.unlink(missing_ok=True)

    kb = out.stat().st_size // 1024
    print(f"[flowchart] {out} ({kb} KB, dpi={args.dpi})")
    print("[flowchart] 请用 Read 亲眼检查:节点是否有文字被裁、连线是否穿过节点、层级是否符合叙事顺序。")


if __name__ == "__main__":
    main()
