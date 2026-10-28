import app.extraction.extractor as extractor
from app.schemas import Invoice


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": '{"vendor_name":"Vendor","invoice_number":"INV-2","total":"12.50"}'}}]}


def test_extractor_sends_each_page_and_parses_json(monkeypatch):
    monkeypatch.setattr(extractor.settings, "llm_base_url", "https://example.test/v1")
    monkeypatch.setattr(extractor.settings, "llm_api_key", "test-key")
    monkeypatch.setattr(extractor.settings, "llm_model", "vision-test")
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["payload"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr(extractor.requests, "post", fake_post)
    invoice = extractor.extract_invoice([(b"page-one", "image/png"), (b"page-two", "image/png")])
    assert isinstance(invoice, Invoice)
    assert invoice.invoice_number == "INV-2"
    assert captured["url"] == "https://example.test/v1/chat/completions"
    content = captured["payload"]["messages"][1]["content"]
    assert sum(part.get("type") == "image_url" for part in content) == 2
