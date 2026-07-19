"""LangGraph 编排(图文并行版):

          ┌─ literature → verify ─┐
plan ──┤                          ├─ draft → render → qa ─┬─ END
          └─ figures(按主题生成) ─┘            ↑           └─ revise ─┘
                                               └────────────┘
plan 之后文献链与图表链并行执行,draft 等两条分支都完成后汇合;
qa 不通过且未超修订上限时 revise → render → qa 循环。
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from . import nodes
from .state import PaperState


def _route_qa(state: PaperState) -> str:
    if state["qa_report"]["passed"]:
        return "done"
    if state.get("revision", 0) >= state["config"].get("max_revisions", 2):
        return "give_up"
    return "revise"


def build_graph():
    g = StateGraph(PaperState)
    g.add_node("plan", nodes.plan_node)
    g.add_node("literature", nodes.literature_node)
    g.add_node("verify", nodes.verify_node)
    g.add_node("figures", nodes.figures_node)
    g.add_node("draft", nodes.draft_node)
    g.add_node("render", nodes.render_node)
    g.add_node("qa", nodes.qa_node)
    g.add_node("revise", nodes.revise_node)

    g.add_edge(START, "plan")
    # 并行分支:文献链与图表链同时跑
    g.add_edge("plan", "literature")
    g.add_edge("plan", "figures")
    g.add_edge("literature", "verify")
    # draft 是汇合点:源节点列表 = 屏障,等 verify 与 figures 都完成才执行
    g.add_edge(["verify", "figures"], "draft")
    g.add_edge("draft", "render")
    g.add_edge("render", "qa")
    g.add_conditional_edges("qa", _route_qa, {"revise": "revise", "done": END, "give_up": END})
    g.add_edge("revise", "render")
    return g.compile()
