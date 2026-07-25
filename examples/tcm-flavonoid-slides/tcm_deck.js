// 陈皮黄酮：提取工艺优化与质量标志物 —— 硕士学位论文答辩（paper-slides / pku 主题）
const { Deck } = require("./slidekit");

const d = new Deck({
  theme: "pku", lang: "zh",
  title: "陈皮黄酮的提取工艺优化与质量标志物筛选",
  subtitle: "把“陈久者良”从经验说法变成可测的成分指标",
  shortTitle: "陈皮黄酮",
  occasion: "硕士学位论文答辩",
  presenter: "李 明", advisor: "王 立 教授",
  org: "北京大学 药学院",
  date: "2026 年 7 月",
});

d.cover({ notes: "开场：陈皮按年份卖出十倍价差，但药典只测橙皮苷一个指标——这个缺口就是本文的切入点。" });
d.toc();

// ============ 01 问题 ============
d.section("问题", "药典指标与实际质量的脱节", [
  ["一个指标定不了等级", "橙皮苷在三产地间差异不足 1.5 倍，无法区分优劣"],
  ["提取工艺各家不一", "文献报道的乙醇浓度跨度 50–90%，收率无法互比"],
  ["“陈久者良”缺证据", "年份与活性成分的定量关系尚未建立"],
]);

d.page({
  title: "陈皮是柑橘果皮的干燥饮片，按产地与陈化年份分级流通",
  blocks: [
    { type: "cols", ratio: [10, 10], cols: [
      { blocks: [{ type: "figure", path: "assets/web/peel1_2.jpg", maxH: 3.3, frame: true,
        caption: "干燥陈皮饮片的内外表面" }] },
      { blocks: [
        { type: "bullets", size: 14, gap: 0.24, items: [
          { lead: "鉴别特征：", text: "外表面棕褐、密布凹入的油室，内表面类白色并带维管束纹路——油室密度与内表面色泽是传统分级依据。" },
          { lead: "样品矩阵：", text: "新会、四川、浙江三产地，各取陈化 1、3、5 年样品，共九组；同批采收以排除年际差异。" },
          { lead: "前处理：", text: "60 ℃ 烘至恒重，粉碎过 40 目筛，避光干燥保存。" },
        ]},
      ]},
    ]},
  ],
  notes: "先让评审看到药材本体与分级依据，后面讲“为什么单一指标不够”才有落点。",
});

d.page({
  title: "药典只测橙皮苷，而它在产地间的差异远小于价格差异",
  blocks: [
    { type: "cols", ratio: [11, 9], cols: [
      { blocks: [{ type: "chart", kind: "bar", height: 3.15, numFmt: "0.0",
        valTitle: "含量 (mg·g⁻¹)", caption: "三产地六种黄酮的含量对比（合成示意数据）",
        data: [
          { name: "橙皮苷", labels: ["新会", "四川", "浙江"], values: [38.2, 31.6, 29.4] },
          { name: "川陈皮素", labels: ["新会", "四川", "浙江"], values: [4.8, 2.1, 1.6] },
          { name: "橘皮素", labels: ["新会", "四川", "浙江"], values: [3.1, 1.2, 0.9] },
        ]}]},
      { blocks: [
        { type: "bullets", size: 14, gap: 0.24, items: [
          { lead: "价格与指标脱节：", text: "新会陈皮的市价可达四川货的 8–10 倍，但橙皮苷含量只高 30%。" },
          { lead: "差异藏在多甲氧基黄酮：", text: "川陈皮素与橘皮素在新会样品中分别高 2.3 倍与 3.4 倍，而药典不测这两项。" },
          { lead: "由此产生的问题：", text: "以单一指标验收，无法把真正决定价格的成分纳入质量控制。" },
        ]},
        { type: "callout", label: "文献", size: 11.5,
          text: "《中国药典》2020 年版一部；Zhang 等 (2021) J Ethnopharmacol" },
      ]},
    ]},
  ],
  notes: "先给价格与含量的反差，评审立刻能理解问题为什么值得做。多甲氧基黄酮是全篇伏笔。",
});

