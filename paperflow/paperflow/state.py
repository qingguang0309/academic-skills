"""paperflow 状态定义:整条流水线共享一个 PaperState,LangGraph 按节点传递并合并更新。

log 使用 operator.add reducer:图文两条并行分支会同时写日志,必须可合并;
其余键各分支互斥(literature/verify 写文献,figures 写图),无并发冲突。
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class PaperState(TypedDict, total=False):
    config: dict[str, Any]        # paper.yaml 内容 + 运行参数(backend/workdir/template)
    outline: dict[str, Any]       # plan 节点产出:title/sections[{key,goal}]
    candidate_refs: list[dict]    # literature 节点产出:[{key,title,doi,why}]
    bibliography: list[dict]      # verify 节点产出:通过核验的文献(含真实题录)
    dropped_refs: list[dict]      # 核验失败被剔除的候选(防编造的证据)
    sections: dict[str, str]      # draft 节点产出:{section_key: prose}
    figures: list[dict]           # figures 节点产出:[{path,caption,label}]
    draft_path: str               # render 节点产出:主文档路径(tex/md)
    outputs: list[str]            # render 节点产出:pdf/tex/docx 等最终文件
    qa_report: dict[str, Any]     # qa 节点产出:{passed, issues[]}
    revision: int                 # 已执行的修订轮数
    log: Annotated[list[str], operator.add]   # 全程日志(并行分支可合并追加)
