"""anatomy_export — 把 anatomy skill 画的等轴测装置图导出成可直接进 PPT/论文的 PNG。

anatomy（github.com/wheresryan22/anatomy，本仓库 skills/anatomy，装在 ~/.claude/skills/anatomy）
擅长画"有体积的真实装置"：扣式电池夹具、电镜镜筒、反应釜、谱仪光路。它的产物是
交互式 HTML 页面，原样截图放进幻灯有三个问题，本脚本逐一处理：

1. **线太细、灰阶太浅**：浅色主题是 0.6 px 发丝线 + 极浅灰，屏幕近看精致，
   投影上一片发白。导出时注入"幻灯配置"：线宽 1.1 px，lo/mid/faint 与暗面加深一档。
2. **卡片与留白**：只截 ``.iso-stage svg``（不要 Fig 编号、标题、读数那张卡片——
   图注交给 slidekit 的 caption），纸色改纯白，再按内容裁边，图在栏里才够大。
3. **矢量不能直接进 pptx**：线宽靠 ``vector-effect: non-scaling-stroke``，光晕靠
   CSS blur，颜色全是 CSS 变量——PowerPoint 的 SVG 渲染不认这些。所以走无界面
   Chrome 按 4 倍像素比截 PNG，而不是放大 SVG（放大 SVG 线宽不变，会更细）。

不改 anatomy 的构建脚本：样式在截图前由 drive.mjs 注入页面，任何 ``*-light.html`` 都能用。

用法::

    python3 anatomy_export.py fig-light.html -o assets/fig/clamp.png
    python3 anatomy_export.py fig-light.html -o clamp.png --pose '[["key","End"]]'   # 先摆姿态再截
    python3 anatomy_export.py fig-light.html -o clamp.png --keep-tones                # 保留 anatomy 原色

依赖:Node 20.10+、Chrome/Chromium(anatomy 自带的 drive.mjs 要用)、Pillow。
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops

# 幻灯配置:只动线宽与灰阶,不动构图与配色体系。数值按 13.33in 宽幅、投影观看校过——
# 原版 lo #b4b4b8 / faint #d4d4d6 在白底上对比度不到 2:1,投影等于看不见
DECK_CSS = (
    '.iso[data-theme="light"]{'
    "--anatomy-page:#ffffff;--anatomy-card:#ffffff;--anatomy-paper:#ffffff;"
    "--anatomy-weight:1.1px;--anatomy-mid:#6e6e73;--anatomy-lo:#909095;--anatomy-faint:#b9b9bc;"
    "--anatomy-shade-0:#cfcfcb;--anatomy-shade-1:#dadad6}"
)
PAPER_CSS = '.iso[data-theme="light"]{--anatomy-page:#ffffff;--anatomy-card:#ffffff;--anatomy-paper:#ffffff}'


def anatomy_dir(given):
    d = pathlib.Path(given or os.environ.get("ANATOMY_DIR") or "~/.claude/skills/anatomy").expanduser()
    if not (d / "scripts" / "drive.mjs").exists():
        sys.exit(f"找不到 anatomy:{d}/scripts/drive.mjs 不存在。先安装:"
                 f"npx skills add wheresryan22/anatomy -g -a claude-code,或用 --anatomy-dir 指定")
    return d


def trim(png, margin):
    """按内容裁掉四周白边,留 margin 像素净空。"""
    im = Image.open(png).convert("RGB")
    diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255)))
    box = diff.convert("L").point(lambda v: 255 if v > 6 else 0).getbbox()
    if not box:
        sys.exit(f"{png} 是一张白图——页面没画出来,先用 anatomy 的 capture.mjs 看看页面本身")
    x0, y0, x1, y1 = box
    return im.crop((max(0, x0 - margin), max(0, y0 - margin),
                    min(im.width, x1 + margin), min(im.height, y1 + margin)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("page", help="anatomy 构建出的浅色页面(*-light.html)")
    ap.add_argument("-o", "--out", required=True, help="输出 PNG")
    ap.add_argument("--scale", type=float, default=4, help="设备像素比(默认 4,约 2400 px 宽)")
    ap.add_argument("--pose", default="[]", help='截图前执行的 drive.mjs 动作 JSON,如 \'[["key","End"]]\'')
    ap.add_argument("--wait", type=int, default=800, help="摆完姿态后等待的毫秒数")
    ap.add_argument("--margin", type=int, default=40, help="裁边后保留的白边(像素)")
    ap.add_argument("--keep-tones", action="store_true", help="只换白纸,不加粗不加深")
    ap.add_argument("--anatomy-dir", help="anatomy 安装目录(默认 $ANATOMY_DIR 或 ~/.claude/skills/anatomy)")
    a = ap.parse_args()

    page = pathlib.Path(a.page).resolve()
    html = page.read_text(encoding="utf-8", errors="ignore")
    # 样式只覆盖浅色主题:anatomy 的主题在构建时写死在第一个 <body> 上(内联 CSS 与脚本里
    # 也出现 data-theme 字样,不能整页搜),深色页面要用 --light 重新构建
    body = re.search(r"<body[^>]*>", html)
    if not body or 'data-theme="light"' not in body.group(0):
        sys.exit(f"{page.name} 不是浅色主题页面——幻灯与论文用白底,请用 build.mjs --light 构建")
    drive = anatomy_dir(a.anatomy_dir) / "scripts" / "drive.mjs"
    # --pose 里的 key 动作会聚焦图形,焦点框会被一起截进去:去掉轮廓,截图前再移走焦点
    css = (PAPER_CSS if a.keep_tones else DECK_CSS) + ".iso-stage:focus,.iso-stage:focus-visible{outline:none;box-shadow:none}"
    inject = ("(()=>{const s=document.createElement('style');"
              f"s.textContent={json.dumps(css)};document.head.appendChild(s);return 'deck style on'}})()")

    with tempfile.TemporaryDirectory() as tmp:
        raw = pathlib.Path(tmp) / "raw.png"
        actions = [["eval", inject], *json.loads(a.pose), ["wait", a.wait],
                   ["eval", "document.activeElement && document.activeElement.blur(), 'blurred'"],
                   ["shot", str(raw), ".iso-stage svg", a.scale]]
        steps = pathlib.Path(tmp) / "steps.json"
        steps.write_text(json.dumps(actions), encoding="utf-8")
        # --reduced:关掉空闲巡游,页面停在构建时的初始姿态(或 --pose 摆出的姿态)
        r = subprocess.run(["node", str(drive), str(page), "--actions", str(steps), "--reduced"],
                           capture_output=True, text=True)
        if r.returncode != 0 or not raw.exists():
            sys.exit(f"drive.mjs 失败:\n{r.stdout}\n{r.stderr}")
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        im = trim(raw, a.margin)
        im.save(out)

    print(f"wrote {out} ({im.width}×{im.height} px)")
    print("进 slidekit:{ type: \"figure\", path: \"%s\", evidence: \"schematic\", caption: \"…\" }" % out)


if __name__ == "__main__":
    main()
