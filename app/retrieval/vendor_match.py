from difflib import SequenceMatcher
from app.schemas import Invoice

def suggest_vendor(invoice: Invoice, known_vendors: list[str], threshold: float = 0.72) -> dict | None:
    """Baseline lexical vendor match; not embedding-backed RAG."""
    query = invoice.vendor_name.strip().casefold()
    if not query: return None
    matches = [(SequenceMatcher(None, query, name.casefold()).ratio(), name) for name in known_vendors]
    if not matches: return None
    score, name = max(matches)
    return {"vendor_name": name, "similarity": round(score, 3), "suggestion": score >= threshold}
