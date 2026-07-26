// 钙钛矿太阳能电池的湿热稳定性 —— 硕士学位论文答辩（paper-slides / pku 主题）
// 数据为合成示意值，用于演示版式；真实汇报请替换为自己的测量结果。
const { Deck } = require("./slidekit");

const d = new Deck({
  theme: "pku", lang: "zh", kind: "defense",
  // plate 封面:校徽横排在左上、地标线描沉进底部红带——与参考的真实汇报同构
  coverStyle: "plate",
  // 手动断行：14 字标题在 42pt / 7.59in 下会折成 "…稳定\n性"，末行留一个孤字
  title: "钙钛矿太阳能电池的\n湿热稳定性",
  subtitle: "把封装从“挡水”重新定义为“抬高迁移势垒”",
  shortTitle: "钙钛矿湿热稳定性",
  occasion: "硕士学位论文答辩",
  presenter: "李 明", advisor: "王 立 教授",
  org: "北京大学 材料科学与工程学院",
  date: "2026 年 7 月",
});

d.cover({ notes: "开场：钙钛矿的效率早已追平晶硅，卡住产业化的是寿命。本文把封装从经验试错变成有机理依据的设计。" });
d.toc();

// ============ 01 问题 ============
d.section("问题", "效率达标，寿命没达标", [
  ["效率已经不是瓶颈", "认证效率 26.7%，与单晶硅持平"],
  ["寿命差了一个数量级", "湿热 T80 约 1 850 h，标准要求 25 000 h"],
  ["封装被当成挡水层", "只压 WVTR，不看降解走的是哪条路径"],
]);

d.page({
  title: "十二年里效率翻了近一倍，湿热寿命却仍差一个数量级",
  blocks: [
    { type: "cols", ratio: [1.18, 1], cols: [
      { blocks: [{ type: "figure", path: "assets/fig_gap.png", maxH: 3.4,
        caption: "认证效率与湿热 T80 寿命的十二年走势（合成示意数据）" }] },
      { blocks: [
        { type: "bullets", size: 14, gap: 0.24, items: [
          { lead: "效率侧已收敛：", text: "2021 年后每两年只涨 0.5 个百分点，材料体系基本定型。" },
          { lead: "寿命侧仍在爬坡：", text: "T80 从 50 h 涨到 1 850 h，但 IEC 61215 的门槛是 25 000 h。" },
          { lead: "两条曲线的斜率不同：", text: "效率靠组分与界面优化就能推进，寿命受制于降解动力学，不会自动跟上。" },
        ]},
      ]},
    ]},
  ],
  source: "NREL Best Research-Cell Efficiency Chart (2025); IEC 61215-1-1:2021",
  notes: "这一页只讲一件事：卡住产业化的不是效率。评审若追问 T80 定义，退到公式页。",
});

d.page({
  title: "湿热 85/85 是最苛刻的一关，它同时激活水解与离子迁移",
  blocks: [
    { type: "cols", ratio: [1, 1.1], cols: [
      { blocks: [{ type: "figure", path: "assets/solar_panel_array_field_2.jpg", maxH: 3.1,
        caption: "户外电站的组件阵列：湿热与温度循环是实际服役中的主导应力" }] },
      { blocks: [
        { type: "bullets", size: 14, gap: 0.22, items: [
          { lead: "为什么是 85/85：", text: "85 ℃ 让离子迁移的时间尺度落进实验室可测范围，85% RH 保证水汽始终过量。" },
          { lead: "两种机制同时开工：", text: "水分子先与钙钛矿形成水合相，随后碘化物沿晶界迁移——单看任一条都低估衰减速度。" },
          { lead: "不能用高温干热替代：", text: "干热只加速迁移，测不出水合这一步，会把封装需求估低。" },
        ]},
        { type: "stats", items: [
          { value: "85 ℃", label: "试验温度" },
          { value: "85%", label: "相对湿度" },
          { value: "1 000 h", label: "IEC 单轮时长" },
        ]},
      ]},
    ]},
  ],
  notes: "照片是真实电站，用来把实验室条件和服役场景连起来。",
});

// ============ 02 降解机理 ============
d.section("降解机理", "先弄清水汽进来之后发生了什么", [
  ["三条路径并行", "有机阳离子逸出、碘迁移、界面析出 PbI₂"],
  ["温度决定谁先到", "活化能相差一倍以上，主导路径随温度切换"],
  ["这决定了封装该防什么", "只挡水解决不了迁移"],
]);

