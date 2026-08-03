"""把一张实景照片烘焙成首尾页的极淡底图。

配方来自拆解真实汇报的结束页底图（3840×2160、8-bit 调色板、33 级灰阶，
取值仅 255→223，上部 68% 是纯白）——等价于原照按约 12% 不透明度压在白底上，
且淡化是**烘焙进 PNG** 的，不靠 PPT 的透明度设置。这样做的好处是渲染器无关：
PowerPoint、LibreOffice、导出的 PDF 看到的都是同一张图。

再加一条竖向的不透明度斜坡：上半段完全为白，从 55% 高度起线性升到峰值。
均匀压淡会读成"一张被冲淡的照片"，带斜坡才读成"下缘的一层肌理"。
"""
from PIL import Image
import numpy as np

SRC = "assets/electricity_transmission_1.jpg"
OUT = "assets/bg_grid.png"
W, H = 2666, 1500          # 16:9，与 13.33×7.5 in 画布同比
PEAK = 0.12                # 底部峰值不透明度，对齐参考件的 12%
RAMP_START = 0.55          # 自此高度起开始显影，之上全白

im = Image.open(SRC).convert("L")          # 先转灰阶：底图不该带自己的色相
# 中心裁到 16:9 再缩放，避免拉伸变形
ar = W / H
w, h = im.size
if w / h > ar:
    nw = int(h * ar); im = im.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
else:
    nh = int(w / ar); im = im.crop((0, (h - nh) // 2, w, (h + nh) // 2))
im = im.resize((W, H), Image.LANCZOS)

g = np.asarray(im, dtype=np.float32) / 255.0
ramp = np.clip((np.linspace(0, 1, H) - RAMP_START) / (1 - RAMP_START), 0, 1)
alpha = (ramp ** 1.4)[:, None] * PEAK      # 指数 1.4 让过渡更靠下、更柔
out = 1.0 - alpha * (1.0 - g)              # 以白为底做 alpha 合成
arr = np.clip(out * 255, 0, 255).astype(np.uint8)
Image.fromarray(arr, mode="L").save(OUT, optimize=True)

print(f"{OUT}  {W}×{H}")
print(f"  最暗像素 {arr.min()}（参考件为 223），上部 50% 最暗 {arr[:H//2].min()}")
