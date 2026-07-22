// BSE-EDS 开放基金汇报 —— paper-slides skill (slidekit) 版本
const { Deck } = require("./slidekit");

const d = new Deck({
  theme: "azure", lang: "zh",
  title: "BSE–EDS 多模态融合:\n突破水泥基材料微观相识别的灰度天花板",
  subtitle: "水泥基材料微观相识别与水化程度智能表征 —— 研究计划",
  shortTitle: "BSE–EDS 多模态融合",
  occasion: "开放基金项目研究计划汇报",
  presenter: "非金属材料AI+实验室",
  org: "中国建筑材料科学研究总院(CBMA)",
  date: "2026 年 7 月",
});

d.cover({ notes: "开场:BSE 单模态的天花板是信息问题,不是模型问题;本项目用最少的化学采样把它补上。" });
d.toc();

// ============ 01 研究背景 ============
d.section("研究背景", "灰度天花板从哪里来");

d.page({
  title: "低碳混合材体系已成常态,掺合料与水化产物灰度重叠,\nBSE 单模态分割触及信息天花板",
  blocks: [
    { type: "bullets", gap: 0.3, items: [
      { lead: "混合材是低碳主路线:", text: "矿渣、粉煤灰、偏高岭土、石灰石大比例替代熟料,混合体系成为工程常态。" },
      { lead: "灰度退化:", text: "SCM 颗粒及其反应边与水化产物灰度区间重叠,单一强度通道无法区分化学上不同的相。" },
      { lead: "架构调优已无增益:", text: "FCN、U-Net 等 BSE-only 模型对灰度重叠相继续调参基本无增益——上限在模态,不在模型。" },
    ]},
    { type: "callout", label: "文献", size: 12.5,
      text: "Scrivener (2004) Cem Concr Compos;Lothenbach et al. (2011) CCR;Juenger & Siddique (2015) CCR" },
  ],
  notes: "口头引出文献:Scrivener 2004 奠定 BSE 定量分析;Lothenbach/Juenger 说明混合材已是主流——问题因此普遍而尖锐。",
});

d.page({
  title: "核心科学问题:少量而聪明的化学采样,能否补上 BSE 缺失的信息维度",
  blocks: [
    { type: "callout", label: "核心问题", size: 14.5,
      text: "以 ≤5% 视场覆盖的稀疏 EDS 采样,经配准门控的图注意力融合网络注入 BSE 形貌特征——能否将灰度重叠相的像素级分割 IoU 提升 ≥20 个百分点,并支撑水化程度的准确、高效表征?" },
    { type: "stats", items: [
      { value: "≤5%", label: "EDS 视场覆盖", note: "稀疏采样预算" },
      { value: "+20 pp", label: "灰度重叠相 IoU", note: "相对 BSE-only 基线" },
      { value: "−50%", label: "EDS 机时", note: "同等精度下" },
    ]},
    { type: "text", lead: "关键构想:", size: 15.5,
      text: "把 EDS 从被动的验证仪器,改造成由模型主动指挥的化学信息供给——模型自己决定实验下一步看哪里。" },
  ],
  notes: "这一页停留久一点:后续内容都服务于这个问题。强调 ≤5% 与 +20 pp 两个数字。",
});

// ============ 02 研究方案 ============
d.section("研究方案", "配对数据集 · 两阶段融合网络 · 主动采样");

d.page({
  title: "4 体系 × 4 掺量 × 6 龄期的配对数据集,为训练与验证提供系统覆盖",
  blocks: [
    { type: "cards", cols: 2, items: [
      { title: "胶材体系", text: "P.I 42.5 基准,分别复掺矿渣、粉煤灰、石灰石,覆盖主流低碳配比路线" },
      { title: "掺量与龄期", text: "替代率 0 / 20 / 40 / 60 wt%(w/b = 0.4);龄期 1 / 3 / 7 / 28 / 90 / 180 d" },
      { title: "配对采集", text: "同视场 BSE 高分辨图 + EDS 六元素图(Ca/Si/Al/Fe/Mg/S),≥3000 组配对图像" },
      { title: "标注质量", text: "≥600 幅像素级相标注,经 QXRD、TGA、EDS 点分析三重交叉核验" },
    ]},
    { type: "text", size: 12.5, color: "6E7681", text: "合成示例视场见附录 A;定量 BSE 实践遵循 Scrivener (2004)。" },
  ],
  notes: "强调配对与交叉核验:标签质量决定 +20 pp 是否可信。",
});