d.page({
  title: "水汽进入后分成三条并行路径，本文在入口与势垒两处干预",
  blocks: [
    { type: "figure", path: "assets/flow_degrade.png", maxH: 3.3, credit: "",
      caption: "湿热降解的路径分解与两处干预点" },
    { type: "bullets", size: 13.5, gap: 0.2, items: [
      { lead: "为什么要分路径：", text: "三条路径的活化能不同，主导者随温度切换；把它们混作“降解”一个词，就无法判断某种封装到底拦住了哪一条。" },
    ]},
  ],
  notes: "流程图是全篇骨架，后面每一页都能挂回这三条路径上。",
});

d.page({
  title: "碘迁移的活化能是 0.68 eV，落在 85 ℃ 下最容易被激活的区间",
  blocks: [
    { type: "cols", ratio: [1.1, 1], cols: [
      { blocks: [{ type: "figure", path: "assets/fig_ea.png", maxH: 3.0,
        caption: "三条路径的表观活化能（n = 5，误差棒为标准差）" }] },
      { blocks: [
        { type: "bullets", size: 14, gap: 0.22, items: [
          { lead: "阳离子逸出最先启动：", text: "0.42 eV，但它受限于表面积，在致密膜里贡献有限。" },
          { lead: "碘迁移是主导项：", text: "0.68 eV 对应 85 ℃ 下约 4×10⁴ s⁻¹ 的跳跃频率，与实测衰减时间尺度一致。" },
          { lead: "PbI₂ 析出是后果不是原因：", text: "0.94 eV，只有前两步先发生才观察得到。" },
        ]},
        { type: "callout", label: "推论", size: 13,
          text: "封装若只降 WVTR，压住的是第一步；碘迁移一旦启动，残余水汽也足以维持。" },
      ]},
    ]},
  ],
  source: "Yang 等 (2019) Nat. Commun. 10, 4498；本组 2025 年变温阻抗实测",
  notes: "这是全篇最关键的一个数字。评审若问活化能怎么定的，退到下一页的公式。",
});

d.page({
  title: "用 Arrhenius 关系把活化能与加速倍率对应起来",
  blocks: [
    { type: "cols", ratio: [1.3, 1], cols: [
      { blocks: [
        { type: "formula", path: "assets/eq/arr.png", height: 0.70, tag: "(1)",
          where: [["k(T)", "温度 T 下的降解速率常数"], ["A", "指前因子"],
                  ["Ea", "表观活化能，由变温实验的斜率给出"]] },
        { type: "formula", path: "assets/eq/wvtr.png", height: 0.70, tag: "(2)",
          where: [["D", "水汽在阻隔层中的扩散系数"], ["S", "溶解度"],
                  ["L", "阻隔层厚度"], ["t(lag)", "水汽穿透的滞后时间"]] },
        { type: "formula", path: "assets/eq/t80.png", height: 0.66, tag: "(3)",
          where: [["β", "Weibull 形状因子，指示限速步类型"], ["τ", "特征寿命"]] },
      ]},
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.22, items: [
          { lead: "为什么只能报表观值：", text: "三条路径并行时，式 (1) 测到的是加权结果，权重随温度改变——这正是活化能不能跨温区外推的原因。" },
          { lead: "滞后时间比稳态更要紧：", text: "式 (2) 的滞后时间决定封装在多久之后才开始失效；实验室短时测试常常整段落在滞后期内，因而高估阻隔能力。" },
          { lead: "β 才是机理证据：", text: "式 (3) 中 β < 1 对应表面主导，β ≈ 1 对应体相扩散主导；T80 只说“多久”，β 说“为什么”。" },
        ]},
        { type: "callout", label: "取值", size: 12.5,
          text: "本文 A = 2.1×10⁸ s⁻¹，变温区间 55—95 ℃，五个温度点线性拟合 R² = 0.994。" },
      ]},
    ]},
  ],
  notes: "公式页不逐条念，只说明每个量是怎么测出来的。",
});

// ============ 03 封装策略 ============
d.section("封装策略", "从挡水改为抬高势垒", [
  ["先把入口关小", "原子层沉积 Al₂O₃ 把 WVTR 压三个量级"],
  ["再把势垒抬高", "晶界钝化让碘迁移在室温下走不动"],
  ["两者缺一不可", "单独用任一种，T80 都停在 800 h 量级"],
]);

