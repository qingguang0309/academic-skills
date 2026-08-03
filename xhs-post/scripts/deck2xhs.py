#!/usr/bin/env python3
# ============================================================
# deck2xhs.py —— 把 PPT / PDF 逐页转成小红书可直接上传的图片
#
#   python3 deck2xhs.py talk.pptx -o xhs
#   python3 deck2xhs.py paper.pdf -o xhs --dpi 200
#   python3 deck2xhs.py talk.pptx -o xhs --only 1,3,5-9      # 挑页
#
# 产出两套：
#   xhs-01.png …  3:4（1080×1440），小红书信息流原生比例，**传这套**
#   page-01.png … 原始比例高清图，需要横版或再加工时用
#
# 三条踩过的坑，已在脚本里挡住：
#   1. 小红书信息流按 3:4 展示。16:9 幻灯直接传会被自动裁掉左右两侧——
#      正文那一列会整个没掉。必须放进 3:4 画布居中，宁可留白也不裁内容。
#   2. pdftoppm 对个位数页码不补零，生成 page-1/page-10，
#      按文件名排序会变成 1,10,11,2…。这里统一补零。
#   3. 留白底色不能写死。从页面四角采样取实际底色，
#      否则暖白版式配纯白留白会出现一圈可见的边界。
# ============================================================
import argparse
import pathlib
import re
import shutil
import subprocess
import sys
from collections import Counter

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow：pip install pillow")

XHS_W, XHS_H = 1080, 1440          # 小红书信息流原生 3:4
XHS_MAX = 18                       # 单篇图片上限
PAD = 20                           # 3:4 画布内的安全留白(px)


def need(cmd):
    if not shutil.which(cmd):
        sys.exit(f"缺少命令 {cmd}。pptx 转换需要 LibreOffice(soffice)，"
                 f"逐页出图需要 poppler(pdftoppm)。")


def to_pdf(src: pathlib.Path, workdir: pathlib.Path) -> pathlib.Path:
    if src.suffix.lower() == ".pdf":
        return src
    need("soffice")
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf",
                    str(src), "--outdir", str(workdir)],
                   check=True, capture_output=True)
    pdf = workdir / (src.stem + ".pdf")
    if not pdf.exists():
        sys.exit(f"LibreOffice 未能转换 {src}")
    return pdf


def render(pdf: pathlib.Path, outdir: pathlib.Path, dpi: int):
    need("pdftoppm")
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png",
                    "-aa", "yes", "-aaVector", "yes",
                    str(pdf), str(outdir / "page")], check=True)
    # pdftoppm 不补零：page-1 / page-10 混排会让按名排序错乱
    for f in sorted(outdir.glob("page-*.png")):
        n = re.search(r"-(\d+)\.png$", f.name).group(1)
        tgt = outdir / f"page-{int(n):02d}.png"
        if f != tgt:
            f.rename(tgt)
    return sorted(outdir.glob("page-*.png"))


def edge_color(im: Image.Image):
    """从四角采样取页面底色。留白写死纯白，遇到暖白/米色版式会露出边界。"""
    w, h = im.size
    k = max(4, min(w, h) // 60)
    px = []
    for box in [(0, 0, k, k), (w - k, 0, w, k), (0, h - k, k, h), (w - k, h - k, w, h)]:
        px += list(im.crop(box).getdata())
    return Counter(px).most_common(1)[0][0]


def parse_only(spec, n):
    if not spec:
        return list(range(1, n + 1))
    keep = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            keep += list(range(int(a), int(b) + 1))
        elif part:
            keep.append(int(part))
    bad = [i for i in keep if not 1 <= i <= n]
    if bad:
        sys.exit(f"--only 里的页码超出范围(共 {n} 页)：{bad}")
    return keep


def main():
    ap = argparse.ArgumentParser(description="PPT / PDF 逐页转小红书图片")
    ap.add_argument("src", help="输入 .pptx 或 .pdf")
    ap.add_argument("-o", "--outdir", default="xhs", help="输出目录(默认 xhs)")
    ap.add_argument("--dpi", type=int, default=160, help="原图渲染 DPI(默认 160)")
    ap.add_argument("--only", help="只要某几页，如 1,3,5-9")
    ap.add_argument("--bg", help="3:4 留白底色 #RRGGBB；默认从页面四角采样")
    a = ap.parse_args()

    src = pathlib.Path(a.src).expanduser().resolve()
    if not src.exists():
        sys.exit(f"找不到 {src}")
    out = pathlib.Path(a.outdir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    pages = render(to_pdf(src, out), out, a.dpi)
    if not pages:
        sys.exit("没有渲染出任何页面")
    keep = parse_only(a.only, len(pages))

    im0 = Image.open(pages[0])
    ratio = im0.height / im0.width
    print(f"共 {len(pages)} 页，原图 {im0.size}，比例 1:{ratio:.3f}"
          f"（小红书 3:4 是 1:1.333）")

    bg = None
    if a.bg:
        h = a.bg.lstrip("#")
        bg = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    made = []
    for idx, i in enumerate(keep, 1):
        im = Image.open(pages[i - 1]).convert("RGB")
        canvas_bg = bg or edge_color(im)
        # 按"能放下"缩放：比 3:4 更宽的(如 16:9)受宽度约束，更瘦的(如 A4)受高度约束
        sw, sh = XHS_W - 2 * PAD, XHS_H - 2 * PAD
        sc = min(sw / im.width, sh / im.height)
        im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
        canvas = Image.new("RGB", (XHS_W, XHS_H), canvas_bg)
        canvas.paste(im, ((XHS_W - im.width) // 2, (XHS_H - im.height) // 2))
        p = out / f"xhs-{idx:02d}.png"
        canvas.save(p, quality=95)
        made.append(p)

    print(f"3:4 版 {len(made)} 张 → {out}/xhs-*.png")
    print(f"原图     {len(pages)} 张 → {out}/page-*.png")
    if len(made) > XHS_MAX:
        print(f"\n!! 超出小红书单篇 {XHS_MAX} 张上限 {len(made) - XHS_MAX} 张。"
              f"用 --only 挑页，并在交付说明里写清删了哪几页、为什么——"
              f"静默截断会让作者以为全都发出去了。")
    else:
        print(f"在 {XHS_MAX} 张上限内，可全部上传。")


if __name__ == "__main__":
    main()