d.page({
  title: "两阶段网络:配准残差 <1 px 才进入融合,\n稀疏化学信息沿超像素图传播补全",
  blocks: [
    { type: "cols", ratio: [13, 6], cols: [
      { blocks: [ { type: "figure", path: "assets/bse_eds_architecture.png", frame: false, maxH: 4.15,
                    caption: "四阶段融合分割架构", credit: "本项目 figflow 生成" } ] },
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.24, items: [
          { lead: "两步配准:", text: "刚性互信息 + 可学习形变场,达标才放行" },
          { lead: "双分支编码:", text: "CNN 稠密形貌 ∥ GNN 化学梯度约束超像素图" },
          { lead: "融合输出:", text: "多尺度注意力 → 像素级相分割与相分数" },
        ]},
        { type: "callout", size: 12, label: "机制", text: "配准不达标的视场不进入融合,配准误差从机制上被隔离" },
      ]},
    ]},
  ],
  notes: "按 ①→④ 走一遍架构图;方法基础:Maes 1997 互信息配准、Achanta 2012 SLIC、Ronneberger 2015 U-Net。",
});

d.page({
  title: "不确定性驱动的主动采样闭环:模型指挥 EDS 看哪里",
  blocks: [
    { type: "steps", items: [
      { title: "不确定性估计", text: "MC-dropout / 深度集成,像素级熵图" },
      { title: "高熵区聚类", text: "相可分性判据圈定信息价值最高区域" },
      { title: "定向 EDS 采集", text: "仪器只测模型点名的位置" },
      { title: "融合更新", text: "新化学证据沿超像素图传播,迭代收敛" },
    ]},
    { type: "bullets", size: 15, gap: 0.22, items: [
      { lead: "效率目标:", text: "同等精度下 EDS 机时较均匀随机采样减少 ≥50%,以实录 dwell 与 mapping 时间日志验证。" },
      { lead: "下游任务:", text: "分割导出的水化程度、孔隙率、相分数与相邻接特征,输入水化程度与强度预测器,留一体系外推检验泛化。" },
    ]},
  ],
  notes: "闭环是本项目区别于\"先测后融\"方案的核心:采样本身被学习信号驱动。",
});

// ============ 03 预期成果 ============
d.section("预期成果", "量化指标 · 独立验证协议 · 开放交付");

d.page({
  title: "预期以 ≤5% EDS 覆盖将灰度重叠相 IoU 提升 ≥20 pp,\n同等精度下机时减半",
  blocks: [
    { type: "figure", path: "assets/fig-002.png", maxH: 3.55, frame: false,
      caption: "IoU–覆盖率目标曲线与机时对比(合成示意数据,非实测)", credit: "本项目 paperflow 生成" },
    { type: "callout", label: "怎么读", size: 13,
      text: "两条曲线的间隔即化学信息的价值:主动选点用 5% 覆盖换 ≥20 pp;BSE-only 基线停在 0.55,与架构无关。" },
  ],
  notes: "指着 (a) 双箭头讲 +20 pp;(b) 48% vs 100% 讲机时。明确声明是申报目标。",
});

d.page({
  title: "四项量化指标各自绑定独立于模型的验证协议",
  blocks: [
    { type: "table", widths: [0.42, 0.58],
      header: ["量化指标", "验证协议"],
      rows: [
        ["灰度重叠相 IoU 提升 ≥20 pp(≤5% 覆盖)", "留出像素级标注测试集;标签经 EDS 点分析核验"],
        ["分割推算水化程度误差 ≤5%", "与 TGA 独立测量对照,覆盖全部配比与龄期"],
        ["同等精度下 EDS 机时节省 ≥50%", "同视场实录 dwell 与 mapping 时间日志"],
        ["数据、权重、报告模块开放交付", "≥3000 配对 + ≥600 标注数据集;CBMA 微调权重;自动报告模块"],
      ]},
    { type: "callout", tone: "warn", label: "说明", size: 12.5,
      text: "全篇数值均为申报目标而非已得结果;示意图为合成数据。交付物存入 CBMA 无机非金属材料数据节点。" },
  ],
  notes: "逐行念指标;评审最关心每个数字都有独立于模型的验收办法。",
});

