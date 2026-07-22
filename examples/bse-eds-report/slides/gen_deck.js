// Grant-briefing deck for the BSE-EDS fusion open-fund project.
// Follows academic-pptx skill: action titles, one exhibit per slide,
// communication-first design (navy/blue/white, single font, >=20pt body).
const pptxgen = require("pptxgenjs");

const C = {
  bg: "FFFFFF",
  primary: "1F4E79",
  accent: "2E75B6",
  body: "2D2D2D",
  muted: "777777",
  rule: "CCCCCC",
  highlight: "FFF2CC",
  boxFill: "EBF3FA",
  onDarkSub: "A0BBDD",
  onDarkBody: "CADCFC",
};
const FACE = "Microsoft YaHei";
const M = 0.5;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in

function titleBlock(slide, text, opts = {}) {
  const h = opts.h || 0.95;
  slide.addText(text, {
    x: M, y: 0.22, w: 9.0, h,
    fontSize: opts.size || 24, fontFace: FACE, color: C.primary,
    bold: true, valign: "top", margin: 0,
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: M, y: 0.22 + h + 0.03, w: 9.0, h: 0.02,
    fill: { color: C.rule }, line: { type: "none" },
  });
}

function cite(slide, text, y = 5.18) {
  slide.addText(text, {
    x: M, y, w: 9.0, h: 0.32,
    fontSize: 12.5, fontFace: FACE, color: C.muted, align: "left", margin: 0,
  });
}

// ---------- 1. Title ----------
{
  const s = pres.addSlide();
  s.background = { color: C.primary };
  s.addText("BSE–EDS 多模态融合:突破水泥基材料\n微观相识别的灰度天花板", {
    x: 0.7, y: 1.15, w: 8.6, h: 1.7,
    fontSize: 30, fontFace: FACE, color: "FFFFFF", bold: true,
    align: "left", valign: "top", margin: 0,
  });
  s.addText("水泥基材料微观相识别与水化程度智能表征 · 开放基金项目研究计划汇报", {
    x: 0.7, y: 3.0, w: 8.6, h: 0.4,
    fontSize: 16, fontFace: FACE, color: C.onDarkSub, align: "left", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 3.62, w: 2.0, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" },
  });
  s.addText("非金属材料AI+实验室 — 开放基金项目\n中国建筑材料科学研究总院(CBMA) · 2026 年 7 月", {
    x: 0.7, y: 3.78, w: 8.6, h: 0.75,
    fontSize: 15, fontFace: FACE, color: C.onDarkBody, align: "left", margin: 0,
  });
  s.addNotes("开场:一句话点题——BSE 单模态的天花板是信息问题,不是模型问题;本项目用最少的化学采样把它补上。");
}

// ---------- 2. Motivation ----------
{
  const s = pres.addSlide();
  titleBlock(s, "低碳混合材体系已成常态,掺合料与水化产物灰度重叠,\nBSE 单模态分割触及信息天花板");
  s.addText([
    { text: "混合材是低碳主路线:", options: { bold: true, breakLine: false } },
    { text: "矿渣/粉煤灰/偏高岭土/石灰石大比例替代熟料,混合体系成为工程常态。", options: { breakLine: true } },
    { text: "灰度退化:", options: { bold: true, breakLine: false } },
    { text: "SCM 颗粒及其反应边与水化产物灰度区间重叠,单一强度通道无法区分化学上不同的相。", options: { breakLine: true } },
    { text: "架构调优已无增益:", options: { bold: true, breakLine: false } },
    { text: "FCN / U-Net 等 BSE-only 模型对灰度重叠相继续调参基本无增益——上限在模态,不在模型。", options: { breakLine: true } },
  ], {
    x: M, y: 1.55, w: 9.0, h: 3.2,
    fontSize: 20, fontFace: FACE, color: C.body,
    paraSpaceAfter: 14, valign: "top",
  });
  cite(s, "Scrivener (2004) Cem Concr Compos; Lothenbach et al. (2011) CCR; Juenger & Siddique (2015) CCR");
  s.addNotes("口头引出文献:Scrivener 2004 奠定了 BSE 定量分析;Lothenbach 2011、Juenger 2015 说明混合材已是主流——问题因此变得普遍而尖锐。");
}

