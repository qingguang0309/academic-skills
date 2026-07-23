// MOF 高通量筛选 CO2 捕集 —— 研究生开题报告(paper-slides / pine 主题)
const { Deck } = require("./slidekit");

const d = new Deck({
  theme: "pine", lang: "zh",
  title: "面向烟气 CO₂ 捕集的 MOF 高通量计算筛选\n与机器学习加速",
  subtitle: "从 137 953 个候选结构到 50 个可实验对象的确定性路径 —— 开题报告",
  shortTitle: "MOF 高通量筛选",
  occasion: "研究生学位论文开题报告",
  presenter: "李 明", advisor: "张 伟 教授",
  org: "××大学 材料科学与工程学院",
  date: "2026 年 7 月",
});

d.cover({ notes: "开场:胺洗的再生能耗是燃烧后捕集的成本大头;吸附法的关键在材料,材料的关键在怎么从十万级候选里找到对的那几十个。" });
d.toc();

// ============ 01 选题背景与意义 ============
d.section("选题背景与意义", "为什么是 MOF,为什么要靠筛");

d.page({
  title: "燃烧后捕集是存量排放的现实路径,\n胺洗高再生能耗呼唤新一代吸附材料",
  blocks: [
    { type: "cols", ratio: [2, 3], cols: [
      { blocks: [
        { type: "figure", path: "assets/web/plant_3.jpg", maxH: 3.1 }, // 署名自动读 credits.json
      ]},
      { blocks: [
        { type: "bullets", gap: 0.26, size: 15.5, items: [
          { lead: "存量约束:", text: "燃煤与工业烟气仍将长期存在,燃烧后捕集是可改造存量源的主流路线。" },
          { lead: "现役技术痛点:", text: "MEA 胺洗再生能耗约 3.5–4 GJ/t CO₂,占捕集成本 60% 以上,且有降解与腐蚀问题。" },
          { lead: "MOF 的机会:", text: "孔化学高度可调,固体吸附再生能耗有望降至 2 GJ/t 以下——但候选空间高达十万级。" },
        ]},
      ]},
    ]},
    { type: "callout", label: "文献", size: 12.5,
      text: "Sumida et al. (2012) Chem. Rev.;Furukawa et al. (2013) Science;Boyd et al. (2019) Nature" },
  ],
  notes: "口头引文献:Sumida 2012 是 MOF 碳捕集的系统综述;Boyd 2019 证明了数据驱动设计湿烟气捕集的可行性。照片:燃煤电厂夜景(CC0)。",
});

d.page({
  title: "核心问题:计算与机器学习能否把 10⁵ 级候选空间\n可靠地压缩到 50 个可实验对象",
  blocks: [
    { type: "callout", label: "核心问题", size: 14.5,
      text: "以 GCMC 分子模拟为标尺、机器学习代理模型为加速器,能否在保持粗筛精度(MAE ≤ 0.3 mmol g⁻¹)的前提下,把 CoRE MOF 全库筛选的计算成本压缩两个数量级,并交付 50 个兼具容量、选择性与水稳定性的可合成候选?" },
    { type: "stats", items: [
      { value: "137 953", label: "候选 MOF 结构", note: "CoRE MOF 2019 全库" },
      { value: "×100", label: "筛选加速目标", note: "ML 代理 vs 纯 GCMC" },
      { value: "50", label: "实验候选清单", note: "含水稳定性约束" },
    ]},
    { type: "text", lead: "选题定位:", size: 15.5,
      text: "不造新合成路线,专注把“从库到实验清单”这一步做成可复现、可迁移的筛选管线。" },
  ],
  notes: "强调三个数字:全库规模、加速比、最终清单。管线本身是论文的可复用贡献。",
});

// ============ 02 研究内容与技术路线 ============
d.section("研究内容与技术路线", "四阶段漏斗 · GCMC 标尺 · ML 加速");

