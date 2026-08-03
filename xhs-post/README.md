# xhs-post

把做好的 PPT / PDF / 论文转成小红书图文笔记：逐页出图 + 写文案。

这是一个**自包含**的 Claude Agent Skill，整个目录可以单独打包分发，不依赖本仓库其它部分。

```
xhs-post/
├── SKILL.md                    技能定义（五条铁律 + 五步流程）
├── scripts/deck2xhs.py         PPT/PDF → 3:4 竖版图片
└── references/copywriting.md   文案结构、词表、自查清单
```

## 用法

```bash
python3 scripts/deck2xhs.py talk.pptx -o xhs
python3 scripts/deck2xhs.py paper.pdf -o xhs --dpi 200
python3 scripts/deck2xhs.py talk.pptx -o xhs --only 1,4-9,12,15-19
```

产出 `xhs-01.png`…（3:4，1080×1440，上传这套）与 `page-01.png`…（原始比例高清图）。

## 依赖

- Python 3 + Pillow
- poppler（`pdftoppm`）—— 逐页出图
- LibreOffice（`soffice`）—— 仅 .pptx 输入时需要

```bash
brew install poppler          # macOS
pip install pillow
```

## 它挡住的三个坑

1. **3:4 不是建议。** 小红书信息流按 3:4 展示，16:9 幻灯直接传会被裁掉左右两侧——
   正文那一列会整个没掉。脚本放进 1080×1440 画布居中，宁可留白也不裁内容。
2. **`pdftoppm` 不补零。** `page-1` / `page-10` 按名排序会变成 1,10,11,2…，脚本统一补零。
3. **留白底色不写死。** 从页面四角采样取实际底色，暖白版式配纯白留白会露出一圈边界。

超过小红书单篇 18 张上限时脚本报警而不静默截断——静默截断会让作者以为全都发出去了。

## 不做什么

不发布、不登录、不代操作账号，只产出文件。发布由作者本人完成。
