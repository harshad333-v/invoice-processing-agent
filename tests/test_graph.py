from app.agent.graph import build_graph
from app.schemas import Invoice

def test_graph_routes_invalid_invoice_to_review():
    result = build_graph().invoke({"invoice": Invoice(), "attempts": 0})
    assert result["status"] == "needs_review"
