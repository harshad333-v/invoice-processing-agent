import hashlib
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import ValidationError
from app.schemas import Invoice
from app.validators.run import validate_invoice
from app.agent.risk import score_invoice_risk
from app.agent.graph import process_invoice

app = FastAPI(title="Invoice Processing Agent", version="0.2.0")
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "invoice-processing-agent"}


@app.post("/validate")
def validate(invoice: Invoice):
    issues = validate_invoice(invoice)
    blocking = any(issue.severity == "error" for issue in issues)
    return {"invoice": invoice.model_dump(mode="json"),
            "issues": [issue.model_dump() for issue in issues],
            "risk": score_invoice_risk(invoice, issues),
            "status": "needs_review" if blocking or issues else "ready_for_approval"}


@app.post("/process")
async def process(file: UploadFile = File(...)):
    filename = (file.filename or "invoice.png").replace("\\", "/").split("/")[-1]
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload a PDF or supported image (PNG, JPG, WEBP).")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds the 15 MiB limit.")
    is_pdf = raw.startswith(b"%PDF")
    is_image = raw.startswith(b"\x89PNG\r\n\x1a\n") or raw.startswith(b"\xff\xd8\xff") or (raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")
    if not (is_pdf or is_image):
        raise HTTPException(status_code=415, detail="File contents do not match a supported PDF or image.")
    try:
        result = process_invoice(raw, filename)
        invoice = result["invoice"]
        issues = result.get("issues", [])
        risk = score_invoice_risk(invoice, issues)
        return {"invoice": invoice.model_dump(mode="json"),
                "issues": [issue.model_dump() for issue in issues],
                "risk": risk,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "status": result.get("status"), "attempts": result.get("attempts", 1),\n                "page_count_processed": result.get("page_count_processed", 1)}
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse invoice document: {exc}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Extraction service is not configured or unavailable.") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Invoice processing failed. Check server logs for details.") from exc