d.page({
  title: "封装叠层的作用分工：阻隔层管入口，钝化层管势垒",
  blocks: [
    { type: "cols", ratio: [1, 1.15], cols: [
      { blocks: [{ type: "figure", path: "assets/encapsulation_lamination_1.jpg", maxH: 3.0,
        caption: "封装胶膜的荧光检查：用于判断层压后有无空隙与分层" }] },
      { blocks: [
        { type: "steps", size: 13.5, items: [
          { title: "原子层沉积 Al₂O₃（20 nm）", text: "在 80 ℃ 下沉积，避免热损伤钙钛矿层；WVTR 降至 10⁻⁴ g·m⁻²·d⁻¹ 量级。" },
          { title: "晶界钝化（苯乙铵碘）", text: "在晶界处形成二维层，把碘空位的迁移势垒抬高约 0.3 eV。" },
          { title: "EVA 层压 + 边缘密封", text: "承担机械保护与边缘路径封堵，单独使用时阻隔能力有限。" },
        ]},
        { type: "table", header: ["层", "作用对象", "关键指标"], rows: [
          ["Al₂O₃", "水汽入口", "WVTR 3×10⁻⁴ g·m⁻²·d⁻¹"],
          ["苯乙铵碘", "碘迁移势垒", "ΔEa ≈ +0.3 eV"],
          ["EVA + 边封", "机械与边缘路径", "剥离强度 > 60 N·cm⁻¹"],
        ]},
      ]},
    ]},
  ],
  notes: "照片是真实的封装胶膜检查，用来说明层压质量本身也是变量。",
});

d.page({
  title: "阻隔层把 WVTR 压了三个量级，但单独用它只把 T80 推到 780 h",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [
        { type: "chart", kind: "bar", height: 2.9, legend: false, numFmt: "0",
          valTitle: "湿热 T80 (h)",
          caption: "三种封装方案的湿热 T80（合成示意数据）",
          data: [{ name: "T80", labels: ["无封装", "单层 EVA", "EVA + Al₂O₃"],
                   values: [260, 780, 1980] }] },
      ]},
      { blocks: [
        { type: "bullets", size: 14, gap: 0.22, items: [
          { lead: "阻隔提升是必要的：", text: "从无封装到 EVA + Al₂O₃，T80 提高 7.6 倍。" },
          { lead: "但收益不成比例：", text: "WVTR 降了三个量级，T80 只涨了不到一个量级——说明限速步已经不是水汽进入。" },
          { lead: "剩下的差距在势垒：", text: "残余水汽已足以维持碘迁移，这一步只能靠钝化去拦。" },
        ]},
        { type: "stats", items: [
          { value: "10³×", label: "WVTR 降幅" },
          { value: "3.0×", label: "T80 增幅" },
          { value: "780 h", label: "阻隔单独的上限" },
        ]},
      ]},
    ]},
  ],
  notes: "这一页是全篇的转折：把“阻隔不够”这个判断用数据立住。",
});

d.page({
  title: "阻隔与钝化叠加后，T80 达到 1 980 h，衰减由指数转为近线性",
  blocks: [
    { type: "cols", ratio: [1.15, 1], cols: [
      { blocks: [{ type: "figure", path: "assets/fig_aging.png", maxH: 3.2,
        caption: "三种方案的归一化效率衰减曲线（阴影为 n = 3 的极差）" }] },
      { blocks: [
        { type: "bullets", size: 14, gap: 0.22, items: [
          { lead: "形状变了，不只是变慢：", text: "Weibull 指数 β 从 0.85 升到 1.05，衰减从“前期陡降”转为近似匀速。" },
          { lead: "这说明限速步换了：", text: "β < 1 对应表面主导，β ≈ 1 对应体相扩散主导，与钝化封住晶界通路一致。" },
          { lead: "距离标准仍有差距：", text: "1 980 h 对 25 000 h，需要在钝化层的热稳定性上继续做。" },
        ]},
      ]},
    ]},
  ],
  source: "本组 2025—2026 年湿热老化实测（n = 3）",
  notes: "β 的变化是本文最有说服力的机理证据，比 T80 数字本身更重要。",
});

d.page({
  title: "制样与测试流程：每一步都控住了会影响寿命的变量",
  blocks: [
    { type: "cols", ratio: [1, 1.1], cols: [
      { blocks: [{ type: "figure", path: "assets/spin_coating_laboratory_1.png", maxH: 3.0,
        caption: "手套箱内的旋涂制样：水氧含量全程低于 0.1 ppm" }] },
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.2, items: [
          { lead: "制样：", text: "反溶剂一步法，手套箱内完成；同一批次内器件效率标准差控制在 0.6% 以内。" },
          { lead: "封装：", text: "Al₂O₃ 沉积温度 80 ℃、200 循环；层压 145 ℃ / 12 min。" },
          { lead: "老化：", text: "双 85 箱连续运行，每 100 h 取出测 J–V，测试环境 25 ℃ / 40% RH。" },
          { lead: "统计：", text: "每组 3 片，报告极差而非标准差——样本量不足以支持标准差。" },
        ]},
        { type: "callout", label: "已控变量", size: 12.5,
          text: "同批次退火时间、封装前静置时长、老化箱内位置三项均做了随机化；未控住的是钙钛矿薄膜的晶粒尺寸分布，它随批次波动约 15%。" },
      ]},
    ]},
  ],
  notes: "方法页的作用是让评审相信数据；重点说清哪些变量被控住了。",
});

