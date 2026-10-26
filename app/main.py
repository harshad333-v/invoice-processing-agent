from fastapi import FastAPI, File, HTTPException, UploadFile
from app.schemas import Invoice
from app.validators.run import validate_invoice
from app.agent.graph import process_invoice

app = FastAPI(title="Invoice Processing Agent", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/validate")
def validate(invoice: Invoice):
    issues = validate_invoice(invoice)
    return {"invoice": invoice.model_dump(mode="json"),
            "issues": [issue.model_dump() for issue in issues],
            "status": "needs_review" if any(issue.severity == "error" for issue in issues) else "ready_for_approval"}

@app.post("/process")
async def process(file: UploadFile = File(...)):
    filename = file.filename or "invoice.png"
    if not filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".webp")):
        raise HTTPException(status_code=415, detail="Upload a PDF or supported image.")
    try:
        result = process_invoice(await file.read(), filename)
        return {"invoice": result["invoice"].model_dump(mode="json"),
                "issues": [issue.model_dump() for issue in result.get("issues", [])],
                "status": result.get("status"), "attempts": result.get("attempts", 1)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Invoice processing failed: {exc}") from exc