d.page({
  title: "本文要做三件事：定工艺、找标志物、验活性",
  blocks: [
    { type: "callout", label: "研究目标", size: 13.5,
      text: "以响应面法确定可复现的超声辅助提取工艺，在此基础上定量六种黄酮，用多变量统计筛出能区分产地与年份的质量标志物，并以抗炎活性验证所筛标志物是否与药效相关。" },
    { type: "stats", items: [
      { value: "6 种", label: "定量黄酮", note: "HPLC-DAD 同步测定" },
      { value: "27 组", label: "工艺实验", note: "四因素三水平 BBD" },
      { value: "3 × 3", label: "样品矩阵", note: "三产地 × 三陈化年份" },
    ]},
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "bullets", size: 13.5, rule: false, items: [
        { lead: "与已有工作的区别：", text: "多数报道只优化收率；本文把“提取工艺”与“质量评价”接在一条链上。" },
      ]}]},
      { blocks: [{ type: "bullets", size: 13.5, rule: false, items: [
        { lead: "可交付的东西：", text: "一套工艺参数、一组标志物、以及二者之间的定量对应关系。" },
      ]}]},
    ]},
  ],
  notes: "三个数字对应三章。强调“接成一条链”——这是与只优化收率的工作的差别。",
});

// ============ 02 工艺 ============
d.section("提取工艺", "响应面优化与动力学", [
  ["四因素三水平", "乙醇浓度、温度、时间、液料比"],
  ["以总黄酮为响应值", "Box–Behnken 设计 27 组"],
  ["用动力学解释", "两段行为对应溶出与平衡"],
]);

d.page({
  title: "两条链在最优工艺处交接",
  blocks: [
    { type: "text", size: 13.5,
      text: "这张图回答两个问题：工艺参数在哪一步被固定下来，以及后续的定量与活性数据为什么彼此可比。" },
    { type: "figure", path: "assets/dg_flow.png", maxH: 3.5, credit: "",
      caption: "研究技术路线（Graphviz 布局引擎绘制）" },
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "bullets", size: 13, rule: false, items: [
        { lead: "工艺链：", text: "响应面把乙醇浓度、温度、时间、液料比四个参数收敛到唯一一组取值，此后不再变动。" },
      ]}]},
      { blocks: [{ type: "bullets", size: 13, rule: false, items: [
        { lead: "解析链：", text: "定量、统计与活性验证都在同一批最优工艺提取物上完成，避免跨工艺数据互不可比。" },
      ]}]},
    ]},
  ],
  notes: "先给全局图，后面每页对应图上一个方框。被问方法就回到这页定位。",
});

d.page({
  title: "六种黄酮在 28 min 内实现基线分离",
  blocks: [
    { type: "cols", ratio: [8, 12], cols: [
      { blocks: [{ type: "figure", path: "assets/web/hplc4_3.jpg", maxH: 3.4, frame: true,
        caption: "定量所用液相色谱系统" }] },
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.22, items: [
          { lead: "色谱柱与流动相：", text: "C18 柱（250 × 4.6 mm，5 μm）；0.1% 甲酸水–乙腈梯度洗脱，流速 1.0 mL·min⁻¹。" },
          { lead: "检测条件：", text: "柱温 30 ℃，进样 5 μL；黄酮苷类于 283 nm、多甲氧基黄酮于 330 nm 检测。" },
          { lead: "方法学验证：", text: "六种成分线性范围内 r² > 0.999，加样回收率 96.4–102.1%，日内精密度 RSD < 2.0%。" },
          { lead: "为什么要双波长：", text: "两类黄酮的最大吸收相差近 50 nm，单波长会低估多甲氧基黄酮——而它们正是本文的候选标志物。" },
        ]},
      ]},
    ]},
  ],
  notes: "答辩必问方法细节，这页把条件与验证数据一次给全；最后一条解释双波长，是与“候选标志物”呼应的伏笔。",
});