d.page({
  title: "四阶段漏斗:几何过滤与 GCMC 打底,\nML 代理承担绝大多数评价",
  blocks: [
    { type: "steps", items: [
      { title: "几何过滤", text: "孔径/比表面/密度硬约束,去除不可及结构" },
      { title: "GCMC 粗筛", text: "8 200 个结构 15:85 CO₂/N₂ 混合等温线" },
      { title: "ML 精筛", text: "代理模型 + 主动学习覆盖全库" },
      { title: "精算与验证", text: "DFT 结合能 + 水稳定性,Top-50 清单" },
    ]},
    { type: "bullets", size: 15, gap: 0.22, items: [
      { lead: "训练集设计:", text: "GCMC 粗筛结果即 ML 训练集,几何+化学描述符,主动学习按不确定性补标注。" },
      { lead: "产出物:", text: "开源筛选管线 + 全库性能数据库 + Top-50 候选清单(附合成可行性注记)。" },
    ]},
  ],
  notes: "漏斗的关键设计:昂贵计算只花在模型不确定的地方——主动学习决定 GCMC 下一步算哪些结构。",
});

d.page({
  title: "预期以 ≈2 800× 的候选压缩进入目标区:\nS ≥ 150 且 q ≥ 4 mmol g⁻¹",
  blocks: [
    { type: "figure", path: "assets/fig_screening.png", maxH: 3.75,
      caption: "四阶段筛选漏斗与容量–选择性图谱(合成示意数据,非实测)", credit: "本项目 paper-figures 规范生成" },
    { type: "callout", label: "怎么读", size: 12.5,
      text: "(a) 每一级把候选压一个量级,昂贵方法只接住上一级的幸存者;(b) Pareto 前沿逼近绿色目标区,目标区右上角即实验清单的来源。" },
  ],
  notes: "指着 (b) 讲:灰云是全体,前沿是天花板,绿区是工程要求;三者的距离就是筛选的价值。",
});

d.page({
  title: "方法有效性:等温线复现烟气工况,\n代理模型对 GCMC 的 R² 达 0.92",
  blocks: [
    { type: "figure", path: "assets/fig_isotherm.png", maxH: 3.75,
      caption: "混合气等温线与 ML–GCMC parity(合成示意数据,非实测)", credit: "本项目 paper-figures 规范生成" },
    { type: "callout", label: "验证口径", size: 12.5,
      text: "(a) 以 0.15 bar 分压(虚线)为评价点,对照 MOF-74 基准;(b) 预期 R² ≥ 0.9、MAE ≤ 0.3 mmol g⁻¹,±0.5 带内命中率 ≥ 95%。" },
  ],
  notes: "这两个面板对应开题最常被问的两个问题:评价工况是否贴近真实烟气;ML 是否可信。",
});

// ============ 03 预期成果与研究计划 ============
d.section("预期成果与研究计划", "指标绑定验证 · 两年时间表 · 风险预案");

d.page({
  title: "四项量化指标各自绑定独立验证口径",
  blocks: [
    { type: "table", widths: [0.44, 0.56],
      header: ["量化指标", "验证口径"],
      rows: [
        ["ML 代理精度:R² ≥ 0.9,MAE ≤ 0.3 mmol g⁻¹", "留出 20% GCMC 结果盲测,分孔径分区报告"],
        ["筛选加速 ≥ 100×(等精度)", "同一候选集,纯 GCMC 与管线实测机时对比"],
        ["Top-50 清单:S ≥ 150,q ≥ 4 mmol g⁻¹", "0.15 bar、313 K 混合气 GCMC 复核 + 水稳定性文献核验"],
        ["开源交付", "筛选管线代码 + 全库数据库 + 候选清单公开发布"],
      ]},
    { type: "callout", tone: "warn", label: "说明", size: 12.5,
      text: "本页与全篇数值均为开题目标而非已得结果;示意图为合成数据。" },
  ],
  notes: "每个数字都有独立于模型本身的验收办法,这是开题委员会最关心的。",
});

d.page({
  title: "两年计划:前半段建标尺,后半段换清单",
  blocks: [
    { type: "table", widths: [0.26, 0.36, 0.38],
      header: ["阶段", "时间", "里程碑"],
      rows: [
        ["方法与数据搭建", "2026.09 – 2026.12", "CoRE MOF 清洗入库;GCMC 流程对标文献基准"],
        ["高通量粗筛", "2027.01 – 2027.06", "8 200 结构混合气数据集;首版描述符库"],
        ["ML 与主动学习", "2027.07 – 2027.12", "代理模型达标(R² ≥ 0.9);全库预测完成"],
        ["精算与论文", "2028.01 – 2028.06", "Top-50 清单与开源发布;学位论文撰写"],
      ]},
  ],
  notes: "里程碑与指标一一对应:每个阶段结束都有可检查的交付物。",
});

