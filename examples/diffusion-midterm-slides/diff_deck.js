// 扩散模型少步采样 —— 博士研究生中期考核(paper-slides / pku 主题)
const { Deck } = require("./slidekit");

const d = new Deck({
  theme: "pku", lang: "zh",
  title: "扩散模型少步采样的误差分解与时间步优化",
  subtitle: "把采样代价从数十次网络求值压到十次以内",
  shortTitle: "少步采样",
  occasion: "博士研究生中期考核",
  presenter: "李 明", advisor: "王 立 教授",
  org: "北京大学 智能学院",
  date: "2026 年 7 月",
});

d.cover({ notes: "开场:扩散模型的质量已经够用,卡在采样代价。少步采样的关键不是换求解器,而是搞清误差从哪来。" });
d.toc();

// ============ 01 问题 ============
d.section("问题", "少步采样卡在哪里");

d.page({
  title: "采样代价与网络求值次数成正比，这是扩散模型落地的主要开销",
  blocks: [
    { type: "bullets", size: 15.5, gap: 0.26, items: [
      { lead: "代价结构：", text: "每步采样调用一次去噪网络，生成一张 1024² 图像的 50 步采样约需 12 GFLOPs×50，推理成本几乎全在这里。" },
      { lead: "现有做法：", text: "高阶 ODE 求解器把 50 步压到 20 步左右；蒸馏类方法能到个位数步，但要重训网络、且难以复用预训练权重。" },
      { lead: "被忽略的自由度：", text: "时间步的选取。多数求解器沿用均匀或简单几何间隔，而误差对步长分布高度敏感。" },
    ]},
    { type: "text", size: 12, color: "797069",
      text: "Song et al. (2021) ICLR;Lu et al. (2022) NeurIPS;Salimans & Ho (2022) ICLR" },
  ],
  notes: "把听众引到\"时间步是免费的自由度\"这个点上——它不需要动网络,是本课题的切入口。",
});

d.page({
  title: "本阶段要回答：少步误差由什么主导，以及步长该怎么分配",
  blocks: [
    { type: "callout", label: "研究问题", size: 14,
      text: "在不改动预训练 score 网络的前提下，把少步采样的重构误差分解为可控与不可控两部分，并据此把时间步选取写成一个可求解的优化问题。" },
    { type: "stats", items: [
      { value: "10 步", label: "目标求值次数", note: "对齐基线 25 步质量" },
      { value: "O(h²)", label: "离散误差阶", note: "二阶求解器实测" },
      { value: "0", label: "网络重训成本", note: "仅离线优化步长表" },
    ]},
  ],
  notes: "三个数字对应三章:目标、理论、方法。强调零重训是与蒸馏类方法的关键区别。",
});

// ============ 02 理论 ============
d.section("理论分析", "从概率流 ODE 到误差分解");

d.page({
  title: "采样等价于沿概率流 ODE 反向积分",
  blocks: [
    { type: "formula", path: "assets/eq/fwd.png", tag: "(1)", height: 0.6,
      where: [["ᾱₜ", "累积噪声调度"], ["x₀", "干净样本"]] },
    { type: "formula", path: "assets/eq/pf.png", tag: "(2)", height: 0.66,
      where: [["f, g", "前向 SDE 的漂移与扩散系数"], ["∇ log pₜ", "由 score 网络近似"]] },
    { type: "text", size: 13.5,
      text: "式 (2) 是确定性的：给定初值与步长表，采样结果唯一。少步采样的全部误差因此只有两个来源——积分离散化，以及 score 网络本身的近似误差。" },
  ],
  notes: "式 (1) 一句带过,重点在式 (2) 的确定性:它把\"采样质量\"变成了\"数值积分精度\"问题。",
});

d.page({
  title: "误差分解：离散项随步长可压，网络项构成不可突破的地板",
  blocks: [
    { type: "formula", path: "assets/eq/err.png", tag: "(3)", height: 0.68,
      where: [["h", "最大步长"], ["p", "求解器阶数"], ["ε", "score 网络的 L² 误差"]] },
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [{ type: "bullets", size: 14, rule: false, items: [
        { lead: "可控项：", text: "C₁hᵖ 随步长以 p 阶衰减，是步长优化能改善的部分。" },
      ]}]},
      { blocks: [{ type: "bullets", size: 14, rule: false, items: [
        { lead: "地板项：", text: "C₂ε 与步长无关；步数增加到一定程度后误差不再下降。" },
      ]}]},
    ]},
  ],
  notes: "这是本阶段的主要理论结果:它解释了为什么一味加步数没用,也说明优化步长的收益上界在哪。",
});

d.page({
  title: "数值实验复现出预测的两段行为",
  blocks: [
    { type: "figure", path: "assets/fig_pareto.png", maxH: 4.0, credit: "",
      caption: "帕累托前沿与误差分解的数值验证(合成示意数据，非实测)" },
    { type: "callout", label: "对照", size: 12.5,
      text: "(b) 中实测曲线在大步长段贴合 h² 斜率、在小步长段收敛到水平线，两段的转折点即式 (3) 两项相等之处——这正是步长预算的合理下界。" },
  ],
  notes: "把 (b) 的转折点讲清:它给出\"再减步长也没用\"的判据,是选 10 步而不是 5 步的依据。",
});

// ============ 03 方法 ============
d.section("方法", "把时间步选取写成优化问题");