d.page({
  title: "乙醇浓度 70%、60 ℃、40 min 时总黄酮收率达 42.7 mg·g⁻¹",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "chart", kind: "line", height: 3.0, numFmt: "0.0",
        valTitle: "总黄酮收率 (mg·g⁻¹)", catTitle: "乙醇体积分数 (%)",
        caption: "不同温度下的乙醇浓度响应（合成示意数据）",
        data: [
          { name: "50 ℃", labels: ["30","50","60","70","80","90"], values: [21.4,30.2,35.8,38.1,35.0,28.6] },
          { name: "60 ℃", labels: ["30","50","60","70","80","90"], values: [24.8,34.6,40.2,42.7,39.4,31.2] },
          { name: "70 ℃", labels: ["30","50","60","70","80","90"], values: [25.1,34.9,39.8,41.0,37.2,29.1] },
        ]}]},
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.2, items: [
          { lead: "浓度存在极值：", text: "70% 处收率最高；再升高时黄酮苷类溶解度下降，同时蜡质与色素被大量共提。" },
          { lead: "温度收益有限：", text: "60 → 70 ℃ 收率反降 1.7 mg·g⁻¹，川陈皮素在 70 ℃ 下检出降解产物。" },
          { lead: "工艺取值：", text: "70% 乙醇、60 ℃、40 min、液料比 25∶1；三次平行的相对标准偏差 1.8%。" },
        ]},
        { type: "callout", tone: "warn", label: "说明", size: 11.5,
          text: "全篇数值为方法演示用的合成示意数据，非真实实验结果。" },
      ]},
    ]},
  ],
  notes: "讲清 70% 的极值成因（溶解度 vs 杂质共提），这是评审最常追问的点；70 ℃ 降解是不再往上加温的理由。",
});

d.page({
  title: "溶出曲线用 Weibull 模型拟合，两段行为对应不同控速步骤",
  blocks: [
    { type: "formula", path: "assets/eq/ext.png", tag: "(1)", height: 0.6,
      where: [["Y∞", "平衡收率"], ["k", "速率常数"], ["n", "形状参数，反映控速机制"]] },
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "bullets", size: 13.5, rule: false, items: [
        { lead: "前 15 min：", text: "n = 0.62 < 1，表面洗脱主导，收率达到平衡值的 78%。" },
      ]}]},
      { blocks: [{ type: "bullets", size: 13.5, rule: false, items: [
        { lead: "15 min 之后：", text: "转为细胞内扩散控速，延长到 60 min 仅再增 4%，故取 40 min。" },
      ]}]},
    ]},
    { type: "formula", path: "assets/eq/des.png", tag: "(2)", height: 0.58,
      where: [["D", "植物相与溶剂相的分配系数"], ["ΔG", "转移自由能"]] },
    { type: "text", size: 13,
      text: "式 (2) 解释了浓度极值：乙醇比例升高使 ΔG 先降后升，70% 处分配系数最有利于黄酮苷向溶剂相转移。" },
  ],
  notes: "两条式子的作用不同：式 (1) 定时间，式 (2) 定浓度。被问“为什么不用更高浓度”就用式 (2) 回答。",
});

// ============ 03 标志物 ============
d.section("质量标志物", "从含量矩阵到可判别指标", [
  ["多变量统计筛选", "OPLS-DA 的 VIP 值排序"],
  ["三个候选标志物", "两种多甲氧基黄酮 + 一种苷元"],
  ["与活性对齐", "候选物与 NO 抑制率相关"],
]);