d.page({
  title: "主要风险已备预案:精度、算力与可合成性",
  blocks: [
    { type: "cards", cols: 3, items: [
      { title: "ML 精度不达标", text: "回退主动学习加密采样;按孔径分区建模,弱区退回 GCMC 直算" },
      { title: "算力不足", text: "粗筛工况降采样(单温度双压力点);课题组集群 + 校级超算排队冗余" },
      { title: "候选不可合成", text: "清单叠加已合成子库(CoRE 实验来源)优先;与合成课题组联合评审" },
    ]},
  ],
  notes: "回应委员会两类典型质疑:模型不准怎么办;算不动怎么办;算出来做不出来怎么办。",
});

// ============ 04 总结 ============
d.section("总结", "一句话:把“找材料”做成可复现的管线");

d.page({
  title: "结论:以 GCMC 为标尺、ML 为杠杆,\n把碳捕集材料发现从经验试错推向管线化",
  blocks: [
    { type: "bullets", gap: 0.3, items: [
      { lead: "1. 问题有解且可度量:", text: "四阶段漏斗把 137 953 个候选压缩约 2 800 倍,每一级有明确准入指标。" },
      { lead: "2. 加速不以精度为代价:", text: "主动学习让昂贵计算只花在不确定处,目标等精度下提速 ≥ 100×。" },
      { lead: "3. 交付可复用:", text: "开源管线 + 全库数据库 + Top-50 实验清单,方法可迁移到其他气体分离体系。" },
    ]},
    { type: "callout", label: "Q&A 导航", size: 12.5,
      text: "技术路线 → P8;目标区证据 → P9;方法有效性 → P10;指标口径 → P12;时间表 → P13" },
  ],
  notes: "Q&A 期间停留本页。",
});

d.refs([
  "Sumida, K., Rogow, D.L., Mason, J.A., et al. (2012). Carbon dioxide capture in metal-organic frameworks. Chemical Reviews, 112, 724–781.",
  "Furukawa, H., Cordova, K.E., O'Keeffe, M., & Yaghi, O.M. (2013). The chemistry and applications of metal-organic frameworks. Science, 341, 1230444.",
  "Wilmer, C.E., Leaf, M., Lee, C.Y., et al. (2012). Large-scale screening of hypothetical metal-organic frameworks. Nature Chemistry, 4, 83–89.",
  "Chung, Y.G., Haldoupis, E., Bucior, B.J., et al. (2019). Advances, updates, and analytics for the computation-ready, experimental MOF database: CoRE MOF 2019. Journal of Chemical & Engineering Data, 64, 5985–5998.",
  "Boyd, P.G., Chidambaram, A., García-Díez, E., et al. (2019). Data-driven design of metal-organic frameworks for wet flue gas CO₂ capture. Nature, 576, 253–256.",
  "Jablonka, K.M., Ongari, D., Moosavi, S.M., & Smit, B. (2020). Big-data science in porous materials. Chemical Reviews, 120, 8066–8129.",
]);

d.page({
  kicker: "附录 A · 概念示意",
  title: "物理图像:多孔晶格捕获 CO₂,床层化实现工程放大",
  blocks: [
    { type: "figure", path: "assets/ai/concept_duo.png", maxH: 4.0,
      caption: "微观晶格吸附(a)与吸附塔床层工程化(b)的概念示意" },
    { type: "text", size: 12.5, color: "6F7873",
      text: "概念图仅用于建立物理直觉,不承载数据;单张分别生成后由 collage 确定性拼版。" },
  ],
  notes: "备被问“宏观上怎么用”时展开:微观吸附位点 → 床层 → 塔;涉及数据一律回到 P9–P12。",
});

d.closing({ contact: "liming@example.edu.cn", notes: "被追问细节时退回结论页或对应页码。" });

d.build("mof_screening_proposal.pptx");