// ---------- 3. Research question ----------
{
  const s = pres.addSlide();
  titleBlock(s, "核心科学问题:少量而聪明的化学采样,\n能否补上 BSE 缺失的信息维度?");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 1.0, y: 1.6, w: 8.0, h: 1.75,
    fill: { color: C.boxFill }, line: { color: C.accent, width: 1.5 }, rectRadius: 0.1,
  });
  s.addText("以 ≤5% 视场覆盖的稀疏 EDS 采样,经配准门控的图注意力融合网络注入 BSE 形貌特征——能否将灰度重叠相的像素级分割 IoU 提升 ≥20 个百分点,并支撑水化程度的准确、高效表征?", {
    x: 1.3, y: 1.75, w: 7.4, h: 1.45,
    fontSize: 18, fontFace: FACE, color: C.primary,
    align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "关键构想:", options: { bold: true, breakLine: false } },
    { text: "把 EDS 从被动的验证仪器,改造成由模型主动指挥的化学信息供给——模型自己决定实验下一步看哪里。", options: {} },
  ], {
    x: M, y: 3.7, w: 9.0, h: 0.95,
    fontSize: 20, fontFace: FACE, color: C.body, valign: "top", margin: 0,
  });
  s.addNotes("这一页停留久一点:全部后续内容都服务于这个问题。强调 ≤5% 与 +20 pp 两个数字。");
}

// ---------- 4. Methods: dataset ----------
{
  const s = pres.addSlide();
  titleBlock(s, "4 体系 × 4 掺量 × 6 龄期的配对数据集,\n为训练与验证提供系统覆盖");
  s.addText("实验设计", {
    x: M, y: 1.5, w: 4.2, h: 0.4,
    fontSize: 21, fontFace: FACE, color: C.accent, bold: true, margin: 0,
  });
  s.addText([
    { text: "胶材:", options: { bold: true, breakLine: false } },
    { text: "P.I 42.5 + 矿渣 / 粉煤灰 / 石灰石", options: { breakLine: true } },
    { text: "替代率:", options: { bold: true, breakLine: false } },
    { text: "0 / 20 / 40 / 60 wt%,w/b = 0.4", options: { breakLine: true } },
    { text: "龄期:", options: { bold: true, breakLine: false } },
    { text: "1 / 3 / 7 / 28 / 90 / 180 d", options: { breakLine: true } },
  ], {
    x: M, y: 1.95, w: 4.2, h: 2.5,
    fontSize: 19, fontFace: FACE, color: C.body,
    paraSpaceAfter: 12, valign: "top",
  });
  s.addText("数据与标注", {
    x: 5.3, y: 1.5, w: 4.2, h: 0.4,
    fontSize: 21, fontFace: FACE, color: C.accent, bold: true, margin: 0,
  });
  s.addText([
    { text: "配对采集:", options: { bold: true, breakLine: false } },
    { text: "同视场 BSE + EDS 六元素图(Ca/Si/Al/Fe/Mg/S)", options: { breakLine: true } },
    { text: "数据规模:", options: { bold: true, breakLine: false } },
    { text: "≥3000 组配对图像;≥600 幅像素级相标注", options: { breakLine: true } },
    { text: "标注质量:", options: { bold: true, breakLine: false } },
    { text: "经 QXRD / TGA / EDS 点分析三重交叉核验", options: { breakLine: true } },
  ], {
    x: 5.3, y: 1.95, w: 4.2, h: 2.5,
    fontSize: 19, fontFace: FACE, color: C.body,
    paraSpaceAfter: 12, valign: "top",
  });
  cite(s, "合成示例视场 → 附录 A;定量 BSE 实践遵循 Scrivener (2004)");
  s.addNotes("强调配对与交叉核验:标签质量决定 +20 pp 是否可信,所以 600 幅标注全部经三种独立手段核验。");
}

