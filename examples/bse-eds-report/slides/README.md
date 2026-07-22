# 汇报 PPT:由本案例生成的开放基金 grant briefing(paper-slides skill)

用本仓库的 **[paper-slides](../../../skills/paper-slides/)** skill 从本目录的研究计划报告
生成的 18 页中文汇报,演示 slidekit 组件库的完整页型:

- `bse_eds_grant_briefing.pptx` — 成品(含演讲者备注);`.pdf` 为预览
- `gen_deck.js` — 生成脚本:只声明内容与块结构,坐标/字阶/页码全部由 slidekit 计算
- `slidekit.js` — 组件库副本(从 skill 复制,随交付归属本目录)
- `prepare_assets.sh` — 收集图素材(架构图取自 figflow-demo,Fig.1/Fig.2 从 paper_article.pdf 抽取)

版式要点:深色封面/结束页三明治结构,目录与章节过渡页自动生成(超大章节号 +
底部章节导航),内容页 kicker+action title,三线表,大数字卡,主动采样四步流程图,
参考文献自动双栏编号,页脚自动"短题 · 章节 | 页码"。中西文混排自动分字体,
中文微软雅黑、西文 Arial。全篇数值为申报目标(黄色 callout 声明),图为合成示意数据。

复现:

```bash
sh prepare_assets.sh
npm install pptxgenjs
node gen_deck.js   # → bse_eds_grant_briefing.pptx
```
