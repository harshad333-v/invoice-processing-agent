from fastapi import FastAPI, HTTPException
from app.schemas import Invoice
from app.validators.run import validate_invoice
from app.agent.graph import build_graph

app = FastAPI(title="Invoice Processing Agent", version="0.1.0")
graph = build_graph()
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/validate")
def validate(invoice: Invoice):
    result = graph.invoke({"invoice":invoice, "attempts":0})
    return {"invoice":invoice.model_dump(mode="json"), "issues":[i.model_dump() for i in result.get("issues",[])], "status":result.get("status")}