// ---------- 5. Methods: architecture ----------
{
  const s = pres.addSlide();
  titleBlock(s, "两阶段网络:配准残差 <1 px 才进入融合,\n稀疏化学信息沿超像素图传播补全");
  // 2952x1559, ratio 1.8935
  s.addImage({ path: "assets/bse_eds_architecture.png", x: M, y: 1.5, w: 6.25, h: 3.30 });
  s.addText([
    { text: "两步配准:", options: { bold: true, breakLine: false } },
    { text: "刚性互信息 + 可学习形变场,达标才放行", options: { breakLine: true } },
    { text: "双分支编码:", options: { bold: true, breakLine: false } },
    { text: "CNN 稠密形貌 ∥ GNN 化学梯度约束超像素图", options: { breakLine: true } },
    { text: "融合输出:", options: { bold: true, breakLine: false } },
    { text: "多尺度注意力 → 像素级相分割与相分数", options: { breakLine: true } },
  ], {
    x: 6.95, y: 1.55, w: 2.55, h: 3.2,
    fontSize: 16, fontFace: FACE, color: C.body,
    paraSpaceAfter: 12, valign: "top",
  });
  cite(s, "图:本项目 figflow 工作流生成。方法基础:Maes et al. (1997); Achanta et al. (2012); Ronneberger et al. (2015)");
  s.addNotes("按 ①→④ 走一遍架构图;强调门控设计——配准不达标的视场不进入融合,连接类误差从机制上排除。");
}

// ---------- 6. Expected results: targets figure ----------
{
  const s = pres.addSlide();
  titleBlock(s, "预期以 ≤5% EDS 覆盖将灰度重叠相 IoU 提升 ≥20 pp,\n同等精度下机时减半", { size: 24 });
  // 2066x826, ratio 2.5012 — keep clear of the figure's own bottom-right note
  s.addImage({ path: "assets/fig-002.png", x: 1.05, y: 1.42, w: 7.9, h: 3.16 });
  s.addText([
    { text: "两条曲线的间隔即化学信息的价值:", options: { bold: true, color: C.accent, breakLine: false } },
    { text: "主动选点用 5% 覆盖换 ≥20 pp;BSE-only 基线停在 0.55,与架构无关。", options: {} },
  ], {
    x: M, y: 4.72, w: 9.0, h: 0.38,
    fontSize: 15, fontFace: FACE, color: C.body, margin: 0,
  });
  cite(s, "示意性目标曲线与柱状图(合成数据,非实测)——本项目 paperflow 生成", 5.22);
  s.addNotes("指着 (a) 图上的双箭头讲 +20 pp 目标;(b) 图 48% vs 100% 讲机时。明确声明:这是申报目标,不是已得结果。");
}

// ---------- 7. Targets & validation table ----------
{
  const s = pres.addSlide();
  titleBlock(s, "四项量化指标各自绑定独立验证协议,成果开放交付", { h: 0.55, size: 24 });
  const header = [
    { text: "量化指标", options: { bold: true, color: C.primary, fill: { color: C.boxFill } } },
    { text: "验证协议", options: { bold: true, color: C.primary, fill: { color: C.boxFill } } },
  ];
  const rows = [
    ["灰度重叠相 IoU 提升 ≥20 pp(≤5% EDS 覆盖)", "留出像素级标注测试集;标签经 EDS 点分析核验"],
    ["分割推算水化程度误差 ≤5%", "与 TGA 独立测量对照,覆盖全部配比与龄期"],
    ["同等精度下 EDS 机时节省 ≥50%", "同视场实录 dwell 与 mapping 时间日志"],
    ["数据、权重、报告模块开放交付", "≥3000 配对 + ≥600 标注数据集;CBMA 微调权重;自动报告生成模块"],
  ];
  s.addTable([header, ...rows.map(r => r.map(t => ({ text: t })))], {
    x: M, y: 1.15, w: 9.0, colW: [4.1, 4.9],
    fontSize: 15.5, fontFace: FACE, color: C.body,
    border: { type: "solid", color: C.rule, pt: 0.75 },
    margin: 0.09, valign: "middle", rowH: 0.72,
  });
  cite(s, "全部数值为申报目标;交付物存入 CBMA 无机非金属材料数据节点");
  s.addNotes("逐行念指标,验证协议一句带过;评审最关心的是每个数字都有独立于模型的验收办法。");
}