d.page({
  title: "川陈皮素与橘皮素的 VIP 值排在最前，橙皮苷排在末位",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "chart", kind: "barh", height: 3.0, legend: false, numFmt: "0.00",
        valTitle: "VIP 值", caption: "OPLS-DA 变量重要性排序（合成示意数据）",
        data: [{ name: "VIP", labels: ["橙皮苷","柚皮苷","新橙皮苷","川陈皮素","橘皮素","5-去甲川陈皮素"],
                 values: [0.41, 0.68, 0.92, 1.86, 1.72, 1.34] }]}]},
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.2, items: [
          { lead: "判别力排序颠倒：", text: "药典指标橙皮苷的 VIP 仅 0.41，远低于阈值 1.0；三种多甲氧基黄酮全部超过阈值。" },
          { lead: "机理上说得通：", text: "橙皮苷是柑橘属普遍成分，而多甲氧基黄酮的积累与陈化过程中的脱糖苷化相关。" },
          { lead: "候选标志物：", text: "川陈皮素、橘皮素、5-去甲川陈皮素，三者组合可把九组样品完全分开。" },
        ]},
      ]},
    ]},
  ],
  notes: "这页是全文最硬的结果：药典指标判别力最低。念 VIP 值时强调阈值 1.0 这条线。",
});

d.page({
  title: "陈化三年样品中多甲氧基黄酮占比升至 21%",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "chart", kind: "doughnut", height: 2.95, holeSize: 60,
        caption: "陈化三年样品的黄酮组成（合成示意数据）",
        data: [{ name: "占比", labels: ["黄酮苷类", "多甲氧基黄酮", "其他"], values: [71, 21, 8] }]}]},
      { blocks: [{ type: "chart", kind: "bar", height: 2.95, numFmt: "0.0",
        valTitle: "占总黄酮比例 (%)", catTitle: "陈化年份",
        caption: "多甲氧基黄酮占比随陈化年份的变化（合成示意数据）",
        legend: false,
        data: [{ name: "多甲氧基黄酮占比", labels: ["1 年", "3 年", "5 年"], values: [12.4, 21.0, 26.8] }]}]},
    ]},
    { type: "text", size: 13,
      text: "占比随年份单调上升，与“陈久者良”的传统判断方向一致；但 5 年样品的总黄酮已下降 9%，说明陈化存在收益上限。" },
  ],
  notes: "环形图只讲“多甲氧基黄酮占两成”这一件事，右侧柱图给年份趋势。收益上限那句是主动交代局限。",
});

d.page({
  title: "候选标志物含量与 NO 抑制率相关，橙皮苷不相关",
  blocks: [
    { type: "table", widths: [0.3, 0.18, 0.2, 0.32],
      header: ["成分", "VIP", "与 NO 抑制率 r", "作为标志物是否成立"],
      rows: [
        ["川陈皮素", "1.86", "0.89", "成立：判别力与活性双高"],
        ["橘皮素", "1.72", "0.83", "成立"],
        ["5-去甲川陈皮素", "1.34", "0.76", "成立，但含量低、定量误差偏大"],
        ["新橙皮苷", "0.92", "0.31", "不成立：判别力不足"],
        ["橙皮苷", "0.41", "0.12", "不成立：与活性无关"],
      ]},
    { type: "callout", label: "口径", size: 12,
      text: "抑制率取 100 μg·mL⁻¹ 提取物在 RAW264.7 细胞上的三次平行均值；r 为含量与抑制率的 Pearson 系数，n = 9。" },
  ],
  notes: "逐行念，重点在最后两行：药典指标与活性无关，这是把标志物换掉的依据。",
});

// ============ 04 结论 ============
d.section("结论与不足", "结论 · 局限 · 下一步", [
  ["工艺可复现", "RSD 1.8%，参数区间明确"],
  ["标志物换人", "多甲氧基黄酮取代橙皮苷"],
  ["尚未解决", "陈化机制与批次外推"],
]);

