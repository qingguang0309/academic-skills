// 通向 2030 年的人工智能算力曲线 —— 学术报告（paper-slides / claude 主题，无校徽）
// 内容与 ../ai-2030-forecast/paper.tex 同源；四份一手来源均已核实，图中不出现无出处数值。
const { Deck } = require("./slidekit");

const d = new Deck({
  theme: "claude", lang: "zh", kind: "groupmeeting", coverStyle: "split",
  // claude 主题本身不带任何校徽；显式置 false 是为了防止将来换主题时被默认值带回来
  logo: false, seal: false,
  // 首尾页的极淡底图（输电塔剪影）。淡化已烘焙进 PNG，见 make_bg.py；
  // 选输电塔而非通用风景：本报告的结论就是电力最先咬合，底图与论点同源。
  bgArt: "assets/bg_grid.png",
  bgArtBlock: "assets/bg_block.png",   // 左侧竖块上的同源肌理，与右侧跨接缝延续
  coverMark: "assets/claude_mark.png", coverMarkH: 1.5,  // 色块左上角的白色标识
  title: "通向 2030 年的\n人工智能算力曲线",
  subtitle: "外推、约束，与最先触及的那堵墙",
  shortTitle: "AI 算力曲线 2030",
  occasion: "学术报告",
  presenter: "李 明",
  org: "计算科学与人工智能实验室",
  date: "2026 年 8 月",
});

d.cover({ notes: "开场：这个题目吵不出结果，是因为双方没有共同的单位。今天我把它换成一个能算的问题。" });
d.toc();

// ============ 01 问题 ============
d.section("问题", "把不可证伪的争论换成可计算的量", [
  ["“会不会更强”无法证伪", "双方对“强”的度量不一致，争不出结果"],
  ["算力是可算的代理量", "有单位、有历史序列、有标度律绑定规模与数据"],
  ["代价要先讲清", "算力不等于能力，最后一节回到这一点"],
]);

d.page({
  title: "把问题收窄到单次训练算力，分歧才变得可以计算",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [
        { type: "bullets", size: 15, gap: 0.26, items: [
          { lead: "为什么选算力：", text: "它有明确单位（FLOP），有公开的历史序列，并通过标度律与模型规模、数据量建立定量联系。" },
          { lead: "收窄的代价：", text: "算力不等于能力，两者之间隔着“算力→损失”与“损失→任务表现”两层映射。" },
          { lead: "收窄的收益：", text: "各方的判断可以折算到同一套单位里，分歧从此可以定位而不只是表态。" },
        ]},
      ]},
      { blocks: [
        { type: "formula", path: "assets/eq/cnd.png", height: 0.8, tag: "(1)",
          where: [["C", "单次训练算力"], ["N", "参数量"], ["D", "训练 token 数"]] },
        { type: "callout", label: "系数 6", size: 13.5,
          text: "来自前向与反向传播中每个参数每个 token 的乘加次数计数。三个量绑定后，给定其中两个即可推出第三个。" },
        { type: "stats", items: [
          { value: "FLOP", label: "单位明确" },
          { value: "20 年", label: "公开历史序列" },
          { value: "2 层", label: "到能力的映射" },
        ]},
      ]},
    ]},
  ],
  notes: "这一页定基调：不是预测，是换一套能算的单位。",
});

d.page({
  title: "算力曲线在 2010 年折过一次，倍增期由 20 个月缩到 6 个月",
  blocks: [
    { type: "figure", path: "assets/fig_trend.png", maxH: 3.5, credit: "",
      caption: "按已发表的倍增周期与 2030 年结论构造的算力轨迹（非逐模型实测点）" },
    { type: "bullets", size: 13.5, gap: 0.2, items: [
      { lead: "对数坐标上斜率抬了 3.3 倍：", text: "这一加速不是硬件单方面的贡献，而是硬件、资本投入与工程并行度共同作用，因此没有像摩尔定律那样明确的物理下限可依。" },
    ]},
  ],
  source: "Sevilla 等 (2022) arXiv:2202.05924；Epoch AI (2024)",
  notes: "折点的位置是这张图唯一要读的信息。历史段是反推轨迹，不要说成实测点。",
});

