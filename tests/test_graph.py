from io import BytesIO
from PIL import Image
from app.schemas import Invoice
import app.agent.graph as graph_module

def tiny_png() -> bytes:
    stream = BytesIO()
    Image.new("RGB", (12, 12), "white").save(stream, format="PNG")
    return stream.getvalue()

def test_graph_routes_invalid_invoice_to_review(monkeypatch):
    monkeypatch.setattr(graph_module, "extract_invoice", lambda *_args, **_kwargs: Invoice())
    result = graph_module.process_invoice(tiny_png(), "sample.png")
    assert result["status"] == "needs_review"
    assert result["attempts"] >= 1
    assert result["issues"]