d.page({
  title: "以教师轨迹为监督，求解步长分配",
  blocks: [
    { type: "formula", path: "assets/eq/obj.png", tag: "(4)", height: 0.72,
      where: [["Φₕ", "单步求解器算子"], ["Ψ", "高精度教师轨迹"], ["T", "总积分区间"]] },
    { type: "algorithm", title: "算法 1  离线时间步优化", size: 12.5, lines: [
      "输入：预训练 score 网络 sθ、步数预算 N、教师步数 M ≫ N",
      "用 M 步高精度求解器在校准集上生成教师轨迹 Ψ",
      "初始化 {tᵢ} 为几何间隔",
      "for k = 1 … K do",
      "  沿当前 {tᵢ} 前向积分，累计式 (4) 的轨迹偏差",
      "  对 {tᵢ} 做投影梯度下降，投影到 Σhᵢ = T 的单纯形",
      "  if 偏差在连续 3 轮内不再下降 then 退出",
      "输出：最优时间步表 {tᵢ}*（与网络权重解耦，可跨采样器复用）",
    ]},
  ],
  notes: "强调两点:教师轨迹只在校准集上算一次;输出是一张表,不是一个新模型——这是零重训成本的来源。",
});

d.page({
  title: "两条链解耦：离线求一次步长表，在线只跑十步",
  blocks: [
    { type: "figure", path: "assets/dg_pipe.png", maxH: 3.3, credit: "",
      caption: "方法流程(Graphviz 布局引擎绘制)" },
    { type: "callout", label: "工程含义", size: 12.5,
      text: "步长表是一个长度 N 的浮点数组，可直接替换现有采样器的时间步序列；部署侧无需改动网络与权重文件。" },
  ],
  notes: "这页给工程听众:改造成本极低。被问落地就停在这页。",
});

// ============ 04 结果与计划 ============
d.section("阶段结果与后续计划", "验证 · 消融 · 时间表");

d.page({
  title: "10 步采样的 FID 与基线 25 步持平",
  blocks: [
    { type: "table", widths: [0.34, 0.22, 0.22, 0.22],
      header: ["方法", "NFE", "FID ↓", "相对基线加速"],
      rows: [
        ["DDIM（均匀步长）", "25", "2.71", "1.0×"],
        ["DPM-Solver++（2 阶）", "20", "2.44", "1.25×"],
        ["本方法（优化时间步）", "10", "2.42", "2.5×"],
        ["本方法（优化时间步）", "8", "2.58", "3.1×"],
      ]},
    { type: "callout", tone: "warn", label: "说明", size: 12,
      text: "表内与全篇数值为方法演示用的合成示意数据，非真实实验结果；图表由本项目脚本可复现生成。" },
  ],
  notes: "读表时点出 10 步一行:FID 2.42 已经优于基线 25 步的 2.71,这是本阶段最硬的结果。",
});

d.page({
  title: "后续半年：把结论从单一模型推广到跨模型与跨采样器",
  blocks: [
    { type: "cards", cols: 3, items: [
      { title: "跨模型迁移", text: "验证步长表在不同 score 网络间的可迁移性；若不可迁移，给出迁移代价的经验规律" },
      { title: "条件生成", text: "在 classifier-free guidance 下重做误差分解——引导强度会改变有效 Lipschitz 常数" },
      { title: "理论收紧", text: "把式 (3) 的常数 C₁、C₂ 与调度函数的显式关系写出来，给出步长表的闭式近似" },
    ]},
  ],
  notes: "三项计划各对应一篇工作。若被问风险,重点讲条件生成那条——引导强度是最不确定的因素。",
});

d.page({
  title: "结论：少步采样的瓶颈是误差结构，不是求解器阶数",
  blocks: [
    { type: "bullets", gap: 0.3, items: [
      { lead: "1. 误差分解：", text: "少步重构误差可拆为随步长 p 阶衰减的离散项与由 score 精度决定的地板项，数值实验与式 (3) 一致。" },
      { lead: "2. 方法：", text: "把时间步选取写成轨迹匹配问题，离线求解一次即可，网络权重不动。" },
      { lead: "3. 效果：", text: "10 次网络求值达到均匀步长 25 步的 FID 水平，部署侧改动仅为替换一个浮点数组。" },
    ]},
    { type: "callout", label: "Q&A 导航", size: 12,
      text: "误差分解 → P8;优化目标与算法 → P10;流程与部署 → P11;主表 → P12" },
  ],
  notes: "Q&A 停留本页。最可能被问:为什么不直接蒸馏(答:蒸馏要重训且绑定网络,本方法零重训、可复用)。",
});

d.refs([
  "Song, J., Meng, C., & Ermon, S. (2021). Denoising diffusion implicit models. ICLR.",
  "Song, Y., Sohl-Dickstein, J., Kingma, D.P., et al. (2021). Score-based generative modeling through stochastic differential equations. ICLR.",
  "Lu, C., Zhou, Y., Bao, F., et al. (2022). DPM-Solver: A fast ODE solver for diffusion probabilistic model sampling in around 10 steps. NeurIPS.",
  "Karras, T., Aittala, M., Aila, T., & Laine, S. (2022). Elucidating the design space of diffusion-based generative models. NeurIPS.",
  "Salimans, T., & Ho, J. (2022). Progressive distillation for fast sampling of diffusion models. ICLR.",
  "Zhang, Q., & Chen, Y. (2023). Fast sampling of diffusion models with exponential integrator. ICLR.",
]);

d.closing({ contact: "liming@pku.edu.cn", notes: "结束页;细节问题退回结论页或对应页码。" });

d.build("diffusion_midterm.pptx");
