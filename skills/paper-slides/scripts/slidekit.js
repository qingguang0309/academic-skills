// ============================================================
// slidekit.js — 学术幻灯组件库(pptxgenjs 之上)
//
// 设计目标(对应 paper-slides skill 三条铁律):
//   1. 模型只组装组件,不手拍坐标——版式由布局引擎计算
//   2. 中西文混排自动分 run:汉字走中文字体,拉丁/数字走西文字体
//   3. 中文学术惯例内建:封面信息区/目录/章节过渡/三线表/页码页脚
//
// 用法:
//   const { Deck, THEMES } = require('./slidekit');
//   const d = new Deck({ theme:'azure', lang:'zh', title:'…', shortTitle:'…',
//                        occasion:'开放基金汇报', presenter:'…', org:'…', date:'…' });
//   d.cover(); d.toc();
//   d.section('研究背景');
//   d.page({ title:'完整结论句作页标题', blocks:[ {type:'bullets', items:[…]} ] });
//   d.refs([…]); d.closing(); d.build('out.pptx');
// ============================================================
"use strict";
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

// ---------- 画布与网格(16:9 宽屏,单位英寸) ----------
const W = 13.33, H = 7.5;
const M = 0.72;               // 左右边距
const CW = W - 2 * M;         // 内容区宽
const FOOTER_Y = 7.06;        // 页脚基线
const CONTENT_BOTTOM = 6.88;  // 内容区底界
const GAP = 0.26;             // 块间默认间距
const FILL_MIN = 0.62;       // 内容页填充率下限:低于此值发"页面太空"警告
const SOURCE_BASE = 6.98;    // 页内来源行底沿(固定;多行向上生长)
const SOURCE_LH = 0.28;      // 来源行行高
const SOURCE_GAP = 0.16;     // 来源行与正文的净空

// ---------- 字阶(pt,13.33in 画布) ----------
const T = {
  coverTitle: 36, coverSub: 15, coverMeta: 13.5, kicker: 12,
  pageTitle: 25, pageSub: 14,
  sectionNum: 96, sectionTitle: 30, sectionNote: 14.5,
  body: 17, small: 13, caption: 11.5, footer: 9.5,
  statValue: 36, statLabel: 13.5, statNote: 11,
  cardTitle: 14.5, cardBody: 12.5, tableBody: 13, ref: 12,
};

// ---------- 主题 ----------
const THEMES = {
  azure: { // 藏青·金 —— 稳重通用
    primary: "1F3A5F", accent: "2F6FAE", warm: "C9A227",
    ink: "23272E", muted: "6E7681", faint: "9AA1AB",
    line: "D9DEE6", wash: "F3F6FA", washBorder: "E1E8F0", tint: "E7EEF6",
    onDark: "FFFFFF", onDarkSub: "AFC4DD",
  },
  pine: { // 墨绿·赭 —— 材料/能源方向
    primary: "1C4B3F", accent: "2E7D6B", warm: "C08A3E",
    ink: "242826", muted: "6F7873", faint: "9BA49F",
    line: "D8E2DD", wash: "F2F7F5", washBorder: "DFEAE5", tint: "E4EFEA",
    onDark: "FFFFFF", onDarkSub: "B5CEC5",
  },
  plum: { // 绛紫·杏 —— 生医/化学方向
    primary: "4B2D50", accent: "7B4E80", warm: "C39A3B",
    ink: "26232A", muted: "757079", faint: "A19CA5",
    line: "E0D8E2", wash: "F6F3F7", washBorder: "E9E1EB", tint: "EFE7F0",
    onDark: "FFFFFF", onDarkSub: "CDB9CF",
  },
  pku: { // 北大红·燕园金 —— 北京大学官方模版配色(北大红 9A0001 / 燕园金 CEAB6E)
    primary: "9A0001", accent: "BE2A2E", warm: "CEAB6E",
    ink: "2A2422", muted: "797069", faint: "A79E97",
    line: "E7DAD8", wash: "FBF5F4", washBorder: "F0E1DF", tint: "F4E4E3",
    onDark: "FFFFFF", onDarkSub: "E6BEB4",
  },
};

// ---------- 背景层:直接取自真实汇报的素材 ----------
// 这三张图是从两份真实的北大汇报里导出来的原件(ppt/media),不是仿制:
//   pku-landmarks 大殿+华表+红楼+博雅塔+未名湖印章的线描,透明底、自上而下渐隐
//   pku-honeycomb 蜂窝网格 + 博雅塔剪影,极淡(主色约 6% 压白)
//   pku-campus    未名湖畔的近白灰度照(最暗仅 223/255),用作首尾页肌理
// 都是机构专属素材,因此只在 pku 主题下启用;其它主题的首尾页保持纯白。
// 不用渐变:CSS 式的渐变背景在投影上一眼假,真实汇报里也没有——它们用的是实素材。
const DECOR = {
  landmarks: "pku-landmarks.png",
  honeycomb: "pku-honeycomb.png",
  campus: "pku-campus.png",
};

// 图表系列色板:主色→强调色→暖色→中性,保证 4 系列内可区分且与页面同调。
// 超过 4 系列说明该换图型(见 references/charts.md),不再往后编色。
function seriesColors(th) {
  return [th.primary, th.accent, th.warm, th.muted, th.faint];
}

// ---------- 语言包 ----------
const LANG = {
  zh: { toc: "目 录", refs: "参考文献", fig: "图", tab: "表",
        presenter: "汇报人", advisor: "指导教师", part: "PART",
        closingMain: "恳请各位专家批评指正", appendix: "附录",
        ack: "致 谢", ackPeople: "指导与合作", ackSupport: "项目与平台支持", org: "单位" },
  en: { toc: "Contents", refs: "References", fig: "Fig.", tab: "Table",
        presenter: "Presenter", advisor: "Advisor", part: "PART",
        closingMain: "Thank You", appendix: "Appendix",
        ack: "Acknowledgements", ackPeople: "Supervision & Collaboration",
        ackSupport: "Funding & Facilities", org: "Affiliation" },
};

// 场合档位:决定封面变体与结束页主文字。答辩要"恳请指正",组会/文献汇报
// 用同一句就假了——那是评审场合的话术。
const KINDS = {
  defense:     { cover: "split", closing: { zh: "恳请各位专家批评指正", en: "Questions & Comments" } },
  grant:       { cover: "split", closing: { zh: "恳请各位专家批评指正", en: "Questions & Comments" } },
  groupmeeting:{ cover: "plate", closing: { zh: "讨论与提问", en: "Discussion" } },
  paperreading:{ cover: "plate", closing: { zh: "讨论与提问", en: "Discussion" } },
};

// ---------- 中西文分 run ----------
// 汉字/全角标点/中文破折省略号 → 中文字体;其余(拉丁、数字、半角标点) → 西文字体
const CJK_RE = /[⺀-鿿豈-﫿　-〿＀-￯—‘’“”…·]/;
function segs(text) {
  const out = [];
  for (const ch of String(text)) {
    const cjk = CJK_RE.test(ch);
    if (out.length && out[out.length - 1].cjk === cjk) out[out.length - 1].t += ch;
    else out.push({ t: ch, cjk });
  }
  return out;
}