d.page({
  title: "结论：应当以多甲氧基黄酮作为陈皮的质量标志物",
  blocks: [
    { type: "bullets", gap: 0.28, items: [
      { lead: "1. 工艺：", text: "70% 乙醇、60 ℃、40 min、液料比 25∶1，总黄酮 42.7 mg·g⁻¹，三次平行 RSD 1.8%；溶出的两段行为由式 (1) 的形状参数 n 区分。" },
      { lead: "2. 标志物：", text: "川陈皮素与橘皮素的 VIP 分别为 1.86 与 1.72，而药典指标橙皮苷仅 0.41，且与抗炎活性无相关（r = 0.12）。" },
      { lead: "3. 陈化：", text: "多甲氧基黄酮占比由 1 年的 12.4% 升至 5 年的 26.8%，但总黄酮在 5 年时已降 9%，陈化收益存在上限。" },
    ]},
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "bullets", size: 13, rule: false, items: [
        { lead: "尚未解决：", text: "脱糖苷化究竟由内源酶还是非酶反应主导，本文的数据无法区分。" },
      ]}]},
      { blocks: [{ type: "bullets", size: 13, rule: false, items: [
        { lead: "外推限制：", text: "样品仅九组、单一采收季，跨批次稳定性需扩大样本后再判。" },
      ]}]},
    ]},
    { type: "callout", label: "Q&A 导航", size: 11.5,
      text: "工艺参数 → P7；动力学与式 (1)(2) → P8；VIP 排序 → P10；活性对齐 → P12" },
  ],
  notes: "Q&A 停留本页。最可能被问：九组样品够不够（答：够支撑判别力排序，不够支撑限量标准，已写进不足）。",
});

d.refs([
  "国家药典委员会 (2020). 中华人民共和国药典（2020 年版·一部）. 中国医药科技出版社.",
  "Zhang, M., Duan, C., Zang, Y., et al. (2011). The flavonoid composition of flavedo and juice from the pummelo cultivar and grapefruit cultivar. Food Chemistry, 129, 1530–1536.",
  "Li, S., Lo, C.-Y., & Ho, C.-T. (2006). Hydroxylated polymethoxyflavones and methylated flavonoids in sweet orange peel. Journal of Agricultural and Food Chemistry, 54, 4176–4185.",
  "Wang, F., Chen, L., Chen, H., et al. (2019). Analysis of flavonoids in Citri Reticulatae Pericarpium by UPLC-Q-TOF-MS. Journal of Pharmaceutical and Biomedical Analysis, 172, 100–110.",
  "Ferreira, S.L.C., Bruns, R.E., Ferreira, H.S., et al. (2007). Box-Behnken design: An alternative for the optimization of analytical methods. Analytica Chimica Acta, 597, 179–186.",
  "Bylesjö, M., Rantalainen, M., Cloarec, O., et al. (2006). OPLS discriminant analysis: combining the strengths of PLS-DA and SIMCA classification. Journal of Chemometrics, 20, 341–351.",
]);

d.acknowledge({
  advisor: [["王 立 教授", "选题指导与全程把关"]],
  collab: [["张 华 博士", "HPLC-MS 方法学建立"], ["陈 悦", "三产地样品采集与前处理"]],
  group: "感谢药物分析课题组全体同学在实验与讨论中的帮助。",
  funding: [["国家自然科学基金", "22374012"], ["北京大学基础科研种子基金", "BMU2025SEED"]],
  facility: ["分子材料与纳米加工实验室（MMNL）", "药学院公共仪器平台"],
  notes: "致谢：念到名字即可，不逐条展开。",
});
d.closing({
  contact: "liming@pku.edu.cn",
  takeaway: "多甲氧基黄酮应取代橙皮苷，成为陈皮的质量标志物。",
  links: [["数据与代码", "github.com/liming/citri-flavone"]],
  notes: "结束页；细节问题退回结论页或对应页码。",
});

d.build("tcm_defense.pptx");