// ============ 04 结论与不足 ============
d.section("结论与不足", "结论、边界、下一步", [
  ["主要结论", "碘迁移是限速步，封装要抬势垒而非只挡水"],
  ["边界", "结论基于 85/85 单一应力，未含光照与温度循环"],
  ["下一步", "钝化层的热稳定性是新的限制项"],
]);

d.page({
  title: "结论：封装的设计目标应从 WVTR 转向碘迁移势垒",
  blocks: [
    { type: "bullets", size: 15, gap: 0.28, items: [
      { lead: "1. 机理：", text: "湿热降解由三条并行路径构成，85 ℃ 下碘迁移（Ea = 0.68 eV）是限速步；PbI₂ 析出是结果而非起因。" },
      { lead: "2. 策略：", text: "原子层沉积 Al₂O₃ 把 WVTR 压低三个量级，T80 达 780 h；叠加晶界钝化后达 1 980 h，为无封装的 7.6 倍。" },
      { lead: "3. 证据：", text: "Weibull 指数从 0.85 升至 1.05，衰减机制由表面主导转为体相扩散主导，与钝化封住晶界通路的预期一致。" },
    ]},
    { type: "callout", label: "不足", size: 13.5,
      text: "结论仅覆盖 85/85 单一应力；光照与温度循环下的耦合失效未纳入，且钝化层自身在 85 ℃ 长时间下的稳定性尚未单独考察。" },
    { type: "cards", size: 13, items: [
      { title: "下一步 · 钝化层热稳定性", text: "二维层在 85 ℃ 下会缓慢相变，需要单独做 1 000 h 的等温跟踪。" },
      { title: "下一步 · 双应力耦合", text: "在 85/85 基础上叠加 1 sun 连续光照，判断光致离子迁移是否改变限速步。" },
      { title: "下一步 · 从器件到组件", text: "现有结论基于 0.1 cm² 小面积器件，边缘路径在组件尺度上权重会显著上升。" },
    ]},
  ],
  source: "全篇数据为合成示意值，用于版式演示",
  notes: "Q&A 导航：机理问题回 P8/P9，工艺问题回 P12/P15，数据统计问题回 P15。",
});

d.refs([
  "国家标准化管理委员会. 地面用光伏组件设计鉴定和定型: IEC 61215-1-1:2021[S]. 2021.",
  "NREL. Best Research-Cell Efficiency Chart[EB/OL]. (2025)[2026-07-01]. nrel.gov/pv/cell-efficiency.html.",
  "YANG S, CHEN S, MOSCONI E, et al. Stabilizing halide perovskite surfaces for solar cell operation[J]. Science, 2019, 365(6452): 473-478.",
  "LEIJTENS T, EPERON G E, NOEL N K, et al. Stability of metal halide perovskite solar cells[J]. Adv Energy Mater, 2015, 5(20): 1500963.",
  "CHENG Y, DING L. Pushing commercialization of perovskite solar cells by improving their intrinsic stability[J]. Energy Environ Sci, 2021, 14(6): 3233-3255.",
]);

d.acknowledge({
  advisor: [["王 立 教授", "选题指导与全程把关"]],
  collab: [["张 华 博士", "原子层沉积工艺与阻隔性测试"], ["陈 悦", "变温阻抗谱与活化能拟合"]],
  group: "感谢材料化学课题组全体同学在制样与老化测试中的协助。",
  funding: [["国家自然科学基金", "52372234"], ["北京大学基础科研种子基金", "BMU2026SEED"]],
  facility: ["分子材料与纳米加工实验室（MMNL）", "工学院公共表征平台"],
  notes: "致谢：念到名字即可，不逐条展开。",
});

d.closing({
  takeaway: "封装的目标不是挡水，是把碘迁移的势垒抬到室温下走不动。",
  contact: "liming@pku.edu.cn",
  links: [["数据与代码", "github.com/liming/pvsk-damp-heat"]],
  notes: "结束页；细节问题退回对应页码，导航见结论页备注。",
});

d.build("pvsk_defense.pptx");
