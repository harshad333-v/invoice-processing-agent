from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from app.schemas import Invoice, ValidationIssue
from app.validators.run import validate_invoice
from app.extraction.extractor import extract_invoice
from app.extraction.preprocess import document_to_image

class State(TypedDict, total=False):
    raw_bytes: bytes
    filename: str
    invoice: Invoice
    issues: list[ValidationIssue]
    attempts: int
    status: str
    raw_model_output: str

def extract_node(state: State) -> dict[str, Any]:
    image_bytes, mime = document_to_image(state["raw_bytes"], state.get("filename", "invoice.png"))
    invoice = extract_invoice(image_bytes, mime)
    return {"invoice": invoice, "attempts": state.get("attempts", 0) + 1, "raw_model_output": invoice.model_dump_json()}

def validate_node(state: State) -> dict[str, Any]:
    issues = validate_invoice(state["invoice"])
    blocking = [i for i in issues if i.severity == "error"]
    return {"issues": issues, "status": "needs_review" if blocking else "ready_for_approval"}

def route_after_validation(state: State) -> str:
    # Do not retry deterministic validation failures automatically: human review is safer
    # unless the extraction itself failed. A future adapter can pass field-specific feedback.
    return "review" if state.get("issues") else "approval"

def review_node(state: State) -> dict[str, Any]: return {"status": "needs_review"}
def approval_node(state: State) -> dict[str, Any]: return {"status": "ready_for_approval"}

def build_graph():
    graph = StateGraph(State)
    graph.add_node("validate", validate_node); graph.add_node("review", review_node); graph.add_node("approval", approval_node)
    graph.set_entry_point("validate")
    graph.add_conditional_edges("validate", route_after_validation, {"review":"review", "approval":"approval"})
    graph.add_edge("review", END); graph.add_edge("approval", END)
    return graph.compile()

def process_invoice(raw_bytes: bytes, filename: str = "invoice.png") -> dict[str, Any]:
    """Run extraction and validation. API failures surface to the UI for a clear message."""
    image_bytes, mime = document_to_image(raw_bytes, filename)
    invoice = extract_invoice(image_bytes, mime)
    issues = validate_invoice(invoice)
    return {"invoice": invoice, "issues": issues, "status": "needs_review" if any(i.severity == "error" for i in issues) else "ready_for_approval", "attempts": 1, "raw_model_output": invoice.model_dump_json()}
