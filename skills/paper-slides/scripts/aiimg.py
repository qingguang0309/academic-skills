#!/usr/bin/env python3
# ============================================================
# aiimg.py — 调用 DashScope 多模态出图模型生成概念示意图/改图
#
# 通道:原生 multimodal-generation 端点(compatible-mode 的 chat 通道
# 不返回图,已实测)。Key 读取:环境变量 DASHSCOPE_API_KEY,
# 其次 ~/dashscope-tool/key.txt —— key 永远不进仓库。
#
# 用法:
#   python3 aiimg.py "深墨绿金铜配色的 MOF 晶格,CO2 分子入孔,无文字" -o assets/ai/mof.png
#   python3 aiimg.py "把这张图改为横幅构图" --ref assets/ai/mof.png -o assets/ai/mof_wide.png
#
# 机制:
#   - 生成后登记 credits.json(creator=模型, license="AI 生成(示意)"),
#     slidekit figure 块自动落"模型 / AI 生成(示意)"署名——学术诚信不靠自觉
#   - 提示词末尾自动追加"无任何文字标注"(AI 生成文字是最大败点;
#     需要文字标注时用 slidekit/schemfig 后期叠加)
# ============================================================
import argparse
import base64
import json
import mimetypes
import os
import pathlib
import sys
import urllib.request

API = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
T2I_DEFAULT = "qwen-image-2.0-pro"     # 质量优先;求快可 -m z-image-turbo
EDIT_DEFAULT = "qwen-image-edit-max"   # 带参考图时默认切编辑模型
NO_TEXT_SUFFIX = ",无任何文字和标注"


def get_key() -> str:
    k = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if k:
        return k
    p = pathlib.Path.home() / "dashscope-tool" / "key.txt"
    if p.exists():
        return p.read_text().strip()
    print("[aiimg] 未找到 API Key:设 DASHSCOPE_API_KEY 或 ~/dashscope-tool/key.txt", file=sys.stderr)
    sys.exit(1)


def as_image_part(ref: str) -> dict:
    if ref.startswith(("http://", "https://")):
        return {"image": ref}
    p = pathlib.Path(ref)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return {"image": f"data:{mime};base64,{b64}"}


def generate(key: str, model: str, prompt: str, ref: str | None, size: str):
    content: list[dict] = []
    if ref:
        content.append(as_image_part(ref))
    content.append({"text": prompt})
    payload = {
        "model": model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": {"size": size, "n": 1},
    }
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    try:
        for part in data["output"]["choices"][0]["message"]["content"]:
            if "image" in part:
                return part["image"]
    except Exception:  # noqa: BLE001
        pass
    raise RuntimeError(f"模型未返回图片:{json.dumps(data, ensure_ascii=False)[:400]}")


def main():
    ap = argparse.ArgumentParser(description="DashScope 出图(概念示意/改图),自动登记 AI 署名")
    ap.add_argument("prompt", help="画面描述:主体+配色(呼应 deck 主题)+风格词;文字标注不要交给模型")
    ap.add_argument("-o", "--out", required=True, help="输出文件(.png/.jpg)")
    ap.add_argument("-m", "--model", default=None, help=f"默认 {T2I_DEFAULT};带 --ref 时默认 {EDIT_DEFAULT}")
    ap.add_argument("--ref", default=None, help="参考图(本地路径或 URL):触发改图/风格迁移")
    ap.add_argument("--size", default="1664*928", help="尺寸,默认 1664*928(16:9)")
    ap.add_argument("--allow-text", action="store_true", help="不追加'无文字'后缀(默认追加)")
    args = ap.parse_args()

    model = args.model or (EDIT_DEFAULT if args.ref else T2I_DEFAULT)
    prompt = args.prompt if args.allow_text else args.prompt.rstrip(",，。 ") + NO_TEXT_SUFFIX
    key = get_key()

    print(f"[aiimg] {model} 生成中…")
    url = generate(key, model, prompt, args.ref, args.size)

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out)
    if out.stat().st_size < 10_000:
        print("[aiimg] 下载异常(文件过小),请重试", file=sys.stderr)
        sys.exit(1)

    # 登记 AI 署名 → slidekit figure 块自动落"模型 / AI 生成(示意)"
    credits_path = out.parent / "credits.json"
    credits = json.loads(credits_path.read_text()) if credits_path.exists() else {}
    credits[out.name] = {
        "title": args.prompt[:80],
        "creator": model,
        "license": "AI 生成(示意)",
        "provider": "",
        "source_page": "",
        "query": args.prompt,
    }
    credits_path.write_text(json.dumps(credits, ensure_ascii=False, indent=2))
    print(f"[aiimg] 已保存 {out}({out.stat().st_size // 1024} KB),署名已登记。请用 Read 亲眼检查,不满意就改提示词重生成。")


if __name__ == "__main__":
    main()
