#!/usr/bin/env python3
# ============================================================
# collage.py — 确定性拼图:多张单图 → 一张组图
#
# 铁律配套工具:多图合并永远"先单张、后拼版"。单张内容可以来自
# matplotlib(paper-figures)、AI 生图(aiimg.py)或照片(fetchimg.py),
# 但拼版必须由本工具确定性完成——等高缩放、统一留白、可选 (a)(b) 角标,
# 版式问题从机制上消除,不把拼版交给生成模型碰运气。
#
# 用法:
#   python3 collage.py out.png a.png b.png             # 一行两列
#   python3 collage.py out.png a.png b.png c.png d.png -c 2 --labels
# ============================================================
import argparse
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.image import imread


def main():
    ap = argparse.ArgumentParser(description="确定性拼图(等高/统一留白/可选角标)")
    ap.add_argument("out", help="输出文件(.png)")
    ap.add_argument("images", nargs="+", help="输入单图,按版面顺序")
    ap.add_argument("-c", "--cols", type=int, default=None, help="列数,默认一行排完")
    ap.add_argument("-g", "--gap", type=float, default=0.02, help="图间距(画布比例,默认 0.02)")
    ap.add_argument("--labels", action="store_true", help="加 (a)(b)(c) 角标")
    ap.add_argument("--width", type=float, default=12.0, help="画布宽(英寸,默认 12)")
    args = ap.parse_args()

    n = len(args.images)
    cols = args.cols or n
    rows = -(-n // cols)
    imgs = [imread(p) for p in args.images]

    # 以首行图的平均纵横比估算画布高
    ars = [im.shape[0] / im.shape[1] for im in imgs]
    row_h = args.width / cols * max(ars[:cols])
    fig_h = row_h * rows

    fig, axes = plt.subplots(rows, cols, figsize=(args.width, fig_h))
    axes = [axes] if n == 1 else list(axes.flat) if hasattr(axes, "flat") else [axes]
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0,
                        wspace=args.gap, hspace=args.gap)
    for i, ax in enumerate(axes):
        ax.axis("off")
        if i >= n:
            continue
        ax.imshow(imgs[i])
        if args.labels:
            ax.text(0.02, 0.97, f"({chr(97 + i)})", transform=ax.transAxes,
                    fontsize=15, fontweight="bold", color="white", va="top",
                    bbox=dict(boxstyle="round,pad=0.25", fc="black", alpha=0.45, ec="none"))
    fig.savefig(args.out, dpi=220, facecolor="white")
    print(f"[collage] {n} 张 → {args.out}({rows}×{cols})")


if __name__ == "__main__":
    main()
    sys.exit(0)
