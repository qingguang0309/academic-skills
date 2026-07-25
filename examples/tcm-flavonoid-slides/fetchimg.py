#!/usr/bin/env python3
# ============================================================
# fetchimg.py — 按关键词拉取"真实、可合法使用"的网络配图
#
# 数据源:Openverse API(聚合 Wikimedia Commons / Flickr / 博物馆等
# 开放许可图库),只保留 CC0 / PDM / CC-BY / CC-BY-SA 四种许可。
# 每张图的许可、作者、来源落盘到 credits.json,slidekit 的 figure 块
# 会自动读取并在页面上署名——署名不靠自觉,靠机制。
#
# 用法:
#   python3 fetchimg.py "coal power plant flue gas" -n 4 -o assets/web -t plant
#   → assets/web/plant_1.jpg … plant_4.jpg + assets/web/credits.json
#
# 备注:标准库实现,无第三方依赖;拉不到合规图就明确报告,宁缺毋滥。
# ============================================================
import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request

API = "https://api.openverse.org/v1/images/"
ALLOWED = ["cc0", "pdm", "by", "by-sa"]  # 均可再分发,BY/BY-SA 需署名
UA = {"User-Agent": "paper-slides-fetchimg/1.0 (academic slide deck tooling)"}
LICENSE_LABEL = {"cc0": "CC0", "pdm": "Public Domain", "by": "CC BY", "by-sa": "CC BY-SA"}


