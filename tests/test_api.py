from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
import app.main as api

client = TestClient(api.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_process_rejects_unsupported_extension():
    response = client.post("/process", files={"file": ("invoice.txt", b"hello", "text/plain")})
    assert response.status_code == 415


def test_process_rejects_mismatched_content():
    response = client.post("/process", files={"file": ("invoice.png", b"not an image", "image/png")})
    assert response.status_code == 415


def test_process_returns_structured_result_when_pipeline_succeeds(monkeypatch):
    image = BytesIO()
    Image.new("RGB", (12, 12), "white").save(image, format="PNG")
    from app.schemas import Invoice, ValidationIssue
    monkeypatch.setattr(api, "process_invoice", lambda *_args: {
        "invoice": Invoice(vendor_name="Vendor", invoice_number="INV-1", total="10"),
        "issues": [ValidationIssue(code="gstin", message="GSTIN is missing")],
        "status": "needs_review", "attempts": 1,
    })
    response = client.post("/process", files={"file": ("invoice.png", image.getvalue(), "image/png")})
    assert response.status_code == 200
    body = response.json()
    assert body["invoice"]["invoice_number"] == "INV-1"
    assert body["status"] == "needs_review"
    assert "risk" in body
