"""命令行入口:python -m paperflow --config paper.yaml [--backend auto] [--workdir DIR]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .backends import BackendError, make_backend
from .graph import build_graph


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="paperflow", description="论文生成流水线(LangGraph 编排)")
    p.add_argument("--config", required=True, help="paper.yaml 配置文件")
    p.add_argument("--backend", default="auto", choices=["auto", "anthropic", "claude-cli", "fixture"])
    p.add_argument("--workdir", default=None, help="工作目录(默认取配置文件所在目录)")
    p.add_argument("--model", default=None, help="覆盖 LLM 模型")
    args = p.parse_args(argv)

    cfg_path = Path(args.config).resolve()
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg["workdir"] = str(Path(args.workdir).resolve() if args.workdir else cfg_path.parent)

    try:
        cfg["_backend"] = make_backend(args.backend, cfg["workdir"], args.model)
    except BackendError as e:
        print(f"后端初始化失败:{e}", file=sys.stderr)
        return 2

    print(f"paperflow 启动 | 后端 {cfg['_backend'].name} | 工作目录 {cfg['workdir']}")
    graph = build_graph()
    try:
        final = graph.invoke({"config": cfg, "log": [], "revision": 0})
    except BackendError as e:
        print(f"流水线失败:{e}", file=sys.stderr)
        return 1

    print("\n".join(final["log"]))
    report = {
        "title": final["outline"].get("title"),
        "qa": final["qa_report"],
        "bibliography": [e["key"] for e in final["bibliography"]],
        "dropped_refs": [
            {"key": d.get("key"), "reason": d.get("reason")} for d in final.get("dropped_refs", [])
        ],
        "outputs": final.get("outputs", []),
        "revisions": final.get("revision", 0),
    }
    report_path = Path(cfg["workdir"]) / "run_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n运行报告:{report_path}")
    for o in final.get("outputs", []):
        print(f"产出:{o}")
    return 0 if final["qa_report"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
