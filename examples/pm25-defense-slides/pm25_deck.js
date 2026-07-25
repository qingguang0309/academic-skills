// PM2.5 长期暴露与心血管疾病 —— 博士学位论文答辩(paper-slides / pku 北大主题)
const { Deck } = require("./slidekit");

const d = new Deck({
  theme: "pku", lang: "zh",
  title: "PM2.5 长期暴露与心血管疾病发病风险",
  subtitle: "基于多中心前瞻性队列的暴露–反应关系与可避免疾病负担",
  shortTitle: "PM2.5 暴露与心血管风险",
  occasion: "博士学位论文答辩",
  presenter: "李 明", advisor: "王 立 教授",
  org: "北京大学 公共卫生学院",
  date: "2026 年 7 月",
});

d.cover({ notes: "开场：PM2.5 是我国首位环境健康风险因子；高浓度段的个体水平长期证据仍薄弱，这正是本论文的切入点。" });
d.toc();

// ============ 01 研究背景与问题 ============
d.section("研究背景与问题", "高浓度段的证据缺口");

d.page({
  title: "PM2.5 位居我国环境健康风险之首，\n但高浓度段的个体水平长期证据仍然薄弱",
  blocks: [
    { type: "cols", ratio: [11, 9], cols: [
      { blocks: [{ type: "figure", path: "assets/web/haze_2.jpg", maxH: 3.5, caption: "重污染日的城市天际线" }] },
      { blocks: [
        { type: "bullets", size: 14.5, gap: 0.26, items: [
          { lead: "负担之重：", text: "PM2.5 长期暴露归因死亡居我国环境风险因子首位，心血管疾病是主要结局。" },
          { lead: "证据之偏：", text: "现有队列证据主要来自欧美低浓度地区(< 25 μg m⁻³),难以外推至我国常见的 40–80 μg m⁻³ 区间。" },
          { lead: "方法之限：", text: "国内多数研究用城市均值代替个体暴露，暴露测量误差会系统性低估效应。" },
        ]},
      ]},
    ]},
    { type: "callout", label: "文献", size: 12,
      text: "GBD 2021 Risk Factors Collaborators (2024) Lancet;Yin et al. (2017) Circulation;Liang et al. (2020) PNAS" },
  ],
  notes: "口头点出三个缺口：负担重、证据偏低浓度、暴露测量粗。本研究对应解决后两个。",
});

d.page({
  title: "核心问题：在高浓度暴露区间，PM2.5 与心血管发病的\n暴露–反应关系形状如何，达标可避免多少负担",
  blocks: [
    { type: "callout", label: "核心问题", size: 14,
      text: "以 1 km 分辨率个体化暴露评估为基础，在我国 40–80 μg m⁻³ 的高浓度区间刻画 PM2.5 与心血管疾病发病的暴露–反应关系形状，并量化不同空气质量标准情景下可避免的疾病负担。" },
    { type: "stats", items: [
      { value: "48.6 万", label: "队列人群", note: "10 省 · 45–79 岁" },
      { value: "9.8 年", label: "中位随访", note: "累计 476 万人年" },
      { value: "1 km", label: "暴露分辨率", note: "卫星–地面融合" },
    ]},
    { type: "text", lead: "论文定位：", size: 15,
      text: "不止给出一个 HR,而是同时交付关系形状、亚组一致性与政策情景下的可避免负担。" },
  ],
  notes: "这一页停留久些：三个数字是全篇的基础，后面每个结果都回到它们。",
});

// ============ 02 研究设计与方法 ============
d.section("研究设计与方法", "队列 · 暴露 · 结局 · 统计");

d.page({
  title: "总体设计：暴露链与队列链并行，在 Cox 模型处汇合",
  blocks: [
    { type: "figure", path: "assets/dg_design.png", maxH: 3.5, frame: false, credit: "",
      caption: "研究技术路线（Graphviz 布局引擎绘制）" },
    { type: "callout", label: "主线", size: 12.5,
      text: "左侧暴露链把卫星与地面数据融合到 1 km 网格，右下队列链把基线与结局数据库链接；两条链在 Cox 模型汇合，再分别输出关系形状与可避免负担。" },
  ],
  notes: "先讲这张图给评审建立全局，再逐页展开细节；被问方法时回到本页定位。",
});

