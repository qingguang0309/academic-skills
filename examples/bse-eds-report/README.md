# 示例:从基金申请书再生成研究计划报告(BSE–EDS 多模态融合)

由一份真实开放基金申请书(《BSE–EDS 多模态融合的水泥基材料微观相识别与水化程度
智能表征》,非金属材料AI+实验室)的研究内容再生成的英文研究计划报告,用于演示
paperflow 在真实项目材料上的完整链路:

- 6 个代理并行产出 5 个章节与作图脚本(fixtures/),图为按主题现场生成的合成数据
  四联图(BSE/稀疏EDS/SLIC超像素图/相图)与指标示意图
- 7 条文献经 Crossref 实时核验(run_report.json);1 条 arXiv DOI 未命中被核验门剔除
- article 模板渲染 + tectonic 编译 → paper_article.pdf(5 页标准论文格式)

复现:`PYTHONPATH=. python -m paperflow --config ../examples/bse-eds-report/paper.yaml --backend fixture`
(申请书原件不在仓库内;全文以 targets 表述,figures 为 illustrative synthetic data。)

另附 [slides/](slides/):用 academic-pptx + 官方 pptx skill 从本报告再生成的 11 页开放基金
汇报 PPT(action-title 结构,含可复现脚本)。
