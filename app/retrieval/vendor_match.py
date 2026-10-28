from difflib import SequenceMatcher
from app.schemas import Invoice


def suggest_vendor(invoice: Invoice, known_vendors: list[str], threshold: float = 0.72) -> dict | None:
    """Suggest a different historical vendor name; lexical baseline, not embedding RAG."""
    query = invoice.vendor_name.strip().casefold()
    if not query:
        return None
    candidates = [(SequenceMatcher(None, query, name.casefold()).ratio(), name)
                  for name in known_vendors if name.strip().casefold() != query]
    if not candidates:
        return None
    score, name = max(candidates)
    return {"vendor_name": name, "similarity": round(score, 3), "suggestion": score >= threshold}
