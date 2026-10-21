# 实验装置示意图：交给 anatomy 画

实验装置、仪器结构、测试夹具、反应器这类"有体积的真实东西"，matplotlib 和 schemfig 都画不好：schemfig 擅长节点—连线，画出来的装置是一堆方框。这类图交给 **anatomy** skill（[github.com/wheresryan22/anatomy](https://github.com/wheresryan22/anatomy)，MIT），它用等轴测实体零件把装置真实地搭出来；本仓库只负责把它的产物接进论文和汇报。

## 什么时候用它

| 要画的东西 | 用什么 |
|---|---|
| 实验装置、仪器结构、测试夹具、反应釜、谱仪光路、电镜镜筒 | **anatomy** |
| 方法流程、技术路线（节点 + 连线） | `schemfig.py flow` |
| 自由构图的机理示意（框、箭头、嵌入小图） | schemfig 的 `text_box` / `connect` |
| 数据图 | paperfig |
| 晶体结构、分子、形貌 | VESTA / Blender 出素材 |

anatomy **不画数据**（没有坐标轴和序列）、不画人和地图；它的数字只来自驱动零件运动的那个小模型。所以图上出现的数值（行程、受力、间隙）必须是真实参数或明说的模型取值。

## 前提

anatomy 在本仓库 `skills/anatomy/`（引自上游，同步方法见其 UPSTREAM.md），和 paper-figures 一起装：

```bash
cp -r skills/anatomy ~/.claude/skills/
```

需要 Node 20.10+ 和 Chrome（它用无界面 Chrome 做截图与检查）。装在别处时设环境变量 `ANATOMY_DIR`。

## 流程

### 1. 按 anatomy 的规矩画，构建浅色版

调用 anatomy skill，照它的 SKILL.md 走：先收集真实尺寸，再列零件清单（Figure 级 40–80 个零件，一小时左右），用它的 kit 搭几何。它的工艺纪律照它的来——灰阶分层、全图只有一个高亮零件（研究对象）、图内不写字（最多一块铭牌）、每条线都落在东西上。

学术模板：`examples/anatomy-coin-cell/build.mjs`，CR2032 扣式电池测试夹具，约 60 个零件。底板、PEEK 绝缘块、镀金上下电极、两根立柱与横梁、旋钮丝杠、5 片碟簧、两个接线柱；旋钮下压 7 mm，前 3 mm 消除间隙，之后碟簧以 2.5 N/mm（模型取值）把接触力加到 10 N。脚本按 `ANATOMY_DIR` 找 kit，可以复制到任何项目里改：

```bash
node build.mjs --light            # 幻灯与论文都用浅色版
node ~/.claude/skills/anatomy/scripts/lines.mjs coin-cell-light.html --out lines.png   # 必须 line ends: 0
```

**静态姿态**：页面在减弱动效模式下停在构建脚本给的初值上。模板把初值设在"已接触、压缩 2 mm、5.0 N"——静态图要挑最能说明机制的那一刻，不是行程起点。

### 2. 导出 PNG：`scripts/anatomy_export.py`

```bash
python3 scripts/anatomy_export.py coin-cell-light.html -o assets/fig/clamp.png
python3 scripts/anatomy_export.py page-light.html -o out.png --pose '[["key","End"]]'   # 先摆姿态再截
```

不改 anatomy 的构建脚本，截图前把"幻灯配置"注入页面。原样截图有三个实测问题，脚本逐一处理：

| 问题 | 原因 | 处理 |
|---|---|---|
| 投影上发白、线条看不见 | 浅色主题是 0.6 px 发丝线，lo/faint 灰在白底上对比度不到 2∶1 | 线宽提到 1.1 px，lo/mid/faint 与暗面各加深一档 |
| 图在栏里很小、四周一圈白 | 截的是整张卡片（Fig 编号、标题、读数），画面只占六成 | 只截 `.iso-stage svg`，纸色改纯白，再按内容裁边 |
| SVG 直接进 pptx 渲染不对 | 线宽靠 `vector-effect: non-scaling-stroke`，光晕靠 CSS blur，颜色全是 CSS 变量 | 走无界面 Chrome 按 4 倍像素比截 PNG；**不要**放大 SVG 再栅格化——线宽不随之变粗，只会更细 |

另外两条实测结论：

- **不要给它换主题色。** 把高亮零件的描边改成北大红试过：高亮只是一圈发丝线，幻灯尺寸上与灰色几乎分不出来，白费一步。强调交给 slidekit 的正文首句与加粗。
- **`--pose` 里用了 `key` 动作会聚焦图形**，焦点框会被截进去；脚本已在截图前去掉轮廓并移走焦点。

### 3. 进汇报（paper-slides）

```js
{ type: "figure", path: "assets/fig/clamp.png", evidence: "schematic", credit: "",
  caption: "CR2032 扣式电池测试夹具示意" }
```

- `evidence: "schematic"`：它是示意图，不是实拍——slidekit 会在图注前标【示意】，也不计入"真实素材"。
- `credit: ""`：自己画的图，显式豁免署名。
- 零件名称、数值写在旁边的 bullets 里，不写进图里（anatomy 的规矩，也省得改图）。模型取值在正文里注明"模型取值"。
- 放在 `cols` 的宽栏里（如 `ratio: [3, 2]`），4 倍截图约 1800–2400 px 宽，在 16:9 幻灯上足够清晰。

### 4. 进论文

按期刊线条图（line art）要求出更高像素比：`--scale 8 --margin 80`，模板实测 3648 px 宽，放成双栏 183 mm 约 500 dpi；期刊要求更高时再加大 `--scale`，并对照 `references/journal-specs.md` 核对 dpi。需要零件编号或标注时，在 matplotlib 里读入 PNG 后用 schemfig 叠加——这一步还没有在本流程里实测过，做的时候按 schemfig 的体检流程逐项检查。

## 实测记录

2026-10-20 在本机跑通：anatomy 自带最小示例 `dial-indicator` 构建结果与其仓库提交版逐字节一致；扣式电池夹具模板深浅两版线头检查均为 0，导出 1824×1649 px，放进 pku 主题 deck 的 `cols` 栏渲染正常；`anatomy_export.py` 的输出与手工注入样式后截图逐像素一致；深色页面与找不到 anatomy 时都会明确报错退出。
