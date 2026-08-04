# academic-deck

生成能直接上台的中文学术汇报 PPT。答辩、开题、中期、组会、基金汇报、会议 talk。

不手拍坐标：声明"这页放哪些块"，位置、间距、字阶、页码、中西文分字体由布局引擎计算。

```bash
npm install
node examples/minimal/deck.js     # → minimal.pptx，6 页
```

## 它和"让模型写个 PPT"的区别

**重要的规矩被做成了会报警的构建期检查，而不是写在文档里等人遵守。**

| 检查 | 触发条件 |
|---|---|
| 实景照片 | 全篇 0 张真实照片 → 报警（`photos: false` 显式豁免） |
| 页面填充率 | 低于 62% → 提示这页太空，并给出四种补法 |
| 标题溢出 | 内容页标题超两行、封面标题超三行 → 报警 |
| 饼图选型 | 类别超过 3 类 → 报警，建议改降序水平条 |
| 图表配色 | 色板短于系列数 → 直接抛错（否则 pptxgenjs 会 `Math.random()` 取色，同一脚本跑两次颜色不一样） |
| 场合缺失 | 未写 `occasion` → 报警（中文学术封面的必需项） |
| 结束页 | 没写 `takeaway` → 报警（Q&A 全程停在这页，别只挂一句客套话） |
| 来源写法 | 用 callout 写页内来源 → 报警（它会跟着栏内流落在栏中部） |

## 目录

```
academic-deck/
├── SKILL.md                 六条规矩 + 块类型表 + 交付清单
├── scripts/
│   ├── slidekit.js          组件库与布局引擎（唯一必需）
│   └── fetchimg.py          取 CC 许可实景照片，署名自动落页（可选）
└── examples/minimal/        最小可运行示例
```

## 四套配色

`azure` 藏青·金（通用）/ `pine` 墨绿·赭 / `plum` 绛紫·杏 / `claude` 赤陶·暖砂

加自己单位的主题前先量对比度：primary 落在 7—11∶1、accent 4.5—5.9∶1（对各自 wash 底），
否则页标题与 kicker 会比其它主题明显偏弱。

## 依赖

必需：Node 18+（`npm install` 装 pptxgenjs 与 jszip）

可选，缺了只影响对应功能：

| 用途 | 依赖 |
|---|---|
| `fetchimg.py` 取图 | Python 3 + Pillow |
| 渲染 PDF 逐页目检 | LibreOffice（`soffice`）+ poppler（`pdftoppm`） |

## 已知限制

中文字体默认 Microsoft YaHei、西文 Arial；本机没有时由系统替换。
LibreOffice 预览的字距与 PowerPoint 实际打开会有差异，拿不准的页在真机确认。
