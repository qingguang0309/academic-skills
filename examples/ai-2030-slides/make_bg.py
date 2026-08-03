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

# ── 色块上的同源肌理 ────────────────────────────────────────────────
# split 封面左侧是 33.9% 宽的实色竖块（BW/W = 4.52/13.33），纯色大面积显平。
# 参考件的做法是在色块上叠一层**同色系、略浅**的素材，让它沉进色块里。
# 这里切同一张图的左 33.9%，在品牌橙上做烘焙——两侧是同一张图跨接缝延续，
# 只是一边压在白底、一边压在橙底，用两种烘焙。
BLOCK_FRAC = 4.52 / 13.33
BRAND = (0xD9, 0x77, 0x57)
BLOCK_PEAK = 0.16          # 比白底那版稍高：橙底上同样的浓度看着更弱

im2 = Image.open(SRC).convert("L")
w2, h2 = im2.size
if w2 / h2 > ar:
    nw = int(h2 * ar); im2 = im2.crop(((w2 - nw) // 2, 0, (w2 + nw) // 2, h2))
else:
    nh = int(w2 / ar); im2 = im2.crop((0, (h2 - nh) // 2, w2, (h2 + nh) // 2))
im2 = im2.resize((W, H), Image.LANCZOS).crop((0, 0, int(W * BLOCK_FRAC), H))

gb = np.asarray(im2, dtype=np.float32) / 255.0
hb = gb.shape[0]
rampb = np.clip((np.linspace(0, 1, hb) - RAMP_START) / (1 - RAMP_START), 0, 1)
ab = (rampb ** 1.4)[:, None] * BLOCK_PEAK
# 深色塔架 → 提亮；即在橙底上向白靠，形成"浅色剪影"，与参考件的浅调线描同理
lift = (1.0 - gb) * ab
rgb = np.stack([BRAND[i] + (255 - BRAND[i]) * lift for i in range(3)], axis=-1)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").save(
    "assets/bg_block.png", optimize=True)
print(f"assets/bg_block.png  {int(W * BLOCK_FRAC)}×{H}（橙块专用，与右侧同源）")
