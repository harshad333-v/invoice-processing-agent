from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from app.config import settings
from app.schemas import Invoice, ValidationIssue
from app.validators.run import validate_invoice
from app.extraction.extractor import extract_invoice
from app.extraction.preprocess import document_to_images


class State(TypedDict, total=False):
    raw_bytes: bytes
    filename: str
    image_bytes: bytes | list[tuple[bytes, str]]
    mime_type: str
    invoice: Invoice
    issues: list[ValidationIssue]
    attempts: int
    status: str
    feedback: str
    raw_model_output: str


def extract_node(state: State) -> dict[str, Any]:
    images = state.get("image_bytes")
    mime_type = state.get("mime_type", "image/png")
    if images is None:
        images = document_to_images(state["raw_bytes"], state.get("filename", "invoice.png"))
    invoice = extract_invoice(images, mime_type, state.get("feedback", ""))
    return {"image_bytes": images, "mime_type": mime_type, "invoice": invoice,
            "attempts": state.get("attempts", 0) + 1,
            "raw_model_output": invoice.model_dump_json()}


def validate_node(state: State) -> dict[str, Any]:
    issues = validate_invoice(state["invoice"])
    feedback = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
    blocking = [issue for issue in issues if issue.severity == "error"]
    return {"issues": issues, "feedback": feedback,
            "status": "needs_review" if blocking or issues else "ready_for_approval"}


def route_after_validation(state: State) -> str:
    issues = state.get("issues", [])
    blocking = any(issue.severity == "error" for issue in issues)
    attempts = state.get("attempts", 0)
    if blocking and attempts <= max(0, settings.max_extraction_retries):
        return "retry"
    return "review" if issues else "approval"


def review_node(state: State) -> dict[str, Any]:
    return {"status": "needs_review"}


def approval_node(state: State) -> dict[str, Any]:
    return {"status": "ready_for_approval"}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("extract", extract_node)
    graph.add_node("validate", validate_node)
    graph.add_node("review", review_node)
    graph.add_node("approval", approval_node)
    graph.set_entry_point("extract")
    graph.add_edge("extract", "validate")
    graph.add_conditional_edges("validate", route_after_validation,
        {"retry": "extract", "review": "review", "approval": "approval"})
    graph.add_edge("review", END)
    graph.add_edge("approval", END)
    return graph.compile()


def process_invoice(raw_bytes: bytes, filename: str = "invoice.png") -> dict[str, Any]:
    """Run bounded extraction/validation retries; send all PDF pages in one provider request."""
    pages = document_to_images(raw_bytes, filename)
    result = build_graph().invoke({
        "raw_bytes": raw_bytes, "filename": filename,
        "image_bytes": pages, "mime_type": "image/png", "attempts": 0, "feedback": ""
    })
    result["page_count_processed"] = len(pages)
    return result