// ============ 02 方法 ============
d.section("方法", "锚点不能自己选", [
  ["等比例配比", "算力预算固定时，参数量与 token 数应同步放大"],
  ["指数外推", "对数坐标下是直线，折点即倍增期变化处"],
  ["锚点取自已发表结论", "自选起点会把结论悄悄写进假设里"],
]);

d.page({
  title: "三个关系式，把标度律、外推与锚点串成一条可复核的链",
  blocks: [
    { type: "cols", ratio: [1.25, 1], cols: [
      { blocks: [
        { type: "formula", path: "assets/eq/chin.png", height: 0.72, tag: "(2)",
          where: [["N_opt", "计算最优参数量"], ["D_opt", "计算最优 token 数"]] },
        { type: "formula", path: "assets/eq/grow.png", height: 0.72, tag: "(3)",
          where: [["g", "年增倍数"], ["t₀", "基准年"]] },
        { type: "formula", path: "assets/eq/anchor.png", height: 0.68, tag: "(4)",
          where: [["C₂₀₂₄", "由两个已发表锚点反推的基准"]] },
      ]},
      { blocks: [
        { type: "bullets", size: 14, gap: 0.22, items: [
          { lead: "式 (2) 的来源：", text: "训练四百余个模型后得到的结论——算力预算固定时，参数量与 token 数应等比例放大。" },
          { lead: "式 (3) 的形态：", text: "对数坐标下是直线；轨迹呈折线，只因为倍增期在某些年份发生了变化。" },
          { lead: "式 (4) 是关键：", text: "本文不自选历史起点，两个锚点都取自同一份公开报告，基准年由它们反推得到。" },
        ]},
      ]},
    ]},
  ],
  notes: "评审最可能质疑的是锚点怎么定的。答案就在式 (4)：不是我选的。",
});

d.page({
  title: "自选起点会把结论写进假设：第一版外推低了六个数量级",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [
        { type: "steps", size: 14, items: [
          { title: "错误做法", text: "自己定一个 2000 年的起点，按倍增期往后推。" },
          { title: "后果", text: "推到 2024 年只有 10¹⁹ 量级，比公开可查的前沿低约六个数量级。" },
          { title: "改法", text: "改用年增 4× 与 2030 年 2×10²⁹ 两个已发表的量反推基准年。" },
        ]},
      ]},
      { blocks: [
        { type: "stats", items: [
          { value: "4.9×10²⁵", label: "反推的 2024 年基准", note: "FLOP" },
          { value: "10²⁵", label: "公开报告的独立陈述", note: "逾 30 个模型达此量级" },
        ]},
        { type: "callout", label: "一致性校验", size: 13.5,
          text: "反推值与该报告另一处独立陈述在数量级上相容。两个来源互不依赖，因此这条校验是有效的。" },
        { type: "bullets", size: 13, gap: 0.18, items: [
          { lead: "一般性教训：", text: "外推里最容易出错的不是增速，是起点。起点一旦自选，结论就被悄悄写进了假设，而且错得毫无痕迹。" },
        ]},
      ]},
    ]},
  ],
  source: "Epoch AI (2024)",
  notes: "这一页讲的是方法纪律，不是结果。它决定了后面所有数字可不可信。",
});

// ============ 03 结果 ============
d.section("结果", "先撞哪一堵墙", [
  ["四道天花板差三个数量级", "“会不会撞墙”不是有内容的问题"],
  ["电力最先咬合", "其次是芯片产能"],
  ["数据墙其实更早", "把两篇文献联立才看得见"],
]);

