// 最小可运行示例 —— 6 页，覆盖封面 / 目录 / 章节 / 内容页 / 参考文献 / 结束页。
// 目的只有一个：让刚拿到这个 skill 的人在两分钟内看到产物，确认环境是通的。
//
//   npm install            # 在 skill 根目录执行
//   node examples/minimal/deck.js
//
// 真实项目不要照抄本文件的内容纪律——它为了短，故意省掉了实景照片、
// 数据图、致谢页。完整规矩见 ../../SKILL.md。
const { Deck } = require("../../scripts/slidekit.js");

const d = new Deck({
  theme: "claude",            // azure / pine / plum / claude / pku
  lang: "zh",
  kind: "groupmeeting",
  coverStyle: "split",       // groupmeeting 默认走 plate，那个变体要挂刊名 logo 或概念图
  title: "一个最小可运行的\n学术汇报示例",
  subtitle: "用来确认环境通了，不用来当模板",
  shortTitle: "最小示例",
  occasion: "组会汇报",
  presenter: "×××",
  org: "×××实验室",
  date: "2026 年 8 月",
  // 本示例不配实景照片，故显式豁免。真实汇报请去掉这一行，
  // 让 build() 的实景图检查生效——它是这个 skill 的硬门槛之一。
  photos: false,
});

d.cover({ notes: "开场白写在这里，演讲者视图可见。" });
d.toc();

d.section("研究背景", "问题从哪里来", [
  ["现状", "一句话说清当前做法"],
  ["缺口", "一句话说清它解决不了什么"],
  ["本文", "一句话说清你补上了哪一块"],
]);

d.page({
  title: "每页标题写完整结论句，通读标题就是完整论证",
  blocks: [
    { type: "cols", ratio: [1, 1], cols: [
      { blocks: [
        { type: "bullets", size: 15, gap: 0.26, items: [
          { lead: "论断在前：", text: "先给判断，再给证据。读者扫一眼就知道这页要说什么。" },
          { lead: "证据跟上：", text: "数字、图、引用三选一，空口的论断在答辩现场撑不住。" },
          { lead: "条数由内容定：", text: "不要为了版面凑三条——每章三页、每页三条是最容易被认出的 AI 味。" },
        ]},
      ]},
      { blocks: [
        { type: "stats", items: [
          { value: "9", label: "块类型" },
          { value: "5", label: "配色主题" },
          { value: "62%", label: "填充率下限" },
        ]},
        { type: "callout", label: "机制", size: 13.5,
          text: "位置、间距、字阶、页码全部由布局引擎计算。页面太空、标题超行、饼图类别过多都会在 build() 时报警。" },
        { type: "bullets", size: 13, gap: 0.18, items: [
          { lead: "为什么要报警：", text: "写在文档里的规矩会被跳过，写成构建期检查才会被执行。这是本 skill 的基本取向——凡是重要的纪律，都尽量做成会失败的机制。" },
        ]},
      ]},
    ]},
  ],
  source: "块类型与页型细节见 references/layouts.md",
  notes: "讲的时候只念左栏第一句和右栏那个大数字。",
});

d.refs([
  "作者 A. 文献标题[J]. 期刊名, 2024, 12(3): 45-67.",
]);

d.closing({
  takeaway: "环境通了，接下来把内容换成你自己的。",
  contact: "your@email.edu",
});

d.build("minimal.pptx");