def search(query: str, want: int):
    params = urllib.parse.urlencode({
        "q": query,
        "license": ",".join(ALLOWED),
        "page_size": max(want * 5, 20),
        "mature": "false",
    })
    req = urllib.request.Request(f"{API}?{params}", headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    results = data.get("results", [])
    # 过滤:许可白名单 + 有直链;偏好大图(演示投影需要 >= 900px 宽)
    ok = [x for x in results if x.get("license") in ALLOWED and x.get("url")]
    ok.sort(key=lambda x: ((x.get("width") or 0) >= 900, x.get("width") or 0), reverse=True)
    return ok


def normalize(p: pathlib.Path):
    """按真实字节而非 URL 后缀判定格式:pptx 只吃 JPEG/PNG。
    WebP(Openverse 常见的假 .jpg)自动转码;其余未知格式判为失败。"""
    head = p.read_bytes()[:12]
    if head.startswith(b"\xff\xd8") or head.startswith(b"\x89PNG"):
        return p
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        out = p.with_suffix(".conv.jpg")
        try:
            from PIL import Image  # noqa: PLC0415
            Image.open(p).convert("RGB").save(out, quality=90)
        except Exception:  # noqa: BLE001
            if sys.platform == "darwin":
                subprocess.run(["sips", "-s", "format", "jpeg", str(p), "--out", str(out)],
                               capture_output=True)
        if out.exists() and out.stat().st_size > 10_000:
            p.unlink()
            final = p.with_suffix(".jpg")
            out.rename(final)
            print(f"  [convert] WebP → JPEG:{final.name}")
            return final
    print(f"  [skip] 非 JPEG/PNG 且无法转码:{p.name}", file=sys.stderr)
    p.unlink(missing_ok=True)
    return None


def shrink(p: pathlib.Path, limit=5_000_000, width=2000):
    """超大原图缩到演示分辨率:嵌入 pptx 的图不需要 40MB。优先 PIL,macOS 回退 sips。"""
    if p.stat().st_size <= limit:
        return
    try:
        from PIL import Image  # noqa: PLC0415
        im = Image.open(p)
        im.thumbnail((width, width * 3))
        im.save(p, quality=88)
        print(f"  [shrink] {p.name} → {p.stat().st_size // 1024} KB")
        return
    except Exception:  # noqa: BLE001 —— 无 PIL 或格式不支持,试 sips
        pass
    if sys.platform == "darwin":
        subprocess.run(["sips", "--resampleWidth", str(width), str(p)], capture_output=True)
        print(f"  [shrink] {p.name} → {p.stat().st_size // 1024} KB (sips)")
    else:
        print(f"  [warn] {p.name} 超过 5MB 且无法压缩,建议换图或手动缩放", file=sys.stderr)


def clean_creator(raw: str) -> str:
    """Openverse 的 creator 常带多来源前缀:
    'real name: Nadina Wiórkiewicz pl.wiki: Nadine90 commons: Nadine90'。
    署名行放不下这种脏串,取第一个可用姓名并限长。"""
    c = (raw or "unknown").strip()
    m = re.search(r"real name:\s*([^:]+?)(?:\s+\w+\.?\w*\s*:|$)", c)
    if m:
        c = m.group(1).strip()
    else:
        c = re.split(r"\s+(?:pl|en|de|fr|ja|zh)?\.?w?i?k?i?\s*:|\s+commons\s*:", c)[0].strip()
    c = re.sub(r"\s+", " ", c).strip(" ,;|")
    return (c[:28] + "…") if len(c) > 29 else (c or "unknown")


def download(item, dest: pathlib.Path) -> bool:
    url = item["url"]
    ext = pathlib.Path(urllib.parse.urlparse(url).path).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        return False  # slidekit 只吃 PNG/JPEG;SVG/GIF 跳过
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            buf = r.read()
        if len(buf) < 20_000:  # 太小多半是缩略图或占位
            return False
        dest.with_suffix(ext).write_bytes(buf)
        real = normalize(dest.with_suffix(ext))
        if real is None:
            return False
        shrink(real)
        item["_saved"] = real.name
        return True
    except Exception as e:  # noqa: BLE001 —— 单张失败继续下一候选
        print(f"  [skip] 下载失败 {url[:60]}… ({e})", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(description="拉取开放许可的真实配图并登记署名")
    ap.add_argument("query", help="英文关键词效果最好,如 'coal power plant cooling tower'")
    ap.add_argument("-n", type=int, default=3, help="需要的张数(默认 3)")
    ap.add_argument("-o", "--outdir", default="assets/web", help="输出目录")
    ap.add_argument("-t", "--tag", default=None, help="文件名前缀(默认取自关键词)")
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or re.sub(r"[^a-z0-9]+", "_", args.query.lower()).strip("_")[:24]

    try:
        candidates = search(args.query, args.n)
    except Exception as e:  # noqa: BLE001
        print(f"[fetchimg] Openverse 查询失败:{e}\n没有合规图就不要配图——不要退回搜索引擎扒图。", file=sys.stderr)
        sys.exit(1)

    credits_path = outdir / "credits.json"
    credits = json.loads(credits_path.read_text()) if credits_path.exists() else {}

    saved = 0
    for item in candidates:
        if saved >= args.n:
            break
        dest = outdir / f"{tag}_{saved + 1}"
        if not download(item, dest):
            continue
        saved += 1
        name = item["_saved"]
        credits[name] = {
            "title": item.get("title") or "",
            "creator": clean_creator(item.get("creator")),
            "license": LICENSE_LABEL.get(item["license"], item["license"].upper()),
            "license_url": item.get("license_url") or "",
            "source_page": item.get("foreign_landing_url") or item.get("url"),
            "provider": item.get("source") or item.get("provider") or "openverse",
            "query": args.query,
        }
        c = credits[name]
        print(f"  [{name}] {c['license']} | {c['creator'][:30]} | {c['title'][:50]}")

    credits_path.write_text(json.dumps(credits, ensure_ascii=False, indent=2))
    if saved == 0:
        print("[fetchimg] 没有拿到合规图片。换关键词重试,或这一页不配图。", file=sys.stderr)
        sys.exit(2)
    print(f"[fetchimg] 保存 {saved} 张 → {outdir}/,署名已写入 credits.json")


if __name__ == "__main__":
    main()