d.page({
  title: "四类约束的上限相差三个数量级，问题该换成“先撞哪一堵”",
  blocks: [
    { type: "figure", path: "assets/fig_ceilings.png", maxH: 3.4, credit: "",
      caption: "四类约束单独作用时 2030 年所允许的训练算力上限" },
    { type: "bullets", size: 13.5, gap: 0.2, items: [
      { lead: "跨度极不对称：", text: "电力（单一园区）上限区间 1×10²⁸—3×10²⁹，延迟墙则在 3×10³⁰—1×10³²，中位相差约两个半数量级。在这个尺度差面前，把“会遇到物理瓶颈”当作单一命题讨论是没有内容的。" },
    ]},
  ],
  source: "Epoch AI (2024)",
  notes: "这一页的作用是把问题重新提对：不是会不会，是先撞哪一堵、在什么水平上撞。",
});

d.page({
  title: "四道天花板的量化口径与对应上限",
  blocks: [
    { type: "table", header: ["约束", "资源口径", "允许的训练算力 / FLOP"], rows: [
      ["电力·单一园区", "1—5 GW", "1×10²⁸ — 3×10²⁹"],
      ["电力·跨地域分布式", "2—45 GW", "2×10²⁸ — 2×10³⁰"],
      ["芯片产能", "2 000 万 — 4 亿张 H100 等效", "1×10²⁹ — 5×10³⁰"],
      ["数据存量", "4×10¹⁴ — 2×10¹⁶ 有效 token", "6×10²⁸ — 2×10³²"],
      ["延迟墙", "现有硬件", "3×10³⁰ — 1×10³²"],
      ["综合结论", "—", "2×10²⁹"],
    ]},
    { type: "bullets", size: 13.5, gap: 0.2, items: [
      { lead: "读法：", text: "综合结论落在电力（单一园区）区间的上四分之一处，略高于芯片产能区间的下沿——这正对应“电力最先咬合、芯片产能其次”的判断。" },
    ]},
  ],
  source: "Epoch AI (2024)",
  notes: "表是给要逐项核对的人看的，讲的时候只念最后一行和读法。",
});

d.page({
  title: "把等比例配比与文本存量联立，数据墙在 2.7×10²⁸ 就到了",
  blocks: [
    { type: "cols", ratio: [1.2, 1], cols: [
      { blocks: [{ type: "figure", path: "assets/fig_scaling.png", maxH: 3.3, credit: "",
        caption: "计算最优配比下 N 与 D 随算力的走向，及其与公开文本存量的交点" }] },
      { blocks: [
        { type: "formula", path: "assets/eq/data.png", height: 0.7, tag: "(5)" },
        { type: "bullets", size: 13.5, gap: 0.2, items: [
          { lead: "解出的交点：", text: "令 D 等于约 3×10¹⁴ token 的公开人类文本存量，由式 (2) 反解得 C ≈ 2.7×10²⁸ FLOP。" },
          { lead: "它比想象的早：", text: "该值仅为综合结论 2×10²⁹ 的 0.14 倍；按 4×/年折算，比电力墙提前约 1.4 年。" },
        ]},
      ]},
    ]},
  ],
  source: "Hoffmann 等 (2022) arXiv:2203.15556；Villalobos 等 (2024) arXiv:2211.04325",
  notes: "这是全篇唯一一个需要把两份文献放在一起才看得见的结果，讲慢一点。",
});

d.page({
  title: "与上一页的“数据不是紧约束”并不矛盾，差别全在口径",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [
        { type: "cards", size: 13.5, items: [
          { title: "多模态有效 token 口径", text: "4×10¹⁴ — 2×10¹⁶，把图像、音频、视频与质量加权后的重复利用都计入。结论：数据不是紧约束。" },
          { title: "纯文本存量口径", text: "约 3×10¹⁴ token。结论：在 2.7×10²⁸ FLOP 处即告失效。" },
        ]},
      ]},
      { blocks: [
        { type: "stats", items: [
          { value: "0.14×", label: "数据墙 / 综合结论" },
          { value: "1.4 年", label: "比电力墙提前" },
        ]},
        { type: "callout", label: "精确表述", size: 13.5,
          text: "纯文本路线在 2.7×10²⁸ FLOP 附近失效。继续放大必须依赖多模态语料、合成数据或数据效率改进——这三条从可选项变成必需项的时点，由式 (5) 给出。" },
        { type: "bullets", size: 13, gap: 0.18, items: [
          { lead: "该问哪个问题：", text: "不是“数据够不够用”，而是“按哪个口径算、这个口径对应的技术路线是否成立”。口径一换，结论就反向。" },
        ]},
      ]},
    ]},
  ],
  notes: "有人会拿上一页反驳，这一页就是替他把话说完，再指出口径差别。",
});

