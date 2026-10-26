from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from app.schemas import Invoice, ValidationIssue
from app.validators.run import validate_invoice

class State(TypedDict, total=False):
    invoice: Invoice
    issues: list[ValidationIssue]
    attempts: int
    status: str

def validate_node(state: State) -> dict[str, Any]:
    invoice = state["invoice"]
    issues = validate_invoice(invoice)
    return {"issues": issues, "status": "needs_review" if issues else "ready_for_approval", "attempts": state.get("attempts", 0)}

def route(state: State) -> str:
    return "review" if state.get("issues") else "approval"

def review_node(state: State) -> dict[str, Any]:
    return {"status": "needs_review"}

def approval_node(state: State) -> dict[str, Any]:
    return {"status": "ready_for_approval"}

def build_graph():
    graph = StateGraph(State)
    graph.add_node("validate", validate_node)
    graph.add_node("review", review_node)
    graph.add_node("approval", approval_node)
    graph.set_entry_point("validate")
    graph.add_conditional_edges("validate", route, {"review":"review", "approval":"approval"})
    graph.add_edge("review", END)
    graph.add_edge("approval", END)
    return graph.compile()