// ---------- 8. Risks ----------
{
  const s = pres.addSlide();
  titleBlock(s, "主要风险前置处置:配准漂移设亚像素门控,\n跨体系泛化设留一外推检验");
  s.addText([
    { text: "配准漂移与充电畸变:", options: { bold: true, breakLine: false } },
    { text: "刚性 + 形变两步配准,人工地标残差 <1 px 方可进入分割阶段。", options: { breakLine: true } },
    { text: "跨体系泛化:", options: { bold: true, breakLine: false } },
    { text: "留一体系外推(leave-one-system-out)检验微观中间变量是否优于仅配比基线。", options: { breakLine: true } },
    { text: "不确定性质量:", options: { bold: true, breakLine: false } },
    { text: "MC-dropout / 深度集成的高熵聚类直接驱动主动采样,采样收益即其有效性自证。", options: { breakLine: true } },
  ], {
    x: M, y: 1.55, w: 9.0, h: 2.7,
    fontSize: 20, fontFace: FACE, color: C.body,
    paraSpaceAfter: 14, valign: "top",
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: M, y: 4.35, w: 9.0, h: 0.62,
    fill: { color: C.highlight }, line: { color: "E6C800", width: 1 }, rectRadius: 0.06,
  });
  s.addText("说明:全篇数值均为申报目标而非已得结果;示意图均为合成数据。", {
    x: 0.75, y: 4.35, w: 8.5, h: 0.62,
    fontSize: 15, fontFace: FACE, color: "7A5200", valign: "middle", margin: 0,
  });
  s.addNotes("主动回应评审最可能的两个质疑:配准误差会不会污染融合;换一个胶材体系还灵不灵。");
}

// ---------- 9. Conclusions (stays up during Q&A) ----------
{
  const s = pres.addSlide();
  s.background = { color: C.primary };
  s.addText("结论", {
    x: M, y: 0.28, w: 9.0, h: 0.45,
    fontSize: 20, fontFace: FACE, color: C.onDarkSub, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: M, y: 0.78, w: 9.0, h: 0.04,
    fill: { color: C.accent }, line: { type: "none" },
  });
  s.addText([
    { text: "1. 突破口在模态,不在模型:", options: { bold: true, breakLine: false } },
    { text: "补上化学维度,目标以 ≤5% 稀疏 EDS 将灰度重叠相 IoU 提升 ≥20 pp。", options: { breakLine: true } },
    { text: "2. EDS 角色重构:", options: { bold: true, breakLine: false } },
    { text: "从被动验证到模型主动指挥的化学信息供给,同等精度下机时目标 −≥50%。", options: { breakLine: true } },
    { text: "3. 可复用的智能表征能力:", options: { bold: true, breakLine: false } },
    { text: "开放数据集 + CBMA 微调权重 + 自动报告模块,接入 CBMA 数据节点。", options: { breakLine: true } },
  ], {
    x: M, y: 1.05, w: 9.0, h: 3.4,
    fontSize: 21, fontFace: FACE, color: "FFFFFF",
    paraSpaceAfter: 22, valign: "top", margin: 0,
  });
  s.addText("非金属材料AI+实验室 · 中国建筑材料科学研究总院(CBMA) | github.com/qingguang0309/academic-skills", {
    x: M, y: 4.9, w: 9.0, h: 0.4,
    fontSize: 12.5, fontFace: FACE, color: C.onDarkSub, margin: 0,
  });
  s.addNotes("Q&A 期间保持本页。提问导航:数据集细节→第4页;架构→第5页;指标→第7页;合成示例→附录A。");
}

