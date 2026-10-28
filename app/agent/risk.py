from app.schemas import Invoice, ValidationIssue


def score_invoice_risk(invoice: Invoice, issues: list[ValidationIssue], duplicate_candidates: list[dict] | None = None) -> dict:
    """Deterministic review triage score, not a fraud probability or trained model."""
    score = 0
    reasons: list[str] = []
    for issue in issues:
        score += {"error": 15, "warning": 5}.get(issue.severity, 0)
        reasons.append(f"{issue.code}: {issue.message}")
    if duplicate_candidates:
        score += 40
        reasons.append(f"{len(duplicate_candidates)} exact duplicate candidate(s) found")
    if not invoice.gstin.strip():
        score += 15
        reasons.append("GSTIN is missing")
    if invoice.total <= 0:
        score += 10
        reasons.append("Invoice total is zero or negative")
    score = min(score, 100)
    return {"score": score, "tier": "high" if score >= 60 else "medium" if score >= 25 else "low",
            "reasons": reasons, "is_fraud_probability": False}
