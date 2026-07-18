"""paperflow 状态定义:整条流水线共享一个 PaperState,LangGraph 按节点传递并合并更新。"""
from __future__ import annotations

from typing import Any, TypedDict


class PaperState(TypedDict, total=False):
    config: dict[str, Any]        # paper.yaml 内容 + 运行参数(backend/workdir)
    outline: dict[str, Any]       # plan 节点产出:title/sections[{key,goal}]
    candidate_refs: list[dict]    # literature 节点产出:[{key,title,doi,why}]
    bibliography: list[dict]      # verify 节点产出:通过四库核验的文献(含真实题录)
    dropped_refs: list[dict]      # 核验失败被剔除的候选(防编造的证据)
    sections: dict[str, str]      # draft 节点产出:{section_key: markdown}
    figures: list[dict]           # figures 节点产出:[{path,caption,label}]
    draft_path: str               # assemble 节点产出:paper.md 路径
    outputs: list[str]            # assemble 节点产出:docx/tex 等最终文件
    qa_report: dict[str, Any]     # qa 节点产出:{passed, issues[]}
    revision: int                 # 已执行的修订轮数
    log: list[str]                # 全程日志(附加合并)