// ---------- 10. References ----------
{
  const s = pres.addSlide();
  titleBlock(s, "参考文献", { h: 0.5, size: 24 });
  const refs = [
    "Scrivener, K.L. (2004). Backscattered electron imaging of cementitious microstructures: understanding and quantification. Cement and Concrete Composites, 26, 935–945.",
    "Lothenbach, B., Scrivener, K., & Hooton, R.D. (2011). Supplementary cementitious materials. Cement and Concrete Research, 41, 1244–1256.",
    "Juenger, M.C.G., & Siddique, R. (2015). Recent advances in understanding the role of supplementary cementitious materials in concrete. Cement and Concrete Research, 78, 71–80.",
    "Maes, F., Collignon, A., Vandermeulen, D., Marchal, G., & Suetens, P. (1997). Multimodality image registration by maximization of mutual information. IEEE Transactions on Medical Imaging, 16, 187–198.",
    "Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional networks for biomedical image segmentation. LNCS, 9351, 234–241.",
    "Achanta, R., Shaji, A., Smith, K., Lucchi, A., Fua, P., & Süsstrunk, S. (2012). SLIC superpixels compared to state-of-the-art superpixel methods. IEEE TPAMI, 34, 2274–2282.",
    "Long, J., Shelhamer, E., & Darrell, T. (2015). Fully convolutional networks for semantic segmentation. CVPR 2015, 3431–3440.",
  ];
  s.addText(
    refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1 } })),
    {
      x: M, y: 1.05, w: 9.0, h: 4.3,
      fontSize: 13, fontFace: FACE, color: C.body,
      paraSpaceAfter: 10, valign: "top", margin: 0,
    }
  );
}

// ---------- 11. Appendix A ----------
{
  const s = pres.addSlide();
  s.addText("附录 A — 合成示例视场", {
    x: M, y: 0.18, w: 9.0, h: 0.35,
    fontSize: 14, fontFace: FACE, color: C.muted, italic: true, margin: 0,
  });
  s.addText("从灰度退化的 BSE 视场到相图:稀疏采样点经超像素图传播补全", {
    x: M, y: 0.58, w: 9.0, h: 0.5,
    fontSize: 22, fontFace: FACE, color: C.primary, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: M, y: 1.14, w: 9.0, h: 0.02, fill: { color: C.rule }, line: { type: "none" },
  });
  // 2066x1771, ratio 1.1666
  s.addImage({ path: "assets/fig-000.png", x: M, y: 1.3, w: 4.35, h: 3.73 });
  s.addText([
    { text: "(a) 合成 BSE:", options: { bold: true, breakLine: false } },
    { text: "偏高岭土与矿渣灰度几乎相同,BSE-only 不可分", options: { breakLine: true } },
    { text: "(b) 稀疏 EDS:", options: { bold: true, breakLine: false } },
    { text: "覆盖 ≤5%,按真值相着色", options: { breakLine: true } },
    { text: "(c) 超像素图:", options: { bold: true, breakLine: false } },
    { text: "含样本的节点实心着色,灰色小节点待图传播补全", options: { breakLine: true } },
    { text: "(d) 真值相图:", options: { bold: true, breakLine: false } },
    { text: "同一视场、同一配色,细白线为相界", options: { breakLine: true } },
  ], {
    x: 5.15, y: 1.4, w: 4.35, h: 3.4,
    fontSize: 16, fontFace: FACE, color: C.body,
    paraSpaceAfter: 12, valign: "top",
  });
  cite(s, "合成示意数据(高斯滤波随机场生成),非实测——本项目 paperflow 生成");
}

pres.writeFile({ fileName: "bse_eds_grant_briefing.pptx" }).then(() => console.log("written"));