d.page({
  title: "主要风险已前置处置:门控、外推检验与自证机制",
  blocks: [
    { type: "cards", cols: 3, items: [
      { title: "配准漂移与充电畸变", text: "刚性 + 形变两步配准,人工地标残差 <1 px 方可进入分割阶段" },
      { title: "跨体系泛化", text: "留一体系外推检验微观中间变量是否优于仅配比基线" },
      { title: "不确定性质量", text: "高熵聚类直接驱动主动采样,采样收益即其有效性自证" },
    ]},
  ],
  notes: "主动回应评审两个最可能的质疑:配准误差会不会污染融合;换一个胶材体系还灵不灵。",
});

// ============ 04 总结 ============
d.section("总结", "一句话:补化学维度,而不是继续调模型");

d.page({
  title: "结论:以最小化学采样代价,把定量 SEM 表征推向常规可部署",
  blocks: [
    { type: "bullets", gap: 0.32, items: [
      { lead: "1. 突破口在模态,不在模型:", text: "补上化学维度,目标以 ≤5% 稀疏 EDS 将灰度重叠相 IoU 提升 ≥20 pp。" },
      { lead: "2. EDS 角色重构:", text: "从被动验证到模型主动指挥的化学信息供给,同等精度下机时目标 −≥50%。" },
      { lead: "3. 可复用的智能表征能力:", text: "开放数据集 + CBMA 微调权重 + 自动报告模块,接入 CBMA 数据节点。" },
    ]},
    { type: "callout", label: "Q&A 导航", size: 12.5,
      text: "数据集细节 → P7;网络架构 → P8;指标与验证 → P11;合成示例 → 附录 A" },
  ],
  notes: "Q&A 期间保持本页。",
});

d.refs([
  "Scrivener, K.L. (2004). Backscattered electron imaging of cementitious microstructures. Cement and Concrete Composites, 26, 935–945.",
  "Lothenbach, B., Scrivener, K., & Hooton, R.D. (2011). Supplementary cementitious materials. Cement and Concrete Research, 41, 1244–1256.",
  "Juenger, M.C.G., & Siddique, R. (2015). Recent advances in understanding the role of SCMs in concrete. Cement and Concrete Research, 78, 71–80.",
  "Maes, F., Collignon, A., et al. (1997). Multimodality image registration by maximization of mutual information. IEEE Trans. Med. Imaging, 16, 187–198.",
  "Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional networks for biomedical image segmentation. LNCS, 9351, 234–241.",
  "Achanta, R., Shaji, A., et al. (2012). SLIC superpixels compared to state-of-the-art superpixel methods. IEEE TPAMI, 34, 2274–2282.",
  "Long, J., Shelhamer, E., & Darrell, T. (2015). Fully convolutional networks for semantic segmentation. CVPR 2015, 3431–3440.",
]);

d.page({
  kicker: "附录 A · 合成示例视场",
  title: "从灰度退化的 BSE 视场到相图:稀疏采样点经超像素图传播补全",
  blocks: [
    { type: "cols", ratio: [10, 9], cols: [
      { blocks: [ { type: "figure", path: "assets/fig-000.png", maxH: 4.5, frame: false } ] },
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.24, items: [
          { lead: "(a) 合成 BSE:", text: "偏高岭土与矿渣灰度几乎相同,BSE-only 不可分" },
          { lead: "(b) 稀疏 EDS:", text: "覆盖 ≤5%,按真值相着色" },
          { lead: "(c) 超像素图:", text: "含样本节点实心着色,灰色小节点待图传播补全" },
          { lead: "(d) 真值相图:", text: "同一视场、同一配色,细白线为相界" },
        ]},
        { type: "text", size: 12, color: "6E7681",
          text: "合成示意数据(高斯滤波随机场生成),非实测——本项目 paperflow 生成。" },
      ]},
    ]},
  ],
});

d.closing({ contact: "github.com/qingguang0309/academic-skills",
  notes: "结束页;若被追问细节,退回结论页或对应附录。" });

d.build("bse_eds_grant_briefing.pptx");
