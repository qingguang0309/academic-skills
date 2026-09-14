#!/usr/bin/env python3
"""从完整版 paper-slides 生成可公开分发的精简版 academic-deck/。

为什么用生成而不是手工复制一份:两份 slidekit.js 一旦并存就会各改各的,
半年后没人说得清哪份是对的。这里让精简版永远从完整版派生,改了完整版重跑即可。

精简掉什么、为什么:
  · pku 主题、内置素材(校徽/地标线描/校园照)及只服务它们的代码路径
    —— 机构专属,不适合公开分发。
  · formula / collage / aiimg / wordlint —— 各自带外部依赖
    (TeX、DashScope),对"我只想快点做出一份好看的汇报"是负担。
  · references/*.md —— 必要的块类型表直接写进精简版 SKILL.md,省掉跳转。

保留 slidekit.js(引擎)与 fetchimg.py(取 CC 许可实景照片)。后者是这套东西
最有价值的机制之一:"必须配真实照片"如果只写在文档里就会被跳过。

每一处删改都带断言,slidekit.js 结构一变就报错,不会静默产出半成品。

    python3 make_lite.py            # → ../../academic-deck/
"""
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent.parent / "academic-deck"

BG_COMMENT = """// ---------- 背景层:素材由作者自带 ----------
// 三个槽位:bgArt(首尾页满版肌理)、bgArtBlock(split 封面色块上的同源肌理)、
// coverMark(色块左上角的单色标识)。淡化要**烘焙进 PNG**,不要靠渲染器的
// 透明度——烘进图里,PowerPoint、LibreOffice、导出的 PDF 看到的才是同一张。
"""

RESOLVE_BRAND = """  // 品牌资源。精简版不含任何内置素材,logo 与 seal 只认显式传入的路径
  // (绝对路径或相对生成脚本);传 false 或不传即关闭,文件不存在则静默跳过。
  //   logo = 横排锁定版,置于正文/章节/目录/参考文献页右上角
  //   seal = 圆形印章,用于 band 式封面居中
  _resolveBrand(opts) {
    const has = p => { try { return p && fs.existsSync(p) ? p : null; } catch (e) { return null; } };
    const kind = KINDS[opts.kind] || KINDS.defense;
    const style = opts.coverStyle || kind.cover;
    const logo = opts.logo === false ? null : has(opts.logo);
    const seal = opts.seal === false ? null : has(opts.seal);
    const logoWhite = opts.logoWhite === false ? null : has(opts.logoWhite);
    const sealWhite = opts.sealWhite === false ? null : has(opts.sealWhite);
    return { logo, seal, logoWhite, sealWhite, style, corner: opts.cornerLogo !== false && !!logo };
  }
"""

DECOR_FNS = """  // 自带底图。等比缩放,不拉伸。精简版只有 bgArt 这一种来源,
  // 不传就静默跳过,首尾页保持纯白。
  _hasDecor(which) { return which === "campus" && !!this.bgArt; }

  _decor(ctx, which, o = {}) {
    if (!this._hasDecor(which)) return;
    const p = this.bgArt;
"""


def strip_institutional(js: str) -> str:
    def cut(pat, why):
        nonlocal js
        m = re.search(pat, js, re.S)
        if not m:
            sys.exit(f"精简失败:{why} —— slidekit.js 结构变了,请更新 make_lite.py")
        js = js[:m.start()] + js[m.end():]

    def swap(pat, new, why):
        nonlocal js
        m = re.search(pat, js, re.S)
        if not m:
            sys.exit(f"精简失败:{why} —— slidekit.js 结构变了,请更新 make_lite.py")
        js = js[:m.start()] + new + js[m.end():]

    # 1) THEMES 里的 pku 条目
    cut(r"\n  pku: \{.*?\n  \},", "找不到 pku 主题块")
    # 2) 背景层注释 + 内置素材表
    swap(r"// ---------- 背景层:直接取自真实汇报的素材 ----------.*?\n\};\n",
         BG_COMMENT, "找不到 DECOR 素材表")
    # 3) _resolveBrand:去掉机构素材的默认路径
    swap(r"  // 品牌资源\(校徽/logo\).*?\n  _resolveBrand\(opts\) \{.*?\n  \}\n",
         RESOLVE_BRAND, "找不到 _resolveBrand")
    # 4) "缺内置素材"的构建期检查:精简版没有内置素材,这条失去意义
    cut(r"    // pku 主题却找不到品牌素材.*?\n    \}\n", "找不到素材缺失检查")
    # 5) _hasDecor / _decor:只剩 bgArt 一种来源
    swap(r"  // 素材背景。等比缩放.*?\n  _decor\(ctx, which, o = \{\}\) \{\n"
         r"    if \(!this\._hasDecor\(which\)\) return;\n    const p = .*?;\n",
         DECOR_FNS, "找不到 _decor")
    # 6) 只服务内置素材的调用点
    pat = r"^\s*this\._decor\(ctx, \"(?:honeycomb|landmarks)\".*\n"
    if not re.search(pat, js, re.M):
        sys.exit("精简失败:找不到 honeycomb/landmarks 调用点")
    js = re.sub(pat, "", js, flags=re.M)
    # 7) plate 留白警告:去掉 landmarks 豁免及其注释
    cut(r"    // pku 主题例外:地标线描已经占住了中段右半幅,不算空。\n",
        "找不到 plate 豁免注释")
    old = 'if (!this._hasDecor("landmarks") &&\n        '
    if js.count(old) != 1:
        sys.exit(f"精简失败:plate 留白警告的 landmarks 豁免命中 {js.count(old)} 次")
    js = js.replace(old, "if (")

    for bad in ("pku", "landmarks", "honeycomb", "DECOR"):
        if bad in js:
            hit = [l.strip() for l in js.splitlines() if bad in l][:3]
            sys.exit(f"精简未净:仍含 {bad!r}\n  " + "\n  ".join(hit))
    return js


def main():
    src = (HERE / "scripts" / "slidekit.js").read_text()
    lite = strip_institutional(src)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "scripts").mkdir(parents=True)
    (OUT / "examples" / "minimal").mkdir(parents=True)

    (OUT / "scripts" / "slidekit.js").write_text(lite)
    shutil.copy2(HERE / "scripts" / "fetchimg.py", OUT / "scripts" / "fetchimg.py")
    for name in ("SKILL.md", "README.md", "package.json"):
        shutil.copy2(HERE / "lite" / name, OUT / name)
    shutil.copy2(HERE / "lite" / "example.js", OUT / "examples" / "minimal" / "deck.js")

    print(f"已生成 {OUT}")
    print(f"  slidekit.js  {len(lite.splitlines())} 行"
          f"(完整版 {len(src.splitlines())} 行)")
    print(f"  主题:azure / pine / plum / claude;机构专属内容零残留")


if __name__ == "__main__":
    main()
