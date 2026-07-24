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

// ---------- 语言包 ----------
const LANG = {
  zh: { toc: "目 录", refs: "参考文献", fig: "图", tab: "表",
        presenter: "汇报人", advisor: "指导教师", part: "PART",
        closingMain: "恳请各位专家批评指正", appendix: "附录" },
  en: { toc: "Contents", refs: "References", fig: "Fig.", tab: "Table",
        presenter: "Presenter", advisor: "Advisor", part: "PART",
        closingMain: "Thank You", appendix: "Appendix" },
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
    this.meta = opts;         // title/shortTitle/occasion/presenter/advisor/org/date
    this.ops = [];            // 延迟渲染:build 时统一执行(目录/页码需要全局信息)
    this.sections = [];       // {title, note, opIndex}
    this.figN = 0; this.tabN = 0;
    this.warns = [];
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
    const style = opts.coverStyle || (seal ? "band" : "plain");
    return { logo, seal, style, corner: opts.cornerLogo !== false && !!logo };
  }

  // 正文/章节/目录/参考文献页右上角的横排 logo(印章+校名),等高缩放不变形
  _brandCorner(ctx) {
    if (!this.brand.corner || !this.brand.logo) return;
    const d = imgSize(this.brand.logo);
    const h = 0.4, w = h * d.w / d.h;
    ctx.slide.addImage({ path: this.brand.logo, x: W - M - w, y: 0.34, w, h });
  }

  // band 式封面/结束页:白底 + 居中红带 + 印章骑在红带上沿,主文字居中于带内
  _bandBase(ctx, o) {
    const th = this.theme, s = ctx.slide, R = this.pres.shapes.RECTANGLE;
    // 印章整枚坐落白区、下沿切于红带上沿(印章与红带同色,故不让其没入红带)
    const sealH = 1.4, sealTop = 0.55, bandTop = sealTop + sealH, bandH = 3.3;
    s.addShape(R, { x: 0, y: bandTop, w: W, h: bandH, fill: { color: th.primary }, line: { type: "none" } });
    if (this.brand.seal) {
      const d = imgSize(this.brand.seal), sw = sealH * d.w / d.h;
      s.addImage({ path: this.brand.seal, x: (W - sw) / 2, y: sealTop, w: sw, h: sealH });
    }
    s.addText(this.runs(o.main, { fontSize: o.mainSize || T.coverTitle, color: th.onDark, bold: true, align: "center" }),
      { x: 1.0, y: 2.62, w: W - 2.0, h: 1.5, margin: 0, align: "center", valign: "middle", lineSpacingMultiple: 1.12 });
    if (o.sub) {
      s.addText(this.runs(o.sub, { fontSize: T.coverSub, color: th.onDarkSub, align: "center" }),
        { x: 1.0, y: 4.32, w: W - 2.0, h: 0.4, margin: 0, align: "center", valign: "middle" });
      s.addShape(R, { x: W / 2 - 0.35, y: 4.82, w: 0.7, h: 0.014, fill: { color: th.onDarkSub }, line: { type: "none" } });
    }
    let y = 5.98;
    [o.meta1, o.meta2].filter(Boolean).forEach((ln, i) => {
      s.addText(this.runs(ln, { fontSize: T.coverMeta, color: i === 0 ? th.ink : th.muted, align: "center" }),
        { x: 1.0, y, w: W - 2.0, h: 0.36, margin: 0, align: "center", valign: "middle" });
      y += 0.42;
    });
    if (o.notes) s.addNotes(o.notes);
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
  section(title, note) {
    this.sections.push({ title, note });
    this.ops.push({ k: "section", a: { title, note, idx: this.sections.length } });
  }
  page(a) { this.ops.push({ k: "page", a }); }
  refs(list, opts = {}) { this.ops.push({ k: "refs", a: { list, ...opts } }); }
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
      else if (op.k === "closing") this._closing(ctx, op.a);
    }
    await pres.writeFile({ fileName });
    if (this.warns.length) {
      console.warn("slidekit 布局警告(建议处理):");
      this.warns.forEach(w => console.warn("  - " + w));
    }
    console.log(`written: ${fileName} (${total} slides)`);
  }

  // ---------- 通用小件 ----------
  _sq(s, x, y, size, color) { // 母题:小方块
    s.addShape(this.pres.shapes.RECTANGLE, { x, y, w: size, h: size, fill: { color }, line: { type: "none" } });
  }
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
      this._sq(ctx.slide, M, y + 0.035, 0.1, th.warm);
      ctx.slide.addText(this.runs(kicker, { fontSize: T.kicker, color: th.accent, bold: true, charSpacing: 2 }), {
        x: M + 0.2, y: y - 0.06, w: CW - 0.2, h: 0.3, margin: 0, valign: "middle" });
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
  _cover(ctx, a) {
    const th = this.theme, s = ctx.slide, m = this.meta;
    if (this.brand.style === "band" && this.brand.seal) {
      return this._bandBase(ctx, {
        main: m.title, mainSize: a.titleSize || T.coverTitle,
        sub: m.subtitle || m.occasion,
        meta1: [
          m.presenter ? `${this.L.presenter}:${m.presenter}` : null,
          m.advisor ? `${this.L.advisor}:${m.advisor}` : null,
        ].filter(Boolean).join("     "),
        meta2: [m.org, m.date].filter(Boolean).join("  ·  "),
        notes: a.notes,
      });
    }
    s.background = { color: th.primary };
    // 母题:左上小方块 + 场合
    this._sq(s, M, 0.92, 0.13, th.warm);
    if (m.occasion) s.addText(this.runs(m.occasion, { fontSize: 13, color: th.onDarkSub, bold: true, charSpacing: 3 }), {
      x: M + 0.26, y: 0.78, w: CW - 0.26, h: 0.4, margin: 0, valign: "middle" });
    // 主标题
    const tSize = a.titleSize || T.coverTitle;
    s.addText(this.runs(m.title, { fontSize: tSize, color: th.onDark, bold: true }), {
      x: M, y: 2.0, w: CW, h: 2.1, margin: 0, valign: "top", lineSpacingMultiple: 1.16 });
    if (m.subtitle) s.addText(this.runs(m.subtitle, { fontSize: T.coverSub, color: th.onDarkSub }), {
      x: M, y: 4.15, w: CW, h: 0.4, margin: 0 });
    // 底部信息区:细线 + 汇报人/导师/单位/日期
    s.addShape(this.pres.shapes.RECTANGLE, { x: M, y: 5.5, w: CW, h: 0.012, fill: { color: th.onDarkSub }, line: { type: "none" } });
    const meta1 = [
      m.presenter ? `${this.L.presenter}:${m.presenter}` : null,
      m.advisor ? `${this.L.advisor}:${m.advisor}` : null,
    ].filter(Boolean).join("    ");
    const meta2 = [m.org, m.date].filter(Boolean).join(" · ");
    if (meta1) s.addText(this.runs(meta1, { fontSize: T.coverMeta, color: th.onDark }), {
      x: M, y: 5.72, w: CW, h: 0.36, margin: 0 });
    s.addText(this.runs(meta2, { fontSize: T.coverMeta, color: th.onDarkSub }), {
      x: M, y: meta1 ? 6.1 : 5.72, w: CW, h: 0.36, margin: 0 });
    if (a.notes) s.addNotes(a.notes);
  }

  // ---------- 目录 ----------
  _toc(ctx) {
    const th = this.theme, s = ctx.slide;
    this._brandCorner(ctx);
    s.addText(this.runs(this.L.toc, { fontSize: 30, color: th.primary, bold: true, charSpacing: this.lang === "zh" ? 6 : 0 }), {
      x: M, y: 0.62, w: 6, h: 0.6, margin: 0 });
    this._sq(s, M, 1.42, 0.12, th.warm);
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
    this._brandCorner(ctx);
    // 超大章节号(浅色) + PART 标签
    s.addText([{ text: String(a.idx).padStart(2, "0"), options: {
      fontFace: this.fonts.latin, fontSize: T.sectionNum, color: th.tint, bold: true } }], {
      x: M - 0.06, y: 1.15, w: 4.4, h: 1.9, margin: 0, valign: "top", align: "left" });
    s.addText([{ text: `${this.L.part} ${String(a.idx).padStart(2, "0")}`, options: {
      fontFace: this.fonts.latin, fontSize: 13, color: th.accent, bold: true, charSpacing: 3 } }], {
      x: M + 0.02, y: 3.06, w: 3, h: 0.32, margin: 0 });
    this._sq(s, M, 3.62, 0.13, th.warm);
    s.addText(this.runs(a.title, { fontSize: T.sectionTitle, color: th.primary, bold: true }), {
      x: M + 0.3, y: 3.36, w: CW - 0.3, h: 0.66, margin: 0, valign: "middle" });
    if (a.note) s.addText(this.runs(a.note, { fontSize: T.sectionNote, color: th.muted }), {
      x: M + 0.3, y: 4.12, w: CW - 1.5, h: 0.6, margin: 0, lineSpacingMultiple: 1.25 });
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
    const box = { x: M, y: top, w: CW, h: CONTENT_BOTTOM - top };
    this._renderBlocks(ctx, a.blocks || [], box);
    this._footer(ctx);
    if (a.notes) s.addNotes(a.notes);
    if (a.appendix) { // 附录页:kicker 前加"附录"标识由调用方在 kicker 传入
    }
  }

  // ---------- 块布局引擎:纵向流式,先测量后绘制,超高整体降字号 ----------
  _renderBlocks(ctx, blocks, box, fontScale = 1) {
    const measured = blocks.map(b => this._measure(ctx, b, box.w, fontScale));
    const totalH = measured.reduce((t, m) => t + m.h, 0) + GAP * Math.max(blocks.length - 1, 0);
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
      const capH = b.caption ? textH(b.caption, T.caption, w) + 0.12 : 0;
      const maxH = (b.maxH || 4.6) * sc;
      const fit = fitRect(dim.w, dim.h, b.maxW || w, maxH - capH);
      return { h: fit.h + capH + 0.06, fit, capH };
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
      for (const it of b.items) {
        const full = (it.lead ? it.lead + "  " : "") + it.text;
        const h = textH(full, size, box.w - 0.3);
        this._sq(s, box.x + 0.02, y + (size / 72) * 0.42, 0.085, th.warm);
        s.addText(this.runs(it.text, { fontSize: size, color: th.ink, lead: it.lead }), {
          x: box.x + 0.3, y: y - 0.02, w: box.w - 0.3, h: h + 0.06, margin: 0,
          valign: "top", lineSpacingMultiple: 1.24 });
        y += h + (b.gap != null ? b.gap : 0.16);
      }
    } else if (t === "stats") {
      const n = b.items.length, gw = 0.32;
      const cw = (box.w - gw * (n - 1)) / n;
      b.items.forEach((it, i) => {
        const x = box.x + i * (cw + gw);
        s.addShape(this.pres.shapes.ROUNDED_RECTANGLE, { x, y: box.y, w: cw, h: box.h,
          fill: { color: th.wash }, line: { color: th.washBorder, width: 1 }, rectRadius: 0.055 });
        s.addText(this.runs(it.value, { fontSize: this._fs(T.statValue, sc), color: th.accent, bold: true }), {
          x: x + 0.15, y: box.y + 0.12, w: cw - 0.3, h: 0.66, margin: 0, align: "center", valign: "middle" });
        s.addText(this.runs(it.label, { fontSize: this._fs(T.statLabel, sc), color: th.ink, bold: true }), {
          x: x + 0.15, y: box.y + 0.8, w: cw - 0.3, h: 0.3, margin: 0, align: "center" });
        if (it.note) s.addText(this.runs(it.note, { fontSize: this._fs(T.statNote, sc), color: th.muted }), {
          x: x + 0.15, y: box.y + 1.1, w: cw - 0.3, h: 0.28, margin: 0, align: "center" });
      });
    } else if (t === "cards") {
      const { cardH, cols, cw } = mz;
      b.items.forEach((it, i) => {
        const r = Math.floor(i / cols), c = i % cols;
        const x = box.x + c * (cw + 0.32), y = box.y + r * (cardH + 0.3);
        s.addShape(this.pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: cardH,
          fill: { color: th.wash }, line: { color: th.washBorder, width: 1 }, rectRadius: 0.05 });
        let yy = y + 0.17;
        if (it.title) {
          this._sq(s, x + 0.2, yy + 0.05, 0.08, th.warm);
          s.addText(this.runs(it.title, { fontSize: this._fs(T.cardTitle, sc), color: th.primary, bold: true }), {
            x: x + 0.38, y: yy - 0.04, w: cw - 0.56, h: 0.32, margin: 0 });
          yy += textH(it.title, this._fs(T.cardTitle, sc), cw - 0.56) + 0.1;
        }
        if (it.text) s.addText(this.runs(it.text, { fontSize: this._fs(T.cardBody, sc), color: th.ink }), {
          x: x + 0.2, y: yy, w: cw - 0.4, h: cardH - (yy - y) - 0.12, margin: 0,
          valign: "top", lineSpacingMultiple: 1.22 });
      });
    } else if (t === "figure") {
      const { fit, capH } = mz;
      const x = box.x + (box.w - fit.w) / 2;
      if (b.frame !== false) s.addShape(this.pres.shapes.RECTANGLE, {
        x: x - 0.04, y: box.y - 0.04, w: fit.w + 0.08, h: fit.h + 0.08,
        fill: { color: "FFFFFF" }, line: { color: th.line, width: 1 } });
      s.addImage({ path: b.path, x, y: box.y, w: fit.w, h: fit.h });
      if (b.caption) {
        this.figN += 1;
        const cap = `${this.L.fig} ${this.figN}  ${b.caption}` + (b.credit ? `(${b.credit})` : "");
        s.addText(this.runs(cap, { fontSize: T.caption, color: th.muted }), {
          x: box.x, y: box.y + fit.h + 0.1, w: box.w, h: capH, margin: 0, align: "center" });
      }
    } else if (t === "table") {
      // 三线表:顶线/底线粗,栏目线细,无竖线
      const font = this._fs(T.tableBody, sc);
      const header = b.header.map(htxt => ({
        text: this.runs(htxt, {}), options: {
          bold: true, color: th.primary, fill: { color: th.wash }, fontSize: font,
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
        s.addShape(this.pres.shapes.OVAL, { x: x + cw / 2 - 0.26, y: cy - 0.26, w: 0.52, h: 0.52,
          fill: { color: th.accent }, line: { color: "FFFFFF", width: 2 } });
        s.addText([{ text: String(i + 1), options: { fontFace: this.fonts.latin, fontSize: 15, color: "FFFFFF", bold: true } }], {
          x: x + cw / 2 - 0.26, y: cy - 0.26, w: 0.52, h: 0.52, align: "center", valign: "middle", margin: 0 });
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
      const tone = b.tone === "warn" ? { fill: "FCF6E3", border: "E3CE8E", text: "7A5B12", chip: th.warm }
                                     : { fill: th.wash, border: th.washBorder, text: th.primary, chip: th.accent };
      s.addShape(this.pres.shapes.ROUNDED_RECTANGLE, { x: box.x, y: box.y, w: box.w, h: box.h,
        fill: { color: tone.fill }, line: { color: tone.border, width: 1 }, rectRadius: 0.05 });
      let tx = box.x + 0.3;
      if (b.label) {
        const lw = estW(b.label, 12) + 0.3;
        s.addShape(this.pres.shapes.ROUNDED_RECTANGLE, { x: box.x + 0.24, y: box.y + box.h / 2 - 0.16, w: lw, h: 0.32,
          fill: { color: tone.chip }, line: { type: "none" }, rectRadius: 0.16 });
        s.addText(this.runs(b.label, { fontSize: 12, color: "FFFFFF", bold: true }), {
          x: box.x + 0.24, y: box.y + box.h / 2 - 0.16, w: lw, h: 0.32, align: "center", valign: "middle", margin: 0 });
        tx = box.x + 0.24 + lw + 0.22;
      }
      s.addText(this.runs(b.text, { fontSize: this._fs(b.size || T.small, sc), color: tone.text }), {
        x: tx, y: box.y + 0.08, w: box.x + box.w - tx - 0.24, h: box.h - 0.16,
        margin: 0, valign: "middle", lineSpacingMultiple: 1.2 });
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
  _closing(ctx, a) {
    const th = this.theme, s = ctx.slide, m = this.meta;
    if (this.brand.style === "band" && this.brand.seal) {
      return this._bandBase(ctx, {
        main: a.main || this.L.closingMain, mainSize: 34,
        sub: a.sub || m.occasion,
        meta1: m.org || "",
        meta2: [a.contact, m.date].filter(Boolean).join("  ·  "),
        notes: a.notes,
      });
    }
    s.background = { color: th.primary };
    this._sq(s, M, 2.5, 0.13, th.warm);
    s.addText(this.runs(a.main || this.L.closingMain, { fontSize: 34, color: th.onDark, bold: true }), {
      x: M, y: 2.9, w: CW, h: 0.9, margin: 0 });
    if (a.sub) s.addText(this.runs(a.sub, { fontSize: 15, color: th.onDarkSub }), {
      x: M, y: 3.95, w: CW, h: 0.45, margin: 0 });
    s.addShape(this.pres.shapes.RECTANGLE, { x: M, y: 5.5, w: CW, h: 0.012,
      fill: { color: th.onDarkSub }, line: { type: "none" } });
    const meta2 = [m.org, a.contact, m.date].filter(Boolean).join("  ·  ");
    s.addText(this.runs(meta2, { fontSize: 13, color: th.onDarkSub }), {
      x: M, y: 5.7, w: CW, h: 0.36, margin: 0 });
    if (a.notes) s.addNotes(a.notes);
  }
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