d.page({
  title: "多中心前瞻性队列覆盖十省城乡，基线与结局均经标准化质控",
  blocks: [
    { type: "cards", cols: 2, items: [
      { title: "研究人群", text: "10 省 15 个中心，2013–2015 年基线纳入 45–79 岁常住居民 48.6 万人，城乡比约 6∶4" },
      { title: "基线测量", text: "统一问卷 + 体格检查 + 血样；吸烟、体力活动、BMI、血压、血脂、糖尿病史等协变量" },
      { title: "结局随访", text: "链接省级死因监测与医保住院数据库，主结局为心血管疾病首次发病(ICD-10 I00–I99)" },
      { title: "质控", text: "结局经双人独立编码复核；失访率 < 3.2%,敏感性分析排除随访首 2 年事件" },
    ]},
    { type: "text", size: 12, color: "797069",
      text: "队列构成与失访分布见附录 A;伦理审批号见论文第二章。" },
  ],
  notes: "强调结局来源是两个独立数据库链接，不依赖自报；失访率低是队列质量的关键指标。",
});

d.page({
  title: "卫星–地面融合模型把暴露评估细化到 1 km 居住地址，\n交叉验证 R² 达 0.88",
  blocks: [
    { type: "cols", ratio: [9, 11], cols: [
      { blocks: [{ type: "figure", path: "assets/web/monitor_3.jpg", maxH: 3.1, caption: "地面监测站的 PM2.5 采样入口" }] },
      { blocks: [
        { type: "bullets", size: 14, gap: 0.22, items: [
          { lead: "数据源：", text: "MODIS/MAIAC 气溶胶光学厚度 + 全国 1600 余个国控站小时浓度 + 气象再分析与土地利用。" },
          { lead: "模型：", text: "随机森林 + 时空 Kriging 残差校正，输出 1 km × 1 km 日尺度浓度场。" },
          { lead: "个体化：", text: "按基线居住地址地理编码提取，取纳入前 3 年移动平均作为长期暴露。" },
          { lead: "验证：", text: "十折交叉验证 R² = 0.88,RMSE = 9.4 μg m⁻³。" },
        ]},
      ]},
    ]},
    { type: "callout", label: "统计模型", size: 12.5,
      text: "Cox 比例风险模型(以年龄为时间尺度),按中心分层，逐步调整人口学、行为与临床协变量；关系形状用限制性立方样条(4 节点)。" },
  ],
  notes: "评审最可能问暴露误差：回答有两层——分辨率到 1 km,且用交叉验证给出误差量级。",
});

// ============ 03 主要结果 ============
d.section("主要结果", "关系形状 · 亚组一致性 · 可避免负担");

d.page({
  title: "暴露–反应关系在高浓度段未见饱和，\n每升高 10 μg m⁻³ 心血管发病风险增加 9%",
  blocks: [
    { type: "figure", path: "assets/fig_dose_forest.png", maxH: 3.7, credit: "",
      caption: "暴露–反应关系与亚组一致性分析(合成示意数据，非实测)" },
    { type: "callout", label: "怎么读", size: 12.5,
      text: "(a) 曲线在 35 μg m⁻³ 国家二级标准以上持续上升、未见平台，说明现行标准之上仍有可观风险；(b) 九个亚组方向一致，仅现吸烟者效应更强(交互 P = 0.03)。" },
  ],
  notes: "指着 (a) 讲“没有饱和”这一条：它直接支撑“标准应继续收紧”的政策含义。",
});

d.page({
  title: "高暴露组十年绝对风险高出 7.1 个百分点，\n达 WHO 指导值可避免 92% 归因发病",
  blocks: [
    { type: "figure", path: "assets/fig_burden.png", maxH: 3.7, credit: "",
      caption: "分暴露水平累积发病与达标情景归因负担(合成示意数据，非实测)" },
    { type: "callout", label: "怎么读", size: 12.5,
      text: "(a) 相对风险转化为绝对风险差，便于公众理解；(b) 情景分析给出政策梯度：达国家二级标准仅能消除约四成归因病例，趋近 WHO AQG 才能消除九成。" },
  ],
  notes: "从相对风险走到绝对风险再走到可避免负担——这是流行病学结果转化为政策语言的三步。",
});

d.page({
  title: "主要结果对协变量调整与敏感性分析稳健",
  blocks: [
    { type: "table", widths: [0.46, 0.27, 0.27],
      header: ["模型 / 敏感性分析", "HR (95% CI)", "相对主模型变化"],
      rows: [
        ["模型 1：仅调整年龄、性别、中心", "1.112 (1.083–1.142)", "+2.0%"],
        ["模型 2：加行为因素(主模型)", "1.090 (1.062–1.119)", "参照"],
        ["模型 3：再加临床指标", "1.081 (1.052–1.111)", "−0.8%"],
        ["排除随访首 2 年事件", "1.086 (1.055–1.118)", "−0.4%"],
        ["共暴露调整(NO₂、O₃)", "1.074 (1.041–1.108)", "−1.5%"],
      ]},
    { type: "callout", tone: "warn", label: "说明", size: 12,
      text: "本页与全篇数值均为方法演示用的合成示意数据，非真实队列结果；图表由本项目脚本可复现生成。" },
  ],
  notes: "逐行念：效应量在各模型间波动不超过 2%,共暴露调整后仍显著——这是稳健性的核心证据。",
});

