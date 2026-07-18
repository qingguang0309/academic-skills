"""LangGraph 编排:plan → literature → verify → figures → draft → assemble → qa,
qa 不通过且未超修订上限时走 revise → assemble → qa 循环。
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
    g.add_node("assemble", nodes.assemble_node)
    g.add_node("qa", nodes.qa_node)
    g.add_node("revise", nodes.revise_node)

    g.add_edge(START, "plan")
    g.add_edge("plan", "literature")
    g.add_edge("literature", "verify")
    g.add_edge("verify", "figures")
    g.add_edge("figures", "draft")
    g.add_edge("draft", "assemble")
    g.add_edge("assemble", "qa")
    g.add_conditional_edges("qa", _route_qa, {"revise": "revise", "done": END, "give_up": END})
    g.add_edge("revise", "assemble")
    return g.compile()