d.page({
  title: "六次方让结果对增速极度敏感：4.0 与 3.0 差了近五倍",
  blocks: [
    { type: "cols", ratio: [1.2, 1], cols: [
      { blocks: [{ type: "figure", path: "assets/fig_sensitivity.png", maxH: 3.2, credit: "",
        caption: "2030 年可达算力对持续年增倍数的敏感性" }] },
      { blocks: [
        { type: "bullets", size: 14, gap: 0.22, items: [
          { lead: "g = 3.0：", text: "2030 年只有 3.6×10²⁸，不足综合结论的五分之一。" },
          { lead: "g = 4.0：", text: "恰为 2×10²⁹，即公开报告的判断值。" },
          { lead: "g = 4.28 / 5.14：", text: "分别触及电力（单一园区）上限与芯片产能中位。" },
        ]},
        { type: "callout", label: "推论", size: 13.5,
          text: "对 2030 年状态的任何断言，实质上都是对“年增速能否维持六年”的断言。" },
        { type: "bullets", size: 13, gap: 0.18, items: [
          { lead: "为什么这么敏感：", text: "六年复利意味着六次方——g 变动四分之一，2030 年的结果就变动一个数量级。历史上该增速已维持十余年，但维持它所依赖的资本与电力扩张已进入新的量级。" },
        ]},
      ]},
    ]},
  ],
  notes: "与其争论 2030 年的绝对水平，不如争论 g 能否维持——后者是可讨论的。",
});

d.page({
  title: "约束的物理载体：电力接入以电网规划计，产能扩张以年计",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "figure", path: "assets/data_center_server_room_2.jpg", maxH: 2.9,
        caption: "数据中心机房：供电与散热能力是最先咬合的约束" }] },
      { blocks: [{ type: "figure", path: "assets/semiconductor_cleanroom_1.png", maxH: 2.9,
        caption: "晶圆厂洁净室：产能无法在需求出现后一两年内响应" }] },
    ]},
    { type: "bullets", size: 13.5, gap: 0.2, items: [
      { lead: "为什么电力最先咬合：", text: "1—5 GW 的园区级功率相当于一座中型核电机组的输出，其接入周期由电网规划决定，而不由芯片供应决定。" },
    ]},
  ],
  notes: "把抽象的约束落到看得见的东西上，观众才会记住排序的理由。",
});

// ============ 04 结论与边界 ============
d.section("结论与边界", "条件命题，不是预测", [
  ["三条结论", "轨迹、约束排序、数据墙位置"],
  ["三处不确定性", "锚点、配比假设、口径"],
  ["最重要的限定", "算力不等于能力"],
]);

