# 汇报 PPT:由本案例再生成的开放基金 grant briefing

用 [academic-pptx](https://github.com/Gabberflast/academic-pptx-skill) skill(内容与结构规范)
+ Anthropic 官方 pptx skill(文件生成与 QA)从本目录的研究计划报告生成的 11 页中文汇报:

- `bse_eds_grant_briefing.pptx` — 成品(含演讲者备注);`.pdf` 为预览
- `gen_deck.js` — pptxgenjs 生成脚本,改内容重跑即可
- `prepare_assets.sh` — 收集图素材(架构图取自 figflow-demo,Fig.1/Fig.2 从 paper_article.pdf 抽取)

结构遵循 academic-pptx 规范:每页标题为完整结论句(action title,通读标题即成完整论证)、
每张结果页一个 exhibit 且关键发现标注在图上、页内引用 + 文末参考文献页、
结论页深蓝底供 Q&A 停留、附录页备提问导航;白底单字体三色以内,正文 ≥19 pt。
全篇数值为申报目标而非已得结果,图为合成示意数据(与报告一致)。

复现:

```bash
sh prepare_assets.sh
npm install pptxgenjs
node gen_deck.js   # → bse_eds_grant_briefing.pptx
```