// ============ 04 结论与创新 ============
d.section("结论与创新", "证据 · 贡献 · 局限");

d.page({
  title: "结论：高浓度区间不存在安全阈值，\n收紧标准的健康收益具有量化依据",
  blocks: [
    { type: "bullets", gap: 0.3, items: [
      { lead: "1. 关系形状：", text: "40–80 μg m⁻³ 区间暴露–反应曲线持续上升未饱和，每 10 μg m⁻³ 对应 HR = 1.09 (1.06–1.12)。" },
      { lead: "2. 人群一致性：", text: "效应在性别、年龄、城乡间方向一致；现吸烟者风险叠加更明显，提示优先干预人群。" },
      { lead: "3. 政策含义：", text: "达国家二级标准可消除约 38% 归因发病，趋近 WHO AQG 可消除 92%,为标准修订提供量化依据。" },
    ]},
    { type: "callout", label: "Q&A 导航", size: 12,
      text: "队列与质控 → P7;暴露评估 → P8;关系形状 → P10;可避免负担 → P11;敏感性分析 → P12;队列构成 → 附录 A" },
  ],
  notes: "Q&A 期间保持本页。若被问局限，转下一页。",
});

d.page({
  title: "创新点在于暴露精度与政策转化，局限已通过设计与分析部分缓解",
  blocks: [
    { type: "cards", cols: 3, items: [
      { title: "创新 · 暴露精度", text: "1 km 个体化暴露替代城市均值，交叉验证 R² = 0.88,显著降低暴露测量误差" },
      { title: "创新 · 高浓度证据", text: "填补 40–80 μg m⁻³ 区间的个体水平长期证据空白，补充以欧美低浓度为主的文献" },
      { title: "创新 · 政策转化", text: "把 HR 转化为达标情景下的可避免负担，直接对接标准修订的决策语言" },
      { title: "局限 · 迁居与暴露变动", text: "以基线地址暴露为主；敏感性分析中排除随访期内迁居者，结果未见实质改变" },
      { title: "局限 · 室内暴露", text: "缺个体室内源与通风信息；已用炊事燃料类型作代理变量部分调整" },
      { title: "局限 · 残余混杂", text: "社会经济地位测量有限；E-value 分析显示需 RR > 1.4 的未测混杂才能解释效应" },
    ]},
  ],
  notes: "主动讲局限并给出已做的缓解措施，比等评审提问更有说服力。",
});

d.refs([
  "GBD 2021 Risk Factors Collaborators (2024). Global burden and strength of evidence for 88 risk factors. The Lancet, 403, 2162–2203.",
  "Yin, P., Brauer, M., Cohen, A., et al. (2017). Long-term fine particulate matter exposure and nonaccidental and cause-specific mortality in a large national cohort of Chinese men. Environmental Health Perspectives, 125, 117002.",
  "Liang, F., Liu, F., Huang, K., et al. (2020). Long-term exposure to fine particulate matter and cardiovascular disease in China. Journal of the American College of Cardiology, 75, 707–717.",
  "Di, Q., Wang, Y., Zanobetti, A., et al. (2017). Air pollution and mortality in the Medicare population. New England Journal of Medicine, 376, 2513–2522.",
  "Brauer, M., Brook, J.R., Christidis, T., et al. (2022). Mortality–air pollution associations in low exposure environments. Research Report, Health Effects Institute, 212.",
  "World Health Organization (2021). WHO global air quality guidelines: particulate matter, ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide. WHO, Geneva.",
]);

d.page({
  kicker: "附录 A · 队列构成",
  title: "十省十五中心的人群分布与暴露水平概览",
  blocks: [
    { type: "table", widths: [0.28, 0.18, 0.18, 0.18, 0.18],
      header: ["区域", "中心数", "人数(万)", "PM2.5 均值", "失访率"],
      rows: [
        ["华北", "4", "13.8", "62.4 μg m⁻³", "3.0%"],
        ["华东", "4", "14.2", "45.1 μg m⁻³", "2.6%"],
        ["华中 / 华南", "3", "9.6", "40.8 μg m⁻³", "3.4%"],
        ["西北 / 西南", "4", "11.0", "51.7 μg m⁻³", "3.9%"],
      ]},
    { type: "text", size: 12, color: "797069",
      text: "合成示意数据，用于展示答辩材料的版式与结构。" },
  ],
});

d.closing({ contact: "liming@pku.edu.cn", notes: "结束页；被追问细节时退回结论页或附录。" });

d.build("pm25_defense.pptx");