d.page({
  title: "结论：三条都是条件命题，条件是增速能否维持六年",
  blocks: [
    { type: "bullets", size: 15, gap: 0.28, items: [
      { lead: "1. 轨迹：", text: "以已发表的两个锚点反推，2024 年基准约 4.9×10²⁵ FLOP；维持年增 4 倍六年后达到 2×10²⁹ FLOP。每一段都可由公开数值复核，不含自选参数。" },
      { lead: "2. 约束排序：", text: "四类约束的上限相差三个数量级以上，最先咬合的是电力，其次是芯片产能。因此该问的是“先遇到哪一个、在什么算力水平上遇到”。" },
      { lead: "3. 数据墙：", text: "纯文本路线在 2.7×10²⁸ FLOP 处失效，比电力约束提前约 1.4 年。多模态语料、合成数据与数据效率改进因此是前置条件，不是加分项。" },
    ]},
    { type: "callout", label: "边界", size: 13.5,
      text: "以上全部取决于年增速能否维持六年，而这一条本报告无法回答。外推的价值不在于给出答案，在于把答案所依赖的假设摆到明处。" },
  ],
  source: "全部外部数值取自四份公开文献，已逐条核对",
  notes: "Q&A 导航：方法问题回 P7/P8，约束问题回 P10/P11，数据墙回 P12/P13。",
});

d.page({
  title: "必须写明的局限：算力与能力之间隔着两层映射",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [
        { type: "steps", size: 13.5, items: [
          { title: "第一层：算力 → 损失", text: "有稳定的幂律形式，但幂指数意味着收益递减——算力涨一个数量级，损失的改善远小于一个数量级。" },
          { title: "第二层：损失 → 任务表现", text: "更不稳定。同一损失水平下不同任务差异很大，推理时计算的引入进一步削弱了对应关系。" },
        ]},
      ]},
      { blocks: [
        { type: "bullets", size: 13.5, gap: 0.22, items: [
          { lead: "因此结论只能说规模：", text: "2×10²⁹ FLOP 支撑的陈述是“规模上的增长空间”，而不是“能力上的必然提升”。" },
          { lead: "原报告也是这么表述的：", text: "它把结论说成“规模差距相当于 GPT-2 到 GPT-4 之间的差距”——这是关于规模的类比，不是关于能力的承诺。" },
        ]},
        { type: "callout", label: "三处不确定性", size: 13,
          text: "锚点精度完全继承自两个已发表量；式 (2) 假定严格等比例配比，实际偏离会让数据墙更早到来；纯文本与多模态两种口径给出方向相反的结论。" },
        { type: "bullets", size: 13, gap: 0.18, items: [
          { lead: "听报告时的判据：", text: "凡是把 FLOP 数字直接说成能力水平的，中间那两层映射一定被跳过了——可以据此判断一个预测是否值得采信。" },
        ]},
      ]},
    ]},
  ],
  notes: "这一页是主动交底。评审最反感的是把规模讲成能力，先自己说破。",
});

d.refs([
  "Epoch AI. Can AI scaling continue through 2030? 2024. epoch.ai/blog/can-ai-scaling-continue-through-2030.",
  "HOFFMANN J, BORGEAUD S, MENSCH A, et al. Training compute-optimal large language models[C]. NeurIPS, 2022, 35. arXiv:2203.15556.",
  "KAPLAN J, MCCANDLISH S, HENIGHAN T, et al. Scaling laws for neural language models[EB/OL]. 2020. arXiv:2001.08361.",
  "SEVILLA J, HEIM L, HO A, et al. Compute trends across three eras of machine learning[EB/OL]. 2022. arXiv:2202.05924.",
  "VILLALOBOS P, HO A, SEVILLA J, et al. Will we run out of data? Limits of LLM scaling based on human-generated data[C]. ICML, 2024. arXiv:2211.04325.",
]);

d.acknowledge({
  advisor: [["实验室同事", "在锚点选取与口径差异上的讨论"]],
  collab: [["Epoch AI 等四个研究组", "本报告全部外部数值的来源"]],
  group: "本报告不产生新数据，只把已发表的判断放进同一套单位里。",
  facility: ["公开文献与开放数据"],
  notes: "致谢从简：本报告的贡献是重新组织，不是新测量。",
});

d.closing({
  takeaway: "先撞的不是电力墙，是数据墙——前提是纯文本路线不变。",
  contact: "liming@example.edu",
  links: [["图表与脚本", "本报告的全部图由公开数据复算"]],
  notes: "结束页；细节问题退回对应页码。",
});

d.build("ai2030_talk.pptx");