// ---------- 文本宽度估算(用于换行/溢出防护) ----------
// 宽度系数取偏保守值:PowerPoint 与 LibreOffice 替身字体渲染略宽于理论 em,
// 宁可估宽一行提前换行/降字,不可估窄导致相邻块重叠
function chW(ch) {
  if (CJK_RE.test(ch)) return 1.06;
  if (/[A-Z@#%]/.test(ch)) return 0.7;
  if (/[a-z0-9]/.test(ch)) return 0.56;
  if (/[ ]/.test(ch)) return 0.3;
  return 0.44; // 半角标点等
}
function estW(text, size) {
  let em = 0;
  for (const ch of String(text)) em += chW(ch);
  return (em * size) / 72;
}
// 贪心换行:CJK 逐字可断,拉丁按词断
function wrapCount(text, size, w) {
  let lines = 1;
  for (const hard of String(text).split("\n")) {
    if (hard !== String(text).split("\n")[0]) lines++;
    const tokens = [];
    let latin = "";
    for (const ch of hard) {
      if (CJK_RE.test(ch)) {
        if (latin) { tokens.push(latin); latin = ""; }
        tokens.push(ch);
      } else if (ch === " ") { if (latin) { tokens.push(latin + " "); latin = ""; } }
      else latin += ch;
    }
    if (latin) tokens.push(latin);
    let cur = 0;
    for (const tk of tokens) {
      const tw = estW(tk, size);
      if (cur + tw > w && cur > 0) { lines++; cur = tw; } else cur += tw;
    }
  }
  return lines;
}
function textH(text, size, w, lineMult = 1.36) {
  return (wrapCount(text, size, w) * size * lineMult) / 72;
}

class Deck {
  constructor(opts = {}) {
    this.theme = THEMES[opts.theme || "azure"];
    if (!this.theme) throw new Error(`未知主题: ${opts.theme}(可选 ${Object.keys(THEMES).join("/")})`);
    this.lang = opts.lang || "zh";
    this.L = LANG[this.lang];
    this.fonts = {
      hans: opts.hansFont || (this.lang === "zh" ? "Microsoft YaHei" : "Arial"),
      latin: opts.latinFont || "Arial",
    };
    this.kind = KINDS[opts.kind] ? opts.kind : "defense";
    this.meta = opts;         // title/shortTitle/occasion/presenter/advisor/org/date
    this.ops = [];            // 延迟渲染:build 时统一执行(目录/页码需要全局信息)
    this.sections = [];       // {title, note, opIndex}
    this.figN = 0; this.tabN = 0; this.realPhotos = 0; this.hasChart = false;
    this.warns = [];
    // 首尾页的自带底图。应当是**已烘焙好淡化**的 PNG(见 examples 里的 make_bg.py):
    // 淡化烘进图里而不靠渲染器的透明度,PowerPoint / LibreOffice / 导出 PDF 才一致。
    this.bgArt = (() => {
      try { return opts.bgArt && fs.existsSync(opts.bgArt) ? opts.bgArt : null; }
      catch (e) { return null; }
    })();
    this.brand = this._resolveBrand(opts);
  }

  // 品牌资源(校徽/logo):pku 主题默认引用随 slidekit 打包的 assets/,
  // 也可用 opts.logo / opts.seal 显式指定(传绝对路径或相对生成脚本的路径),
  // 传 false 关闭;文件不存在则静默跳过(不影响其它主题)。
  //   logo  = 印章+校名横排锁定版,置于正文/章节/目录/参考文献页右上角
  //   seal  = 圆形印章,用于 band 式封面/结束页居中
  //   style = 'band'(白—红—白三段带 + 居中印章,北大官方封面样式)/ 'plain'(纯色封面)
  _resolveBrand(opts) {
    const dir = path.join(__dirname, "assets");
    const isPku = (opts.theme === "pku");
    const has = p => { try { return p && fs.existsSync(p) ? p : null; } catch (e) { return null; } };
    const pick = (v, def) => v === false ? null : has(v || def);
    const logo = pick(opts.logo, isPku ? path.join(dir, "pku-logo.png") : null);
    const seal = pick(opts.seal, isPku ? path.join(dir, "pku-seal.png") : null);
    const kind = KINDS[opts.kind] || KINDS.defense;
    const style = opts.coverStyle || kind.cover;
    // corner 管的是正文/章节/目录各页的右上角标,与封面变体无关。
    // plate 封面自带放大版横排 logo,靠 _coverPlate 不调 _brandCorner 来避免一页两枚校徽。
    return { logo, seal, style, corner: opts.cornerLogo !== false && !!logo };
  }

  // 正文/章节/目录/参考文献页右上角的横排 logo(印章+校名),等高缩放不变形
  _brandCorner(ctx) {
    if (!this.brand.corner || !this.brand.logo) return;
    const d = imgSize(this.brand.logo);
    const h = 0.4, w = h * d.w / d.h;
    ctx.slide.addImage({ path: this.brand.logo, x: W - M - w, y: 0.34, w, h });
  }

  // 文本 → pptxgenjs run 数组(自动分配中西文字体)
  runs(text, o = {}) {
    const arr = [];
    const push = (t, extra) => {
      for (const sg of segs(t)) {
        arr.push({ text: sg.t, options: Object.assign({
          fontFace: sg.cjk ? this.fonts.hans : this.fonts.latin,
          breakLine: false,
        }, o, extra) });
      }
    };
    if (o.lead) { push(o.lead, { bold: true }); if (o.leadGap !== false) push("  ", {}); }
    const body = String(text);
    const parts = body.split("\n");
    parts.forEach((p, i) => {
      push(p, {});
      if (i < parts.length - 1 && arr.length) arr[arr.length - 1].options.breakLine = true;
    });
    if (arr.length) arr[arr.length - 1].options.breakLine = false;
    // lead 不参与换行选项修改
    return arr.map(r => { const { lead, leadGap, ...rest } = r.options; return { text: r.text, options: rest }; });
  }

  // ---------- 页面注册 API ----------
  cover(extra = {}) { this.ops.push({ k: "cover", a: extra }); }
  toc() { this.ops.push({ k: "toc" }); }
  // points: [[小标题, 说明], …] 最多 3 条,渲染在章节页下半区——
  // 章节页不给要点预览就会留大片空白,这是"页面很空"的主要来源之一
  section(title, note, points) {
    this.sections.push({ title, note });
    this.ops.push({ k: "section", a: { title, note, points, idx: this.sections.length } });
  }
  page(a) { this.ops.push({ k: "page", a }); }
  refs(list, opts = {}) { this.ops.push({ k: "refs", a: { list, ...opts } }); }
  // advisor/collab: [[姓名, 贡献说明], …];funding: [[基金名, 编号], …];facility: [平台名, …]
  acknowledge(a = {}) { this.ops.push({ k: "ack", a }); }
  closing(a = {}) { this.ops.push({ k: "closing", a }); }

  // ---------- 构建 ----------
  async build(fileName) {
    const pres = new pptxgen();
    pres.layout = "LAYOUT_WIDE";
    this.pres = pres;

    // 预扫:页码与所属章节
    const total = this.ops.length;
    let curSec = null, tocSlideNo = null;
    this.ops.forEach((op, i) => {
      if (op.k === "section") curSec = op.a.title;
      op._sec = curSec; op._no = i + 1;
      if (op.k === "toc") tocSlideNo = i + 1;
      if (op.k === "section") op.a._pageNo = i + 1;
    });

    for (const op of this.ops) {
      const s = pres.addSlide();
      const ctx = { slide: s, no: op._no, total, sec: op._sec };
      if (op.k === "cover") this._cover(ctx, op.a);
      else if (op.k === "toc") this._toc(ctx);
      else if (op.k === "section") this._section(ctx, op.a);
      else if (op.k === "page") this._page(ctx, op.a);
      else if (op.k === "refs") this._refs(ctx, op.a);
      else if (op.k === "ack") this._ack(ctx, op.a);
      else if (op.k === "closing") this._closing(ctx, op.a);
    }
    // 真实照片不是可选项:实景类页面(研究对象、装置、应用场景)配真图是专业度的
    // 硬门槛。找过确实没有合适的,用 new Deck({ photos: false }) 显式豁免——
    // 让它成为一个决定,而不是一次遗漏。
    if (this.meta.photos !== false && this.realPhotos === 0) this.warns.push(
      `全篇没有真实照片(0 张来自 credits.json 的实景图)——先用 fetchimg.py 按题目取 CC 许可` +
      `照片配到研究对象/装置/应用场景页(见 SKILL.md 第 1.5 步);` +
      `确实没有合适图片时传 photos:false 显式豁免`);
    // pku 主题却找不到品牌素材,说明复制 slidekit.js 时漏了同级的 assets/。
    // SKILL.md 第 2 步早就写了这条,但写着的规则会被跳过——所以做成检查。
    if (this.theme === THEMES.pku) {
      const miss = ["pku-logo.png", ...Object.values(DECOR)]
        .filter(f => !fs.existsSync(path.join(__dirname, "assets", f)));
      if (miss.length) this.warns.push(
        `pku 主题缺少品牌素材 ${miss.join("、")}——复制 slidekit.js 时要连同级的 ` +
        `assets/ 一起复制(校徽与地标/蜂窝/校园照都从那里找)。缺了封面就是一张白纸加字。`);
    }
    // 场合是中文学术封面的必需项:评审得先知道这是答辩还是组会。
    // 旧代码里 subtitle 一存在就把 occasion 顶掉了,静默丢失,这里显式兜住。
    if (!this.meta.occasion) this.warns.push(
      `封面缺少 occasion(场合)——中文学术封面必须写明"硕士学位论文答辩""组会文献汇报"之类,` +
      `否则评审无从判断汇报性质`);
    if ((this.kind === "defense" || this.kind === "grant") && !this.ops.some(o => o.k === "ack")) {
      this.warns.push(`${this.kind} 场合缺少致谢页——答辩/结题的固定动作是致谢导师、合作者与基金,` +
        `用 d.acknowledge({advisor, collab, funding, facility}) 补在 refs 之后`);
    }
    const cl = this.ops.find(o => o.k === "closing");
    if (cl && !cl.a.takeaway) this.warns.push(
      `结束页没有 takeaway——Q&A 全程停在这一页,只写一句客套话等于浪费它;` +
      `传 closing({takeaway: "最想被记住的那句结论"})`);
    await pres.writeFile({ fileName });
    await postProcess(fileName, {
      transition: this.meta.transition ?? "fade",
      cjkFont: this.hasChart ? this.fonts.hans : null,
    });
    this.warns = [...new Set(this.warns)];
    if (this.warns.length) {
      console.warn("slidekit 布局警告(建议处理):");
      this.warns.forEach(w => console.warn("  - " + w));
    }
    console.log(`written: ${fileName} (${total} slides)`);
  }

  // ---------- 通用小件 ----------
  _footer(ctx) {
    const th = this.theme;
    const left = [this.meta.shortTitle, ctx.sec].filter(Boolean).join(" · ");
    ctx.slide.addText(this.runs(left, { fontSize: T.footer, color: th.faint }), {
      x: M, y: FOOTER_Y, w: 7.5, h: 0.3, align: "left", margin: 0, valign: "middle" });
    ctx.slide.addText(this.runs(`${String(ctx.no).padStart(2, "0")} / ${ctx.total}`,
      { fontSize: T.footer, color: th.faint }), {
      x: W - M - 1.2, y: FOOTER_Y, w: 1.2, h: 0.3, align: "right", margin: 0, valign: "middle" });
  }
  _header(ctx, a) { // 返回内容区顶界 y
    const th = this.theme;
    const kicker = a.kicker || ctx.sec || this.meta.occasion || "";
    let y = 0.5;
    if (kicker) {
      ctx.slide.addText(this.runs(kicker, { fontSize: T.kicker, color: th.accent, bold: true, charSpacing: 2.4 }), {
        x: M, y: y - 0.06, w: CW, h: 0.3, margin: 0, valign: "middle" });
      y += 0.34;
    }
    const tSize = a.titleSize || T.pageTitle;
    const lines = wrapCount(a.title, tSize, CW);
    if (lines > 2) this.warns.push(`页 ${ctx.no} 标题预计 ${lines} 行,建议精简`);
    const tH = (Math.min(lines, 3) * tSize * 1.24) / 72;
    ctx.slide.addText(this.runs(a.title, { fontSize: tSize, color: th.primary, bold: true }), {
      x: M, y, w: CW, h: tH + 0.06, margin: 0, valign: "top", lineSpacingMultiple: 1.12 });
    y += tH + 0.12;
    if (a.sub) {
      ctx.slide.addText(this.runs(a.sub, { fontSize: T.pageSub, color: th.muted }), {
        x: M, y, w: CW, h: 0.32, margin: 0, valign: "top" });
      y += 0.4;
    }
    return y + 0.18;
  }

  // ---------- 封面 ----------
  // 标题块到标尺线的净空。CJK 实际行高高于 _measureTitle 用的 1.16 估值,
  // 固定间距在 42pt 下会让标尺线贴住末行字,读起来像下划线而不是独立元素。
  _rulerGap(size) { return 0.24 + (size / 72) * 0.38; }

  // 素材背景。等比缩放,不拉伸——真实汇报里的地标线描被横向拉过 1.455 倍,
  // 塔身明显变胖,那是它们手拍坐标的代价,不必跟着犯。
  // 只在 pku 主题下有素材;其它主题静默跳过,首尾页保持纯白。
  // 内置素材是机构专属的(地标线描、校园照),只在 pku 主题下启用。
  // 但"首尾页要一层极淡底图"是通用需求,所以 campus 槽位允许作者自带:
  // new Deck({ bgArt: "assets/bg.png" })。自带图优先于内置素材,且不看主题。
  _hasDecor(which) {
    if (which === "campus" && this.bgArt) return true;
    return this.theme === THEMES.pku &&
      fs.existsSync(path.join(__dirname, "assets", DECOR[which]));
  }

  _decor(ctx, which, o = {}) {
    if (!this._hasDecor(which)) return;
    const p = (which === "campus" && this.bgArt)
      ? this.bgArt
      : path.join(__dirname, "assets", DECOR[which]);
    const d = imgSize(p);
    let w = o.w, h = o.h;
    if (w && !h) h = w * d.h / d.w;
    else if (h && !w) w = h * d.w / d.h;
    else if (!w && !h) { w = W; h = W * d.h / d.w; }
    const x = o.x != null ? o.x : (o.right != null ? W - o.right - w : 0);
    const y = o.y != null ? o.y : (o.bottom != null ? H - o.bottom - h : 0);
    ctx.slide.addImage({ path: p, x, y, w, h });
  }

  // 短标尺线:封面/结束页/致谢页共用,与目录页那条同族
  _ruler(ctx, x, y, w, color) {
    ctx.slide.addShape(this.pres.shapes.RECTANGLE,
      { x, y, w, h: 0.055, fill: { color }, line: { type: "none" } });
  }

  // 标签—值两级信息区。封面信息不能用空格拼一行居中:
  // 中西文分 run 后空格宽度不可靠,"汇报人"与"指导教师"字数不同,冒号必然参差。
  _infoRows(ctx, o) {
    const th = this.theme, s = ctx.slide;
    let y = o.y;
    for (const [label, value] of o.rows) {
      if (!value) continue;
      s.addText(this.runs(label, { fontSize: 11, color: o.onDark ? th.onDarkSub : th.muted, charSpacing: 1 }),
        { x: o.x, y, w: o.w, h: 0.22, margin: 0, align: o.align || "left", valign: "middle" });
      s.addText(this.runs(value, { fontSize: 14, color: o.onDark ? th.onDark : th.ink }),
        { x: o.x, y: y + 0.22, w: o.w, h: 0.3, margin: 0, align: o.align || "left", valign: "middle" });
      y += 0.62;
    }
    return y - o.y;
  }

  // 标题实测高度。封面过去把标题框写死在固定坐标,三行就压到副题、四行直接穿出;
  // 内容页早有 wrapCount 测量,封面反倒开了后门——这里补上。
  _measureTitle(text, size, w) {
    const lines = wrapCount(text, size, w);
    return { lines, h: (lines * size * 1.16) / 72 };
  }

  _cover(ctx, a) {
    const style = this.brand.style;
    if (style === "band" && this.brand.seal) return this._coverBand(ctx, a);
    if (style === "plate") return this._coverPlate(ctx, a);
    if (style === "solid") return this._coverSolid(ctx, a);
    return this._coverSplit(ctx, a);
  }

  // 变体 split(默认):左竖色块 + 右浅底。气场靠字号断层而非色块面积,
  // 长中文标题在右白区有 7.6in 可用宽度,不像 band 式被挤在带内。
  _coverSplit(ctx, a) {
    const th = this.theme, s = ctx.slide, m = this.meta, R = this.pres.shapes.RECTANGLE;
    const BW = 4.52, PX = 5.02, PW = W - PX - M;
    // 自带底图铺最底层:后面的实色块/色带会盖住它压到的部分,正是参考件的做法
    this._decor(ctx, "campus", { x: 0, y: 0, w: W, h: H });
    // 蜂窝先铺,左边一截会被实色块盖掉——正是 Li-S 那份的做法。
    // split 不放地标线描:右白区被标题、副题、分界线、信息区占满,
    // 真正的空白只有 1in 高,放进去必压字。地标归 plate 变体(它才是 MoS2 的版式)。
    this._decor(ctx, "honeycomb", { x: BW, y: 0, h: 3.9 });
    s.addShape(R, { x: 0, y: 0, w: BW, h: H, fill: { color: th.primary }, line: { type: "none" } });
    const bx = 0.62, bw = BW - bx - 0.6;
    if (m.occasion) s.addText(this.runs(m.occasion, { fontSize: 12, color: th.onDark, bold: true, charSpacing: 3 }),
      { x: bx, y: 2.6, w: bw, h: 0.34, margin: 0, align: "right", valign: "middle" });
    this._infoRows(ctx, {
      x: bx, y: 5.62, w: bw, align: "right", onDark: true,
      rows: [[this.L.presenter, m.presenter], [m.date ? "日期" : "", m.date]],
    });
    this._brandCorner(ctx);

    const tSize = a.titleSize || 42;
    const t = this._measureTitle(m.title, tSize, PW);
    if (t.lines >= 4) this.warns.push(`封面标题 ${t.lines} 行(${tSize}pt)——超过三行会压穿副题区,` +
      `请用 \\n 手动断行、缩短题名,或传 cover({titleSize: 34})`);
    const tTop = 2.30 + (2.10 - Math.min(t.h, 2.10)) / 2;
    s.addText(this.runs(m.title, { fontSize: tSize, color: th.primary, bold: true }),
      { x: PX, y: tTop, w: PW, h: t.h + 0.1, margin: 0, valign: "top", lineSpacingMultiple: 1.16 });
    let y = tTop + t.h + this._rulerGap(tSize);
    this._ruler(ctx, PX, y, 1.5, th.primary);
    y += 0.33;
    if (m.subtitle) {
      s.addText(this.runs(m.subtitle, { fontSize: 16, color: th.muted }),
        { x: PX, y, w: PW, h: 0.4, margin: 0, valign: "middle" });
    }
    s.addShape(R, { x: BW, y: 5.62, w: W - M - BW, h: 0.012, fill: { color: th.line }, line: { type: "none" } });
    // 有导师:导师进标签—值信息区,单位以小字附在下方(两级层次)。
    // 无导师:单位自己占信息区,不再另画——旧写法两条分支都会画一次 org,
    // 相差 0.04in,渲染出来是重影。
    if (m.advisor) {
      this._infoRows(ctx, { x: PX, y: 5.86, w: PW, rows: [[this.L.advisor, m.advisor]] });
      if (m.org) s.addText(this.runs(m.org, { fontSize: 12.5, color: th.muted }),
        { x: PX, y: 6.52, w: PW, h: 0.3, margin: 0, valign: "middle" });
    } else if (m.org) {
      this._infoRows(ctx, { x: PX, y: 5.86, w: PW, rows: [[this.L.org, m.org]] });
    }
    if (a.notes) s.addNotes(a.notes);
  }

  // 变体 plate:浅底 + 底部厚色带,适合组会/文献汇报(可挂刊名 logo 与概念图)
  _coverPlate(ctx, a) {
    const th = this.theme, s = ctx.slide, m = this.meta, R = this.pres.shapes.RECTANGLE;
    const bandY = 5.62;
    // 自带底图铺最底层:后面的实色块/色带会盖住它压到的部分,正是参考件的做法
    this._decor(ctx, "campus", { x: 0, y: 0, w: W, h: H });
    if (this.brand.logo) {
      const d = imgSize(this.brand.logo), h = 0.62, w = h * d.w / d.h;
      s.addImage({ path: this.brand.logo, x: M, y: 0.58, w, h });
    }
    if (m.occasion) s.addText(this.runs(m.occasion, { fontSize: 12, color: th.muted, bold: true, charSpacing: 3 }),
      { x: M, y: 1.46, w: CW, h: 0.3, margin: 0, valign: "middle" });
    const tSize = a.titleSize || 32;
    const t = this._measureTitle(m.title, tSize, CW);
    if (t.lines >= 4) this.warns.push(`封面标题 ${t.lines} 行(${tSize}pt),plate 变体最多三行`);
    s.addText(this.runs(m.title, { fontSize: tSize, color: th.primary, bold: true }),
      { x: M, y: 1.92, w: CW, h: t.h + 0.1, margin: 0, valign: "top", lineSpacingMultiple: 1.16 });
    let y = 1.92 + t.h + this._rulerGap(tSize);
    this._ruler(ctx, M, y, 1.5, th.primary);
    y += 0.32;
    if (m.subtitle) s.addText(this.runs(m.subtitle, { fontSize: 16, color: th.muted }),
      { x: M, y, w: CW * 0.62, h: 0.4, margin: 0, valign: "middle" });
    const jl = this.meta.journalLogo;
    if (jl && fs.existsSync(jl)) {
      const d = imgSize(jl), h = 0.85, w = h * d.w / d.h;
      s.addImage({ path: jl, x: M, y: y + 0.62, w, h });
    }
    const art = this.meta.coverArt;
    // plate 的中段是留给刊名 logo / 概念图的。两个都不给,标题与色带之间会空出
    // 近 3in 的白——那正是"看着像模版没填完"的样子。
    // pku 主题例外:地标线描已经占住了中段右半幅,不算空。
    if (!this._hasDecor("landmarks") &&
        !(jl && fs.existsSync(jl)) && !(art && fs.existsSync(art))) this.warns.push(
      `plate 封面缺少 journalLogo 与 coverArt,中段留白约 3in——` +
      `文献汇报挂刊名 logo,其它场合配一张概念图,或改用 coverStyle: "split"`);
    if (art && fs.existsSync(art)) {
      const d = imgSize(art), box = { w: 5.4, h: 3.2 };
      const sc = Math.min(box.w / d.w, box.h / d.h);
      const w = d.w * sc, h = d.h * sc;
      s.addImage({ path: art, x: W - M - w, y: bandY - h + 0.3, w, h });
    }
    s.addShape(R, { x: 0, y: bandY, w: W, h: H - bandY, fill: { color: th.primary }, line: { type: "none" } });
    // 地标压在红带之上:线描自带自上而下的 alpha 渐隐,与红带同色,
    // 下半截会自然沉进红块——这是 MoS2 原件的 z 序,反过来画就成了被切一刀。
    this._decor(ctx, "landmarks", { right: 0.2, y: bandY - 1.87, w: 5.75 });
    if (m.presenter) s.addText(this.runs(m.presenter, { fontSize: 20, color: th.onDark, bold: true }),
      { x: M, y: bandY + 0.42, w: CW * 0.5, h: 0.44, margin: 0, valign: "middle" });
    const sub = [m.date].filter(Boolean).join("");
    if (sub) s.addText(this.runs(sub, { fontSize: 13.5, color: th.onDarkSub }),
      { x: M, y: bandY + 0.94, w: CW * 0.5, h: 0.34, margin: 0, valign: "middle" });
    // 单位跟在日期之后、同样靠左。带内右半幅留给地标线描——
    // 右对齐会被塔身压住,MoS2 原件的带内也只有左侧一列信息。
    if (m.org) s.addText(this.runs(m.org, { fontSize: 13.5, color: th.onDarkSub }),
      { x: M, y: bandY + 1.34, w: CW * 0.55, h: 0.34, margin: 0, valign: "middle" });
    if (a.notes) s.addNotes(a.notes);
  }

  // 变体 band:白—红—白三段带 + 居中印章(北大官方模版样式)。
  // 带高与副题起点按标题实测行数推算,不再写死坐标。
  _coverBand(ctx, a) {
    const th = this.theme, s = ctx.slide, m = this.meta, R = this.pres.shapes.RECTANGLE;
    const sealH = 1.15, sealTop = 0.62, bandTop = sealTop + sealH;
    const tSize = a.titleSize || T.coverTitle;
    const t = this._measureTitle(m.title, tSize, W - 2.4);
    // 自带底图铺最底层:后面的实色块/色带会盖住它压到的部分,正是参考件的做法
    this._decor(ctx, "campus", { x: 0, y: 0, w: W, h: H });
    if (t.lines >= 4) this.warns.push(`封面标题 ${t.lines} 行(${tSize}pt)——band 式红带放不下,` +
      `请缩短题名或改用 coverStyle: "split"`);
    const hasSub = !!(m.subtitle || m.occasion);
    const bandH = Math.max(3.0, t.h + (hasSub ? 1.5 : 0.9) + 0.9);
    this._decor(ctx, "honeycomb", { x: W - 4.6, y: 0, h: 2.4 });
    s.addShape(R, { x: 0, y: bandTop, w: W, h: bandH, fill: { color: th.primary }, line: { type: "none" } });
    if (this.brand.seal) {
      const d = imgSize(this.brand.seal), sw = sealH * d.w / d.h;
      s.addImage({ path: this.brand.seal, x: (W - sw) / 2, y: sealTop, w: sw, h: sealH });
    }
    let y = bandTop + 0.52;
    // 场合与副题分槽位。旧写法 sub: subtitle || occasion 一旦传了副题,
    // "硕士学位论文答辩"就整张封面消失——中文封面里场合是必需项,不是备选。
    if (m.occasion) {
      s.addText(this.runs(m.occasion, { fontSize: 12, color: th.onDarkSub, bold: true, charSpacing: 3 }),
        { x: 1.0, y, w: W - 2.0, h: 0.3, margin: 0, align: "center", valign: "middle" });
      y += 0.42;
    }
    s.addText(this.runs(m.title, { fontSize: tSize, color: th.onDark, bold: true }),
      { x: 1.2, y, w: W - 2.4, h: t.h + 0.1, margin: 0, align: "center", valign: "top", lineSpacingMultiple: 1.16 });
    y += t.h + 0.22;
    if (m.subtitle) {
      s.addText(this.runs(m.subtitle, { fontSize: T.coverSub, color: th.onDarkSub }),
        { x: 1.0, y, w: W - 2.0, h: 0.36, margin: 0, align: "center", valign: "middle" });
      y += 0.5;
    }
    const below = bandTop + bandH + 0.55;
    this._infoRows(ctx, {
      x: (W - 5.0) / 2, y: below, w: 5.0, align: "center",
      rows: [[this.L.presenter, m.presenter], [this.L.advisor, m.advisor]],
    });
    const tail = [m.org, m.date].filter(Boolean).join("  ·  ");
    if (tail) s.addText(this.runs(tail, { fontSize: T.coverMeta, color: th.muted }),
      { x: 1.0, y: below + 1.32, w: W - 2.0, h: 0.34, margin: 0, align: "center", valign: "middle" });
    if (a.notes) s.addNotes(a.notes);
  }

  // 变体 solid:满版纯色(旧 plain 行为,保留给不需要校徽的场合)
  _coverSolid(ctx, a) {
    const th = this.theme, s = ctx.slide, m = this.meta;
    // 自带底图铺最底层:后面的实色块/色带会盖住它压到的部分,正是参考件的做法
    this._decor(ctx, "campus", { x: 0, y: 0, w: W, h: H });
    s.background = { color: th.primary };
    if (m.occasion) s.addText(this.runs(m.occasion, { fontSize: 13, color: th.onDarkSub, bold: true, charSpacing: 3.4 }),
      { x: M, y: 0.78, w: CW, h: 0.4, margin: 0, valign: "middle" });
    const tSize = a.titleSize || T.coverTitle;
    const t = this._measureTitle(m.title, tSize, CW);
    if (t.lines >= 4) this.warns.push(`封面标题 ${t.lines} 行(${tSize}pt),超过三行请缩短或降字号`);
    s.addText(this.runs(m.title, { fontSize: tSize, color: th.onDark, bold: true }),
      { x: M, y: 2.0, w: CW, h: t.h + 0.1, margin: 0, valign: "top", lineSpacingMultiple: 1.16 });
    let y = 2.0 + t.h + this._rulerGap(tSize);
    this._ruler(ctx, M, y, 1.5, th.onDarkSub);
    if (m.subtitle) s.addText(this.runs(m.subtitle, { fontSize: T.coverSub, color: th.onDarkSub }),
      { x: M, y: y + 0.34, w: CW, h: 0.4, margin: 0, valign: "middle" });
    s.addShape(this.pres.shapes.RECTANGLE, { x: M, y: 5.5, w: CW, h: 0.012, fill: { color: th.onDarkSub }, line: { type: "none" } });
    this._infoRows(ctx, {
      x: M, y: 5.74, w: CW * 0.5, onDark: true,
      rows: [[this.L.presenter, m.presenter], [this.L.advisor, m.advisor]],
    });
    const tail = [m.org, m.date].filter(Boolean).join("  ·  ");
    if (tail) s.addText(this.runs(tail, { fontSize: T.coverMeta, color: th.onDarkSub }),
      { x: M + CW * 0.5, y: 5.86, w: CW * 0.5, h: 0.34, margin: 0, align: "right", valign: "middle" });
    if (a.notes) s.addNotes(a.notes);
  }

  // ---------- 目录 ----------
  _toc(ctx) {
    const th = this.theme, s = ctx.slide;
    this._brandCorner(ctx);
    s.addText(this.runs(this.L.toc, { fontSize: 30, color: th.primary, bold: true, charSpacing: this.lang === "zh" ? 6 : 0 }), {
      x: M, y: 0.62, w: 6, h: 0.6, margin: 0 });
    s.addShape(this.pres.shapes.RECTANGLE, { x: M, y: 1.46, w: 1.15, h: 0.028,
      fill: { color: th.accent }, line: { type: "none" } });
    const n = this.sections.length;
    const rowH = Math.min(0.98, 4.6 / Math.max(n, 1));
    let y = 1.9;
    this.sections.forEach((sec, i) => {
      const num = String(i + 1).padStart(2, "0");
      s.addText([{ text: num, options: { fontFace: this.fonts.latin, fontSize: 22, color: th.accent, bold: true } }], {
        x: M + 0.05, y, w: 0.75, h: 0.5, margin: 0, valign: "middle" });
      s.addText(this.runs(sec.title, { fontSize: 17, color: th.ink, bold: true }), {
        x: M + 0.95, y, w: 7.6, h: 0.5, margin: 0, valign: "middle" });
      if (sec.note) s.addText(this.runs(sec.note, { fontSize: 12.5, color: th.muted }), {
        x: M + 8.7, y, w: CW - 8.7, h: 0.5, margin: 0, valign: "middle" });
      if (i < n - 1) s.addShape(this.pres.shapes.RECTANGLE, {
        x: M + 0.95, y: y + rowH - 0.09, w: CW - 0.95, h: 0.008, fill: { color: th.line }, line: { type: "none" } });
      y += rowH;
    });
    this._footer(ctx);
  }

  // ---------- 章节过渡页 ----------
  _section(ctx, a) {
    const th = this.theme, s = ctx.slide;
    // 章节页右上角铺蜂窝(Li-S 那份的章节页手法)。它落在超大章节号与
    // 右上角标之间的空区,不与任何文字相交。
    this._decor(ctx, "honeycomb", { right: 0, y: 0, h: 3.1 });
    this._brandCorner(ctx);
    // 超大章节号(浅色) + PART 标签
    s.addText([{ text: String(a.idx).padStart(2, "0"), options: {
      fontFace: this.fonts.latin, fontSize: T.sectionNum, color: th.tint, bold: true } }], {
      x: M - 0.06, y: 1.15, w: 4.4, h: 1.9, margin: 0, valign: "top", align: "left" });
    s.addText([{ text: `${this.L.part} ${String(a.idx).padStart(2, "0")}`, options: {
      fontFace: this.fonts.latin, fontSize: 13, color: th.accent, bold: true, charSpacing: 3 } }], {
      x: M + 0.02, y: 3.06, w: 3, h: 0.32, margin: 0 });
    s.addShape(this.pres.shapes.RECTANGLE, { x: M, y: 3.42, w: 0.032, h: 0.54,
      fill: { color: th.accent }, line: { type: "none" } });
    s.addText(this.runs(a.title, { fontSize: T.sectionTitle, color: th.primary, bold: true }), {
      x: M + 0.24, y: 3.36, w: CW - 0.24, h: 0.66, margin: 0, valign: "middle" });
    if (a.note) s.addText(this.runs(a.note, { fontSize: T.sectionNote, color: th.muted }), {
      x: M + 0.24, y: 4.1, w: CW - 1.5, h: 0.44, margin: 0, lineSpacingMultiple: 1.25 });
    // 本章要点预览:章节页不再是一句话 + 大片空白;要点给听众"这章会讲什么"的地图
    if (a.points && a.points.length) {
      const n = Math.min(a.points.length, 3);
      const gw = 0.5, cw2 = (CW - gw * (n - 1)) / n;
      a.points.slice(0, n).forEach((pt, i) => {
        const x = M + i * (cw2 + gw);
        s.addShape(this.pres.shapes.RECTANGLE, { x, y: 4.86, w: cw2, h: 0.02,
          fill: { color: th.line }, line: { type: "none" } });
        const [head, body] = Array.isArray(pt) ? pt : [pt, ""];
        s.addText(this.runs(head, { fontSize: 14, color: th.primary, bold: true }), {
          x, y: 4.98, w: cw2, h: 0.3, margin: 0 });
        if (body) s.addText(this.runs(body, { fontSize: 12.5, color: th.muted }), {
          x, y: 5.3, w: cw2, h: 0.68, margin: 0, valign: "top", lineSpacingMultiple: 1.22 });
      });
    }
    // 底部全章节导航,当前高亮
    let x = M;
    this.sections.forEach((sec, i) => {
      const label = `${String(i + 1).padStart(2, "0")} ${sec.title}`;
      const cur = i + 1 === a.idx;
      const wLbl = estW(label, 11.5) + 0.34;
      s.addText(this.runs(label, { fontSize: 11.5, color: cur ? th.accent : th.faint, bold: cur }), {
        x, y: 6.35, w: wLbl, h: 0.3, margin: 0, valign: "middle" });
      x += wLbl + 0.28;
    });
    this._footer(ctx);
    if (a.notes) s.addNotes(a.notes);
  }

  // ---------- 内容页 ----------
  _page(ctx, a) {
    const s = ctx.slide;
    this._brandCorner(ctx);
    const top = this._header(ctx, a);
    const srcH = this._sourceLine(ctx, a.source);
    const box = { x: M, y: top, w: CW, h: CONTENT_BOTTOM - srcH - top };
    this._renderBlocks(ctx, a.blocks || [], box, 1, true);
    this._footer(ctx);
    if (a.notes) s.addNotes(a.notes);
    if (a.appendix) { // 附录页:kicker 前加"附录"标识由调用方在 kicker 传入
    }
  }

  // ---------- 页内文献/数据来源行 ----------
  // 来源标注属于**页面**,不属于内容流。过去让作者用 callout 块写,它就跟着栏内
  // 纵向流走,落在右栏中部——读者在正文里撞见一行灰字来源,既打断论证又抢注意力。
  // 学术版式的惯例是把它压到页底、与正文用一条细线隔开:要看的人低头就找得到,
  // 不看的人完全不受影响。
  // 返回它占掉的高度,由 _page 从内容区里扣除,保证正文永远不会压到它。
  // 版面上它与页码共用右边缘(W - M),叠成页脚区的第二行——**右对齐本身就是
  // "这是注不是正文"的信号**,所以不加前缀标签、不加分隔线:拆过的两份真实汇报
  // 都没有 "来源:"/"Ref." 这类引导词,也都没有分隔线,加了反而给页面装上双层底框。
  // 字号 12pt 对齐 T.ref(参考文献页同号);颜色用 muted 不用 faint——
  // faint 在白底上对比度只有 2.6:1(AA 线 4.5:1),投影时这行等于没写。
  _sourceLine(ctx, source) {
    if (!source) return 0;
    const th = this.theme, s = ctx.slide;
    const list = (Array.isArray(source) ? source : [source]).filter(Boolean);
    if (!list.length) return 0;
    const text = list.join(this.lang === "zh" ? "；" : "; ");
    const size = 12;
    const lines = wrapCount(text, size, CW);
    // 不截断:静默丢掉一条文献是署名缺失,不是排版问题。让它变丑并报警,
    // 与块布局"降字仍溢出就警告、绝不裁内容"是同一条纪律。
    if (lines > 2) this.warns.push(
      `页 ${ctx.no} 的 source 占 ${lines} 行(上限 2)——页底来源行是查证入口,不是文献表。` +
      `只留最关键的一两条(如 "Nat. Chem. 17, 614-623 (2025)"),完整著录放 d.refs();` +
      `一页多图来自不同文献时,改用各自 figure 块的 credit`);
    const h = lines * SOURCE_LH;
    const y = SOURCE_BASE - h;                 // 底沿固定,多行向上长
    s.addText(this.runs(text, { fontSize: size, color: th.muted }),
      { x: M, y, w: CW, h, margin: 0, align: "right", valign: "middle", lineSpacingMultiple: 1.16 });
    return CONTENT_BOTTOM - y + SOURCE_GAP;
  }

  // ---------- 块布局引擎:纵向流式,先测量后绘制,超高整体降字号 ----------
  // 填充率:内容高 / 可用高。低于 FILL_MIN 视为"页面太空",发警告让作者补内容——
  // 刻意不自动放大字号或拉伸间距:那会破坏全篇字阶一致性,把一个问题换成另一个。
  _renderBlocks(ctx, blocks, box, fontScale = 1, top = false) {
    const measured = blocks.map(b => this._measure(ctx, b, box.w, fontScale));
    const totalH = measured.reduce((t, m) => t + m.h, 0) + GAP * Math.max(blocks.length - 1, 0);
    if (top && box.h > 1.5) {
      const fill = totalH / box.h;
      if (fill < FILL_MIN) this.warns.push(
        `页 ${ctx.no} 填充率 ${(fill * 100).toFixed(0)}%(建议 ≥ ${(FILL_MIN * 100).toFixed(0)}%)——内容偏少,` +
        `考虑:补一张小图/图表、把要点拆成"论断+证据"两层、加一句"本页要回答的问题"、或与相邻页合并`);
    }
    if (totalH > box.h + 0.02 && fontScale > 0.85) {
      return this._renderBlocks(ctx, blocks, box, fontScale - 0.06);
    }
    if (totalH > box.h + 0.02) this.warns.push(`页 ${ctx.no} 内容超高 ${(totalH - box.h).toFixed(2)}in,已降字仍溢出`);
    let y = box.y + Math.min(0.18, Math.max(0, (box.h - totalH) / 2) * 0.4);
    blocks.forEach((b, i) => {
      this._draw(ctx, b, { x: box.x, y, w: box.w, h: measured[i].h }, fontScale, measured[i]);
      y += measured[i].h + GAP;
    });
  }

  _fs(size, scale) { return Math.max(Math.round(size * scale * 2) / 2, 10); }

  _measure(ctx, b, w, sc) {
    const t = b.type;
    if (t === "text") return { h: textH(b.text, this._fs(b.size || T.body, sc), w) + 0.04 };
    if (t === "bullets") {
      let h = 0;
      for (const it of b.items) {
        const size = this._fs(b.size || T.body, sc);
        const full = (it.lead ? it.lead + "  " : "") + it.text;
        h += textH(full, size, w - 0.3) + (b.gap != null ? b.gap : 0.16);
      }
      return { h };
    }
    if (t === "stats") return { h: 1.45 * sc };
    if (t === "cards") {
      const cols = b.cols || Math.min(b.items.length, 3);
      const cw = (w - 0.32 * (cols - 1)) / cols;
      let maxH = 0;
      for (const it of b.items) {
        let h = 0.34; // 内边距
        if (it.title) h += textH(it.title, this._fs(T.cardTitle, sc), cw - 0.4) + 0.08;
        if (it.text) h += textH(it.text, this._fs(T.cardBody, sc), cw - 0.4);
        maxH = Math.max(maxH, h + 0.18);
      }
      const rows = Math.ceil(b.items.length / cols);
      return { h: maxH * rows + 0.3 * (rows - 1), cardH: maxH, cols, cw };
    }
    if (t === "figure") {
      const dim = imgSize(b.path);
      const credit = figureCredit(b);
      const capLine = b.caption || credit ? true : false;
      const capH = capLine ? textH((b.caption || "") + (credit || ""), T.caption, w) + 0.12 : 0;
      const maxH = (b.maxH || 4.6) * sc;
      const fit = fitRect(dim.w, dim.h, b.maxW || w, maxH - capH);
      return { h: fit.h + capH + 0.06, fit, capH, credit };
    }
    if (t === "table") {
      const rows = b.rows.length + 1;
      const rowH = (this._fs(T.tableBody, sc) * 1.35) / 72 + 0.22;
      return { h: rows * rowH + 0.06, rowH };
    }
    if (t === "steps") {
      let maxText = 0;
      const cols = b.items.length;
      const cw = (w - 0.3 * (cols - 1)) / cols;
      for (const it of b.items) {
        let h = 0.78;
        if (it.title) h += textH(it.title, this._fs(14, sc), cw) + 0.05;
        if (it.text) h += textH(it.text, this._fs(12, sc), cw);
        maxText = Math.max(maxText, h);
      }
      return { h: maxText + 0.1, cw };
    }
    if (t === "callout") {
      const size = this._fs(b.size || T.small, sc);
      return { h: Math.max(textH(b.text, size, w - (b.label ? 1.7 : 0.6)) + 0.3, 0.62) };
    }
    if (t === "cols") {
      const ratio = b.ratio || b.cols.map(() => 1);
      const sum = ratio.reduce((a, c) => a + c, 0);
      const gaps = 0.45 * (b.cols.length - 1);
      let maxH = 0;
      b.cols.forEach((col, i) => {
        const cwi = (w - gaps) * (ratio[i] / sum);
        const mh = col.blocks.map(x => this._measure(ctx, x, cwi, sc).h)
          .reduce((a2, c2) => a2 + c2, 0) + GAP * Math.max(col.blocks.length - 1, 0);
        maxH = Math.max(maxH, mh);
      });
      return { h: maxH, ratio, sum, gaps };
    }
    if (t === "chart") {
      const capH = b.caption ? textH(b.caption, T.caption, w) + 0.12 : 0;
      return { h: (b.height || 3.4) * sc + capH, capH };
    }
    if (t === "formula") {
      const dim = imgSize(b.path);
      const eqH = Math.min((b.height || 0.62) * sc, 1.6);          // 公式行高(按内容缩放)
      const eqW = Math.min(dim.w / dim.h * eqH, w - 1.0);
      const h2 = eqW / (dim.w / dim.h);
      let hh = h2 + 0.1;
      if (b.where && b.where.length) {
        const wsz = this._fs(T.caption + 0.5, sc);
        hh += textH(b.where.map(x => x.join(" ")).join("；"), wsz, w - 0.4) + 0.1;
      }
      return { h: hh, eqW, eqH: h2 };
    }
    if (t === "algorithm") {
      const sz = this._fs(b.size || 12.5, sc);
      let h = 0.34;                                                // 标题行
      for (const ln of b.lines) h += textH(ln.replace(/^\s+/, ""), sz, w - 0.9) + 0.055;
      return { h: h + 0.12 };
    }
    if (t === "spacer") return { h: b.h || 0.2 };
    throw new Error(`未知块类型: ${t}`);
  }

  _draw(ctx, b, box, sc, mz) {
    const th = this.theme, s = ctx.slide, t = b.type;
    if (t === "text") {
      s.addText(this.runs(b.text, {
        fontSize: this._fs(b.size || T.body, sc), color: b.color || th.ink,
        bold: b.bold || false, lead: b.lead,
      }), { x: box.x, y: box.y, w: box.w, h: box.h, margin: 0, valign: "top",
            align: b.align || "left", lineSpacingMultiple: 1.22 });
    } else if (t === "bullets") {
      let y = box.y;
      const size = this._fs(b.size || T.body, sc);
      b.items.forEach((it, i) => {
        const full = (it.lead ? it.lead + "  " : "") + it.text;
        const h = textH(full, size, box.w - 0.02);
        s.addText(this.runs(it.text, { fontSize: size, color: th.ink, lead: it.lead }), {
          x: box.x, y: y - 0.02, w: box.w, h: h + 0.06, margin: 0,
          valign: "top", lineSpacingMultiple: 1.26 });
        y += h + (b.gap != null ? b.gap : 0.16);
        // 条目间发丝分隔线:替代行首色块承担"分条"职责
        if (b.rule !== false && i < b.items.length - 1) {
          const gy = y - (b.gap != null ? b.gap : 0.16) / 2;
          s.addShape(this.pres.shapes.RECTANGLE, { x: box.x, y: gy, w: box.w, h: 0.007,
            fill: { color: th.line }, line: { type: "none" } });
        }
      });
    } else if (t === "stats") {
      const n = b.items.length, gw = 0.32;
      const cw = (box.w - gw * (n - 1)) / n;
      b.items.forEach((it, i) => {
        const x = box.x + i * (cw + gw);
        // 顶部标尺线代替填充块:数字靠字号与留白立住,不靠底色
        s.addShape(this.pres.shapes.RECTANGLE, { x, y: box.y, w: cw, h: 0.026,
          fill: { color: th.primary }, line: { type: "none" } });
        s.addText(this.runs(it.value, { fontSize: this._fs(T.statValue, sc), color: th.primary, bold: true }), {
          x, y: box.y + 0.16, w: cw, h: 0.66, margin: 0, align: "left", valign: "middle" });
        s.addText(this.runs(it.label, { fontSize: this._fs(T.statLabel, sc), color: th.ink, bold: true }), {
          x, y: box.y + 0.86, w: cw, h: 0.3, margin: 0, align: "left" });
        if (it.note) s.addText(this.runs(it.note, { fontSize: this._fs(T.statNote, sc), color: th.muted }), {
          x, y: box.y + 1.14, w: cw, h: 0.28, margin: 0, align: "left" });
      });
    } else if (t === "cards") {
      const { cardH, cols, cw } = mz;
      b.items.forEach((it, i) => {
        const r = Math.floor(i / cols), c = i % cols;
        const x = box.x + c * (cw + 0.32), y = box.y + r * (cardH + 0.3);
        // 顶部细线分栏,不画框、不填色
        s.addShape(this.pres.shapes.RECTANGLE, { x, y, w: cw, h: 0.02,
          fill: { color: th.line }, line: { type: "none" } });
        let yy = y + 0.16;
        if (it.title) {
          const tSz = this._fs(T.cardTitle, sc);
          const tH2 = textH(it.title, tSz, cw);
          s.addText(this.runs(it.title, { fontSize: tSz, color: th.primary, bold: true }), {
            x, y: yy - 0.04, w: cw, h: tH2 + 0.06, margin: 0 });
          yy += tH2 + 0.08;
        }
        if (it.text) s.addText(this.runs(it.text, { fontSize: this._fs(T.cardBody, sc), color: th.ink }), {
          x, y: yy, w: cw, h: cardH - (yy - y) - 0.06, margin: 0,
          valign: "top", lineSpacingMultiple: 1.24 });
      });
    } else if (t === "figure") {
      const { fit, capH, credit } = mz;
      const x = box.x + (box.w - fit.w) / 2;
      if (b.frame === true) s.addShape(this.pres.shapes.RECTANGLE, {   // 默认不加框;仅照片按需显式开启
        x: x - 0.035, y: box.y - 0.035, w: fit.w + 0.07, h: fit.h + 0.07,
        fill: { type: "none" }, line: { color: th.line, width: 0.75 } });
      s.addImage({ path: b.path, x, y: box.y, w: fit.w, h: fit.h });
      if (fromRegistry(b.path)) this.realPhotos += 1;   // 用于 build 时的实景图检查
      if (b.caption || credit) {
        let cap;
        if (b.caption) {
          this.figN += 1;
          cap = `${this.L.fig} ${this.figN}  ${b.caption}` + (credit ? `(${credit})` : "");
        } else {
          cap = credit; // 无图注的网络实景图:仍必须落署名行
        }
        s.addText(this.runs(cap, { fontSize: T.caption, color: th.muted }), {
          x: box.x, y: box.y + fit.h + 0.1, w: box.w, h: capH, margin: 0, align: "center" });
      }
    } else if (t === "table") {
      // 三线表:顶线/底线粗,栏目线细,无竖线
      const font = this._fs(T.tableBody, sc);
      const header = b.header.map(htxt => ({
        text: this.runs(htxt, {}), options: {
          bold: true, color: th.primary, fontSize: font,
          border: [{ pt: 1.5, color: th.primary }, { type: "none" }, { pt: 0.75, color: th.muted }, { type: "none" }],
          margin: 0.08, valign: "middle",
        } }));
      const rows = b.rows.map((r, ri) => r.map(cell => ({
        text: this.runs(cell, {}), options: {
          color: th.ink, fontSize: font,
          border: [{ type: "none" },{ type: "none" },
            ri === b.rows.length - 1 ? { pt: 1.5, color: th.primary } : { pt: 0.25, color: th.line },
            { type: "none" }],
          margin: 0.08, valign: "middle",
        } })));
      const colW = b.widths ? b.widths.map(x => x * box.w) : undefined;
      s.addTable([header, ...rows], { x: box.x, y: box.y, w: box.w, colW, fontFace: this.fonts.hans });
      if (b.caption) { this.tabN += 1; }
    } else if (t === "steps") {
      const { cw } = mz;
      const n = b.items.length;
      const cy = box.y + 0.26;
      // 连线
      s.addShape(this.pres.shapes.RECTANGLE, { x: box.x + cw / 2, y: cy - 0.011, w: (cw + 0.3) * (n - 1), h: 0.022,
        fill: { color: th.line }, line: { type: "none" } });
      b.items.forEach((it, i) => {
        const x = box.x + i * (cw + 0.3);
        s.addShape(this.pres.shapes.OVAL, { x: x + cw / 2 - 0.24, y: cy - 0.24, w: 0.48, h: 0.48,
          fill: { color: "FFFFFF" }, line: { color: th.primary, width: 1.4 } });
        s.addText([{ text: String(i + 1), options: { fontFace: this.fonts.latin, fontSize: 15, color: th.primary, bold: true } }], {
          x: x + cw / 2 - 0.24, y: cy - 0.24, w: 0.48, h: 0.48, align: "center", valign: "middle", margin: 0 });
        let yy = cy + 0.42;
        if (it.title) {
          s.addText(this.runs(it.title, { fontSize: this._fs(14, sc), color: th.primary, bold: true }), {
            x, y: yy, w: cw, h: 0.34, margin: 0, align: "center" });
          yy += textH(it.title, this._fs(14, sc), cw) + 0.06;
        }
        if (it.text) s.addText(this.runs(it.text, { fontSize: this._fs(12, sc), color: th.muted }), {
          x, y: yy, w: cw, h: box.h - (yy - box.y), margin: 0, align: "center", lineSpacingMultiple: 1.2 });
      });
    } else if (t === "callout") {
      // 来源标注属于页面不属于内容流,写成 callout 会跟着栏内纵向流走、落在栏中部
      if (b.label && /^(来源|数据来源|文献|出处|Source|Ref\.?|Reference)/i.test(b.label)) this.warns.push(
        `页 ${ctx.no} 用 callout 写来源标注——来源属于页面不属于内容流,` +
        `会跟着栏内流落在栏中部。改用 d.page({ source: "…" })`);

      // 左侧竖线 + 强调色标签:不画框、不填色、不用胶囊 chip
      const rule = b.tone === "warn" ? th.warm : th.accent;
      const txtColor = b.tone === "warn" ? th.muted : th.ink;
      s.addShape(this.pres.shapes.RECTANGLE, { x: box.x, y: box.y + 0.02, w: 0.026,
        h: Math.max(box.h - 0.04, 0.2), fill: { color: rule }, line: { type: "none" } });
      let tx = box.x + 0.22;
      if (b.label) {
        const lw = estW(b.label, 12) + 0.16;
        s.addText(this.runs(b.label, { fontSize: 12, color: rule, bold: true, charSpacing: 0.8 }), {
          x: tx, y: box.y + 0.06, w: lw, h: box.h - 0.12, align: "left", valign: "middle", margin: 0 });
        tx += lw + 0.16;
      }
      s.addText(this.runs(b.text, { fontSize: this._fs(b.size || T.small, sc), color: txtColor }), {
        x: tx, y: box.y + 0.04, w: box.x + box.w - tx, h: box.h - 0.08,
        margin: 0, valign: "middle", lineSpacingMultiple: 1.22 });
    } else if (t === "chart") {
      const { capH } = mz;
      const chH = box.h - capH;
      const kind = b.kind || "bar";
      const isPie = kind === "pie" || kind === "doughnut";
      // 饼/环每片颜色按索引取 chartColors,索引溢出时库会 Math.random() 取色
      // → 同一脚本连跑两次得到两组颜色。宁可报错也不交付不可复现的图。
      const need = isPie ? (b.data[0].labels || []).length : b.data.length;
      const pal = b.colors || seriesColors(th);
      // 饼/环 >3 类:角度判别不可靠、标签会压在扇区上。按 charts.md 该换降序水平条
      if (isPie && need > 3) this.warns.push(
        `页 ${ctx.no} ${kind} 图有 ${need} 个类别(上限 3)——角度判别在 4 类以上不可靠,` +
        `改用 kind:"barh" 降序水平条并在端点标数值(见 references/charts.md)`);
      if (pal.length < need) throw new Error(
        `chart(${kind}): 需要 ${need} 个颜色但色板只有 ${pal.length} 个。` +
        `类别/系列过多正是该换图型的信号(见 references/charts.md);或显式传 colors。`);
      const common = {
        x: box.x, y: box.y, w: box.w, h: chH,
        chartColors: pal.slice(0, need),
        // 这些开关不显式传就等于没传(库内是恒等赋值),必须逐个给 true
        showLegend: b.legend !== false && (isPie || b.data.length > 1),
        legendPos: b.legendPos || (isPie ? "r" : "t"),
        legendFontSize: this._fs(11, sc), legendColor: th.ink,
        dataLabelFontSize: this._fs(11, sc), dataLabelFontFace: this.fonts.latin,
        // 不传 shadow:图表默认无阴影,传 {type:'none'} 会拼出非法的 <a:noneShdw>
      };
      let opts;
      if (isPie) {
        // showValue 与 showPercent 共用同一个 numFmt,同开会把原始值也按百分比格式化
        const pct = b.showValue ? false : (b.showPercent !== false);
        opts = { ...common,
          showPercent: pct, showValue: !!b.showValue,
          dataLabelColor: "FFFFFF",   // 扇区为中高饱和主题色,白字最稳
          dataLabelFormatCode: b.numFmt,
          holeSize: kind === "doughnut" ? Math.min(Math.max(b.holeSize || 58, 1), 90) : undefined,
          // 环形图的 dataLabelPosition 会被库无条件删除,不传
        };
      } else {
        const horiz = kind === "barh";
        const isLine = kind === "line" || kind === "area";
        opts = { ...common,
          catAxisLabelColor: th.muted, catAxisLabelFontSize: this._fs(11, sc),
          catAxisLineShow: true, catAxisLineColor: th.line,
          catAxisMajorTickMark: "none",
          valAxisLabelColor: th.muted, valAxisLabelFontSize: this._fs(11, sc),
          valAxisLineShow: false, valAxisMajorTickMark: "none",
          // 值轴默认带 1pt #888888 粗网格线,是"默认图很丑"的头号原因
          valGridLine: b.grid === false ? { style: "none" } : { color: th.line, size: 0.5, style: "solid" },
          catGridLine: { style: "none" },
          valAxisTitle: b.valTitle, showValAxisTitle: !!b.valTitle,
          valAxisTitleColor: th.muted, valAxisTitleFontSize: this._fs(11, sc),
          catAxisTitle: b.catTitle, showCatAxisTitle: !!b.catTitle,
          catAxisTitleColor: th.muted, catAxisTitleFontSize: this._fs(11, sc),
          dataLabelColor: th.ink,
          dataLabelFormatCode: b.numFmt,   // 如 "0.0" 保留一位小数,默认会四舍五入到整数
        };
        if (isLine) {
          opts.lineSize = b.lineSize || 2.2;
          // 样条插值会凭空造出不存在的极值 = 用平滑伪造数据
          opts.lineSmooth = false;
          const pts = (b.data[0].labels || []).length;
          opts.lineDataSymbol = pts <= 12 ? "circle" : "none";
          opts.lineDataSymbolSize = 6;
          opts.showValue = !!b.showValue;
        } else {
          opts.barDir = horiz ? "bar" : "col";
          opts.barGapWidthPct = Math.min(b.gapPct || 60, 500);
          opts.barOverlapPct = b.overlapPct != null ? b.overlapPct : -8;
          opts.barGrouping = b.stacked ? (b.percent ? "percentStacked" : "stacked") : "clustered";
          opts.showValue = b.showValue !== false;
          // 堆叠只接受 ctr/inBase/inEnd(传 outEnd 会让 PowerPoint 判定文件损坏);
          // 簇状传 outEnd 会被库静默删掉,索性不传,用 PowerPoint 默认位置
          if (b.stacked) opts.dataLabelPosition = "ctr";
          if (b.percent) opts.dataLabelFormatCode = "0%";
        }
      }
      const nameMap = { bar: "BAR", barh: "BAR", pie: "PIE", doughnut: "DOUGHNUT",
                        line: "LINE", area: "AREA", scatter: "SCATTER", radar: "RADAR" };
      s.addChart(this.pres.charts[nameMap[kind] || "BAR"], b.data, opts);
      this.hasChart = true;   // 触发 build 后处理:给图表补中文字体
      if (b.caption) {
        this.figN += 1;
        s.addText(this.runs(`${this.L.fig} ${this.figN}  ${b.caption}`,
          { fontSize: T.caption, color: th.muted }), {
          x: box.x, y: box.y + chH + 0.08, w: box.w, h: capH, margin: 0, align: "center" });
      }
    } else if (t === "formula") {
      const { eqW, eqH } = mz;
      const x = box.x + (box.w - eqW) / 2;
      s.addImage({ path: b.path, x, y: box.y, w: eqW, h: eqH });
      if (b.tag) s.addText(this.runs(b.tag, { fontSize: T.caption + 0.5, color: th.muted }), {
        x: box.x, y: box.y + eqH / 2 - 0.14, w: box.w, h: 0.28, margin: 0, align: "right" });
      if (b.where && b.where.length) {
        const runs = [{ text: b.whereLabel || "其中", options: {
          fontFace: this.fonts.hans, fontSize: T.caption + 0.5, color: th.muted, bold: true } }];
        b.where.forEach(([sym, mean], i) => {
          runs.push(...this.runs(`  ${sym} `, { fontSize: T.caption + 0.5, color: th.primary, bold: true }));
          runs.push(...this.runs(mean + (i < b.where.length - 1 ? "；" : "。"),
            { fontSize: T.caption + 0.5, color: th.muted }));
        });
        s.addText(runs, { x: box.x + 0.2, y: box.y + eqH + 0.12, w: box.w - 0.4, h: box.h - eqH - 0.14,
          margin: 0, valign: "top", lineSpacingMultiple: 1.24 });
      }
    } else if (t === "algorithm") {
      // 伪代码:左侧竖线 + 等宽行号,不画框不填色
      const sz = this._fs(b.size || 12.5, sc);
      s.addShape(this.pres.shapes.RECTANGLE, { x: box.x, y: box.y + 0.02, w: 0.026,
        h: Math.max(box.h - 0.06, 0.2), fill: { color: th.primary }, line: { type: "none" } });
      let y = box.y + 0.02;
      if (b.title) {
        s.addText(this.runs(b.title, { fontSize: sz + 1, color: th.primary, bold: true }), {
          x: box.x + 0.22, y, w: box.w - 0.24, h: 0.3, margin: 0 });
        y += 0.32;
      }
      b.lines.forEach((raw, i) => {
        const indent = (raw.match(/^\s*/) || [""])[0].length * 0.075;   // 前导空格 → 缩进
        const txt = raw.trim();
        const h = textH(txt, sz, box.w - 0.9 - indent);
        s.addText([{ text: String(i + 1).padStart(2, " "), options: {
          fontFace: this.fonts.mono || "Menlo", fontSize: sz - 1.5, color: th.faint } }], {
          x: box.x + 0.22, y, w: 0.3, h: h + 0.04, margin: 0, align: "right" });
        s.addText(this.runs(txt, { fontSize: sz, color: th.ink }), {
          x: box.x + 0.62 + indent, y, w: box.w - 0.66 - indent, h: h + 0.04,
          margin: 0, valign: "top", lineSpacingMultiple: 1.2 });
        y += h + 0.055;
      });
    } else if (t === "cols") {
      const { ratio, sum, gaps } = mz;
      let x = box.x;
      b.cols.forEach((col, i) => {
        const cwi = (box.w - gaps) * (ratio[i] / sum);
        this._renderBlocks(ctx, col.blocks, { x, y: box.y, w: cwi, h: box.h }, sc);
        x += cwi + 0.45;
      });
    }
  }

  // ---------- 参考文献页 ----------
  _refs(ctx, a) {
    const th = this.theme, s = ctx.slide;
    this._brandCorner(ctx);
    const top = this._header(ctx, { title: a.title || this.L.refs, kicker: a.kicker || "" });
    const list = a.list;
    const twoCol = list.length > 5;
    const colN = twoCol ? Math.ceil(list.length / 2) : list.length;
    const colW2 = twoCol ? (CW - 0.6) / 2 : CW;
    [list.slice(0, colN), list.slice(colN)].forEach((col, ci) => {
      if (!col.length) return;
      let y = top;
      col.forEach((r, i) => {
        const idx = ci * colN + i + 1;
        const h = textH(r, T.ref, colW2 - 0.34) + 0.1;
        const x = M + ci * (colW2 + 0.6);
        s.addText([{ text: `[${idx}]`, options: { fontFace: this.fonts.latin, fontSize: T.ref, color: th.accent, bold: true } }], {
          x, y, w: 0.4, h: 0.3, margin: 0 });
        s.addText(this.runs(r, { fontSize: T.ref, color: th.ink }), {
          x: x + 0.42, y, w: colW2 - 0.42, h, margin: 0, valign: "top", lineSpacingMultiple: 1.18 });
        y += h + 0.08;
      });
    });
    this._footer(ctx);
  }

  // ---------- 结束页 ----------
  // 结束页与封面是**镜像呼应**,不是同一张版:封面留"面"(整块色),结束页只留"线"
  // (底部一道细色带)。旧实现让两者共用 _bandBase,除文字外像素级同构,
  // 观众看到结束页的第一反应是"翻回封面了"。
  //
  // 另一处重做:这是 Q&A 全程停在幕布上的那一页。写"恳请各位专家批评指正"等于
  // 让观众盯着一句客套话十分钟,takeaway 槽位放最想被记住的那句结论。
  _closing(ctx, a) {
    const th = this.theme, s = ctx.slide, m = this.meta, R = this.pres.shapes.RECTANGLE;
    this._decor(ctx, "campus", { x: 0, y: 0, w: W, h: H });
    this._brandCorner(ctx);
    const main = a.main || KINDS[this.kind].closing[this.lang] || this.L.closingMain;
    const t = this._measureTitle(main, 34, CW);
    const y0 = 2.55;
    s.addText(this.runs(main, { fontSize: 34, color: th.primary, bold: true }),
      { x: M, y: y0, w: CW, h: t.h + 0.1, margin: 0, valign: "top", lineSpacingMultiple: 1.16 });
    let y = y0 + t.h + this._rulerGap(34);
    this._ruler(ctx, M, y, 1.5, th.primary);
    y += 0.40;
    if (a.takeaway) {
      const tk = this._measureTitle(a.takeaway, 18, 9.5);
      if (tk.lines > 2) this.warns.push("结束页 takeaway 超过两行——它是一句要被记住的结论,不是段落");
      s.addText(this.runs(a.takeaway, { fontSize: 18, color: th.ink }),
        { x: M, y, w: 9.5, h: tk.h + 0.1, margin: 0, valign: "top", lineSpacingMultiple: 1.3 });
    } else if (a.sub) {
      s.addText(this.runs(a.sub, { fontSize: 15, color: th.muted }),
        { x: M, y, w: CW, h: 0.45, margin: 0, valign: "middle" });
    }

    // 三级消隐线:实 1.50in → 中 3.20in → 虚 7.19in。y=5.62 与 plate 封面色带上沿、
    // split 封面信息区分界线是同一条——封面在这条线上是"面",结束页缩成一条消散的线。
    s.addShape(R, { x: M, y: 5.615, w: 1.50, h: 0.030, fill: { color: th.primary }, line: { type: "none" } });
    s.addShape(R, { x: M + 1.50, y: 5.624, w: 3.20, h: 0.012, fill: { color: th.line }, line: { type: "none" } });
    s.addShape(R, { x: M + 4.70, y: 5.627, w: CW - 4.70, h: 0.006, fill: { color: th.washBorder }, line: { type: "none" } });
    const cols = [];
    if (a.contact) cols.push(["联系方式", a.contact]);
    for (const [k, v] of (a.links || [])) cols.push([k, v]);
    if (!cols.length && m.org) cols.push(["单位", m.org]);
    const cw = 3.6;
    cols.slice(0, 3).forEach(([k, v], i) => {
      this._infoRows(ctx, { x: M + i * (cw + 0.4), y: 5.86, w: cw, rows: [[k, v]] });
    });
    if (a.qr && fs.existsSync(a.qr)) {
      s.addImage({ path: a.qr, x: W - M - 0.95, y: 5.78, w: 0.95, h: 0.95 });
      if (a.qrNote) s.addText(this.runs(a.qrNote, { fontSize: 10.5, color: th.muted }),
        { x: W - M - 1.9, y: 6.78, w: 1.9, h: 0.28, margin: 0, align: "right", valign: "middle" });
    }
    // 底部细带:与封面的整块色形成一厚一薄的呼应
    s.addShape(R, { x: 0, y: 7.44, w: W, h: 0.06, fill: { color: th.primary }, line: { type: "none" } });
    if (a.notes) s.addNotes(a.notes);
  }

  // ---------- 致谢页 ----------
  // 答辩/结题/基金汇报的固定动作。过去只能用 d.page() 硬凑,一凑就写成 bullets 列表、
  // 看着像内容页。此页走内容页骨架(同网格、同页眉页脚),与封面刻意区别开。
  _ack(ctx, a) {
    const th = this.theme, s = ctx.slide, R = this.pres.shapes.RECTANGLE;
    // 与封面同一把梯子、同一个色、同一种衰减,但**没有实色块**:
    // 封面是"面",致谢是"面的影子"。不设 background,保持与内容页同骨架。
    this._decor(ctx, "campus", { x: 0, y: 0, w: W, h: H });
    this._brandCorner(ctx);
    s.addText(this.runs(this.L.ack, { fontSize: 30, color: th.primary, bold: true, charSpacing: this.lang === "zh" ? 6 : 0 }),
      { x: M, y: 0.62, w: 6, h: 0.6, margin: 0 });
    s.addShape(R, { x: M, y: 1.46, w: 1.15, h: 0.028, fill: { color: th.accent }, line: { type: "none" } });

    const colW = (CW - 0.45) / 2;
    const left = [];
    for (const [name, role] of (a.advisor || [])) left.push([name, role, true]);
    for (const [name, role] of (a.collab || [])) left.push([name, role, false]);
    const right = [];
    for (const [name, no] of (a.funding || [])) right.push([name, no, true]);
    for (const f of (a.facility || [])) right.push([f, "", false]);

    [[left, this.L.ackPeople, M], [right, this.L.ackSupport, M + colW + 0.45]].forEach(([items, head, x]) => {
      if (!items.length) return;
      s.addShape(R, { x, y: 1.98, w: colW, h: 0.02, fill: { color: th.line }, line: { type: "none" } });
      s.addText(this.runs(head, { fontSize: 12, color: th.muted, bold: true, charSpacing: 2 }),
        { x, y: 2.06, w: colW, h: 0.3, margin: 0, valign: "middle" });
      let y = 2.52;
      for (const [name, note, strong] of items) {
        s.addText(this.runs(name, { fontSize: 15, color: th.ink, bold: strong }),
          { x, y, w: colW, h: 0.3, margin: 0, valign: "middle" });
        if (note) s.addText(this.runs(note, { fontSize: 12, color: th.muted }),
          { x, y: y + 0.30, w: colW, h: 0.28, margin: 0, valign: "middle" });
        y += note ? 0.70 : 0.44;
      }
    });
    if (a.group) s.addText(this.runs(a.group, { fontSize: 13, color: th.muted }),
      { x: M, y: 6.16, w: CW, h: 0.32, margin: 0, valign: "middle" });
    s.addShape(R, { x: 0, y: 7.44, w: W, h: 0.06, fill: { color: th.primary }, line: { type: "none" } });
    this._footer(ctx);
    if (a.notes) s.addNotes(a.notes);
  }
}

// ---------- 放映效果:写盘后向每页注入 <p:transition>(pptxgenjs 不支持切换) ----------
// 默认克制的 fade;Deck 构造传 transition: "fade"|"wipe"|"push"|"none" 可改。
// 注入点:</p:sld> 之前(schema 顺序 cSld → clrMapOvr → transition),幂等。
const TRANSITIONS = {
  fade: '<p:fade/>',
  wipe: '<p:wipe dir="r"/>',
  push: '<p:push dir="r"/>',
};
// 写盘后处理:一次解包完成两件事
//   1) 每页注入放映切换(pptxgenjs 无此 API)
//   2) 给图表文字补 <a:ea>:pptxgenjs 只写 <a:latin>,图表里的中文会被 PowerPoint
//      回退到"等线",与正文字体不一致——这是原生图表唯一必须打的补丁
async function postProcess(fileName, { transition, cjkFont }) {
  const frag = transition && transition !== "none" ? TRANSITIONS[transition] : null;
  if (transition && transition !== "none" && !frag) console.warn(`slidekit: 未知放映效果 ${transition},已跳过`);
  let JSZip;
  try { JSZip = require("jszip"); } catch { console.warn("slidekit: 缺 jszip,后处理跳过"); return; }
  const zip = await JSZip.loadAsync(fs.readFileSync(fileName));

  if (frag) {
    for (const n of Object.keys(zip.files).filter((x) => /^ppt\/slides\/slide\d+\.xml$/.test(x))) {
      let xml = await zip.file(n).async("string");
      if (xml.includes("<p:transition")) continue;
      zip.file(n, xml.replace("</p:sld>", `<p:transition spd="med">${frag}</p:transition></p:sld>`));
    }
  }
  if (cjkFont) {
    const esc = cjkFont.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
    for (const n of Object.keys(zip.files).filter((x) => /^ppt\/charts\/chart\d+\.xml$/.test(x))) {
      let xml = await zip.file(n).async("string");
      if (xml.includes("<a:ea ")) continue;
      xml = xml.replace(/<a:latin typeface="([^"]*)"\s*\/>/g,
        (m) => `${m}<a:ea typeface="${esc}"/>`);
      zip.file(n, xml);
    }
  }
  fs.writeFileSync(fileName, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

// ---------- 网络图自动署名:读图片同目录 credits.json(fetchimg.py 生成) ----------
// 显式传 credit 优先;否则命中 credits.json 就自动生成"作者 / 许可 · 来源"。
// 机制保证:fetchimg 拉的图,署名永远不会漏。
const creditsCache = new Map();
function figureCredit(b) {
  if (b.credit !== undefined) return b.credit || "";
  const dir = path.dirname(b.path);
  if (!creditsCache.has(dir)) {
    const p = path.join(dir, "credits.json");
    let data = null;
    try { data = JSON.parse(fs.readFileSync(p, "utf8")); } catch { /* 无登记文件 */ }
    creditsCache.set(dir, data);
  }
  const reg = creditsCache.get(dir);
  const hit = reg && reg[path.basename(b.path)];
  if (!hit) return "";
  const src = hit.provider === "wikimedia" ? "Wikimedia Commons" : (hit.provider || "");
  // 兜底:credits.json 里可能存着 Openverse 的多来源脏串
  // ("real name: X pl.wiki: Y commons: Z"),署名行放不下,取第一个姓名并限长
  let who = String(hit.creator || "").replace(/real name:\s*/i, "")
    .split(/\s+[a-z]*\.?wiki\s*:|\s+commons\s*:/i)[0].replace(/\s+/g, " ").trim();
  if (who === "unknown") who = "";
  if (who.length > 29) who = who.slice(0, 28) + "\u2026";
  return [who, hit.license, src].filter(Boolean).join(" / ");
}

// 该图片是否登记在同目录 credits.json 里(即 fetchimg/aiimg 取来的、带许可的图)。
// 只统计 fetchimg 来源:AI 生成图不算"真实照片"。
function fromRegistry(imgPath) {
  const dir = path.dirname(imgPath);
  if (!creditsCache.has(dir)) {
    let data = null;
    try { data = JSON.parse(fs.readFileSync(path.join(dir, "credits.json"), "utf8")); } catch { }
    creditsCache.set(dir, data);
  }
  const reg = creditsCache.get(dir);
  const hit = reg && reg[path.basename(imgPath)];
  return !!(hit && hit.license && !String(hit.license).includes("AI"));
}

// ---------- 图片尺寸读取(PNG/JPEG,防变形) ----------
function imgSize(p) {
  const buf = fs.readFileSync(p);
  if (buf.readUInt32BE(0) === 0x89504e47) { // PNG
    return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
  }
  if (buf.readUInt16BE(0) === 0xffd8) { // JPEG
    let off = 2;
    while (off < buf.length - 8) {
      if (buf[off] !== 0xff) { off++; continue; }
      const marker = buf[off + 1];
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return { h: buf.readUInt16BE(off + 5), w: buf.readUInt16BE(off + 7) };
      }
      off += 2 + buf.readUInt16BE(off + 2);
    }
  }
  throw new Error(`无法读取图片尺寸(仅支持 PNG/JPEG): ${p}`);
}
function fitRect(iw, ih, bw, bh) {
  const k = Math.min(bw / iw, bh / ih);
  return { w: iw * k, h: ih * k };
}

module.exports = { Deck, THEMES, T, imgSize };
